class UserProfile {
  final String name;
  final String organization;
  final String role;
  final String preferredLanguage; // 'en', 'de', 'ta', 'ml'

  UserProfile({
    required this.name,
    required this.organization,
    required this.role,
    this.preferredLanguage = 'en',
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      name: json['name'] ?? '',
      organization: json['organization'] ?? '',
      role: json['role'] ?? '',
      preferredLanguage: json['preferredLanguage'] ?? 'en',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'organization': organization,
      'role': role,
      'preferredLanguage': preferredLanguage,
    };
  }
}
