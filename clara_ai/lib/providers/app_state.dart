import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_profile.dart';

class AppState extends ChangeNotifier {
  bool _isDarkMode = false;
  UserProfile? _userProfile;
  bool _isFirstLaunch = true;
  Map<String, dynamic>? _lastPipelineJson;

  bool get isDarkMode => _isDarkMode;
  UserProfile? get userProfile => _userProfile;
  bool get isFirstLaunch => _isFirstLaunch;
  Map<String, dynamic>? get lastPipelineJson => _lastPipelineJson;

  void setLastPipelineJson(Map<String, dynamic> json) {
    _lastPipelineJson = json;
    notifyListeners();
  }

  AppState() {
    _loadPreferences();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    _isDarkMode = prefs.getBool('isDarkMode') ?? false;
    
    final userProfileJson = prefs.getString('userProfile');
    if (userProfileJson != null) {
      _userProfile = UserProfile.fromJson(jsonDecode(userProfileJson));
      _isFirstLaunch = false;
    } else {
      _isFirstLaunch = true;
    }
    notifyListeners();
  }

  Future<void> toggleTheme() async {
    _isDarkMode = !_isDarkMode;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isDarkMode', _isDarkMode);
    notifyListeners();
  }

  Future<void> saveUserProfile(UserProfile profile) async {
    _userProfile = profile;
    _isFirstLaunch = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('userProfile', jsonEncode(profile.toJson()));
    notifyListeners();
  }

  Future<void> clearData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.clear();
    _userProfile = null;
    _isFirstLaunch = true;
    _isDarkMode = false;
    notifyListeners();
  }
}
