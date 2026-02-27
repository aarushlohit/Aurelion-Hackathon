import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'models/report.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000';

  // ── core ───────────────────────────────────────────────────────────────────

  Future<Report> generateReportFromText(String text) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/process_text'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'text': text}),
        )
        .timeout(const Duration(seconds: 60));
    if (response.statusCode == 200) return Report.fromJson(jsonDecode(response.body));
    throw Exception('process_text failed (${response.statusCode}): ${response.body}');
  }

  Future<Report> generateReportFromAudio(Uint8List audioBytes, String filename) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/process_audio'));
    request.files.add(http.MultipartFile.fromBytes('file', audioBytes, filename: filename));
    final streamed = await request.send().timeout(const Duration(seconds: 120));
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode == 200) return Report.fromJson(jsonDecode(body));
    throw Exception('process_audio failed (${streamed.statusCode}): $body');
  }

  // ── debug echo ─────────────────────────────────────────────────────────────

  /// POST /audio_echo — confirm bytes received by backend.
  Future<Map<String, dynamic>> audioEcho(Uint8List bytes, String filename) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/audio_echo'));
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: filename));
    final streamed = await request.send().timeout(const Duration(seconds: 30));
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode == 200) return jsonDecode(body) as Map<String, dynamic>;
    throw Exception('audio_echo failed (${streamed.statusCode}): $body');
  }

  // ── voice enrollment ───────────────────────────────────────────────────────

  /// POST /enroll_voice_live — enroll with auto gender detection.
  Future<Map<String, dynamic>> enrollVoiceLive({
    required Uint8List audioBytes,
    required String filename,
    required String userName,
    String? gender, // 'male', 'female', or null for auto
  }) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/enroll_voice_live'));
    request.files.add(http.MultipartFile.fromBytes('file', audioBytes, filename: filename));
    request.fields['user_name'] = userName;
    if (gender != null && gender != 'auto') request.fields['gender'] = gender;
    final streamed = await request.send().timeout(const Duration(seconds: 60));
    final body = await streamed.stream.bytesToString();
    if (streamed.statusCode == 200) return jsonDecode(body) as Map<String, dynamic>;
    throw Exception('enroll_voice_live failed (${streamed.statusCode}): $body');
  }

  // ── reports ────────────────────────────────────────────────────────────────

  Future<List<Report>> fetchReports() async {
    final response = await http.get(Uri.parse('$baseUrl/reports')).timeout(const Duration(seconds: 30));
    if (response.statusCode == 200) {
      return (jsonDecode(response.body) as List).map((j) => Report.fromJson(j)).toList();
    }
    throw Exception('fetchReports failed');
  }

  Future<Report> fetchReportDetail(String reportId) async {
    final response = await http.get(Uri.parse('$baseUrl/reports/$reportId')).timeout(const Duration(seconds: 30));
    if (response.statusCode == 200) return Report.fromJson(jsonDecode(response.body));
    throw Exception('Report not found');
  }

  Future<Uint8List> downloadReport(String reportId, String format) async {
    final response = await http
        .get(Uri.parse('$baseUrl/reports/$reportId/download?format=$format'))
        .timeout(const Duration(seconds: 30));
    if (response.statusCode == 200) return response.bodyBytes;
    throw Exception('Export failed');
  }

  Future<Uint8List> exportReportDirect(String reportText, String format) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/export_report'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'report_text': reportText, 'format': format}),
        )
        .timeout(const Duration(seconds: 30));
    if (response.statusCode == 200) return response.bodyBytes;
    throw Exception('Export failed: ${response.body}');
  }

  // ── speak ──────────────────────────────────────────────────────────────────

  /// POST /speak — synthesise report as audio, gender routing on backend.
  Future<Uint8List> speakReport(
    String text, {
    String? userName,
    String mode = 'enterprise',
    String? gender, // 'male', 'female', 'auto', or null → backend default
  }) async {
    final body = <String, dynamic>{
      'text': text,
      'mode': mode,
    };
    if (userName != null && userName.isNotEmpty) body['user_name'] = userName;
    // 'auto' and null both map to no explicit gender (backend uses default)
    if (gender != null && gender != 'auto') body['gender'] = gender;

    final response = await http
        .post(
          Uri.parse('$baseUrl/speak'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 30));

    debugPrint('[Clara/speak] status=${response.statusCode}  '
        'content-type=${response.headers['content-type']}  '
        'content-length=${response.bodyBytes.length}');

    if (response.statusCode == 200) return response.bodyBytes;
    throw Exception('Speak failed (${response.statusCode}): ${response.body}');
  }
}
