class Report {
  final String id;
  final String device;
  final String urgency;
  final DateTime timestamp;
  final String content; // Markdown content
  final double confidence;
  final String? providerUsed;
  final int? transcriptLength;

  Report({
    required this.id,
    required this.device,
    required this.urgency,
    required this.timestamp,
    required this.content,
    this.confidence = 0.0,
    this.providerUsed,
    this.transcriptLength,
  });

  factory Report.fromJson(Map<String, dynamic> json) {
    // Handles both the /reports list format and /reports/{id} detail format
    final intent = json['intent'] as Map<String, dynamic>?;
    return Report(
      id: json['report_id'] ?? json['id'] ?? '',
      device: json['device'] ?? intent?['device'] ?? 'Unknown Device',
      urgency: json['urgency'] ?? intent?['urgency'] ?? 'low',
      timestamp: json['timestamp'] != null
          ? DateTime.tryParse(json['timestamp'].toString()) ?? DateTime.now()
          : DateTime.now(),
      content: json['report_markdown'] ?? json['report_text'] ?? json['content'] ?? '',
      confidence: (json['confidence'] ?? intent?['confidence_score'] ?? 0.0).toDouble(),
      providerUsed: json['provider_used'] as String?,
      transcriptLength: json['transcript_length'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'report_id': id,
      'device': device,
      'urgency': urgency,
      'timestamp': timestamp.toIso8601String(),
      'content': content,
      'confidence': confidence,
    };
  }
}
