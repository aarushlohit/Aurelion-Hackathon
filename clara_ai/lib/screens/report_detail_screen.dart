import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:intl/intl.dart';
import '../api_service.dart';
import '../models/report.dart';
import '../widgets/glass_card.dart';

class ReportDetailScreen extends StatefulWidget {
  final Report report;

  const ReportDetailScreen({super.key, required this.report});

  @override
  State<ReportDetailScreen> createState() => _ReportDetailScreenState();
}

class _ReportDetailScreenState extends State<ReportDetailScreen> {
  bool _isSpeaking = false;
  bool _isExporting = false;
  final _audioPlayer = AudioPlayer();

  @override
  void dispose() {
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _exportReport(String format) async {
    setState(() => _isExporting = true);
    try {
      final api = ApiService();
      Uint8List data;
      if (widget.report.id.startsWith('CLARA-')) {
        data = await api.downloadReport(widget.report.id, format.toLowerCase());
      } else {
        data = await api.exportReportDirect(widget.report.content, format.toLowerCase());
      }
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Exported as ${format.toUpperCase()} (${data.length} bytes)')),
        );
      }
      // TODO: Save data to file using file_saver or share_plus
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Export failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isExporting = false);
    }
  }

  Future<void> _speakReport() async {
    if (_isSpeaking) {
      await _audioPlayer.stop();
      setState(() => _isSpeaking = false);
      return;
    }

    setState(() => _isSpeaking = true);
    try {
      final api = ApiService();
      // Use the LLM-summarised endpoint: send report_id for persisted reports,
      // fall back to inline report_text for unsaved ones.
      final hasPersistedId = widget.report.id.startsWith('CLARA-');
      final audioBytes = await api.speakReportSummary(
        reportId: hasPersistedId ? widget.report.id : null,
        reportText: hasPersistedId ? null : widget.report.content,
      );
      await _audioPlayer.play(BytesSource(audioBytes));
      _audioPlayer.onPlayerComplete.listen((_) {
        if (mounted) setState(() => _isSpeaking = false);
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Speak failed: $e')),
        );
        setState(() => _isSpeaking = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Details'),
        actions: [
          IconButton(
            icon: Icon(_isSpeaking ? Icons.stop : Icons.volume_up),
            onPressed: _speakReport,
            tooltip: _isSpeaking ? 'Stop' : 'Speak Report',
          ),
          if (_isExporting)
            const Padding(
              padding: EdgeInsets.all(12),
              child: SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2)),
            )
          else
            PopupMenuButton<String>(
              icon: const Icon(Icons.download),
              tooltip: 'Export',
              onSelected: _exportReport,
              itemBuilder: (context) => [
                const PopupMenuItem(value: 'pdf', child: Text('Export as PDF')),
                const PopupMenuItem(value: 'docx', child: Text('Export as DOCX')),
                const PopupMenuItem(value: 'md', child: Text('Export as Markdown')),
              ],
            ),
        ],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              theme.colorScheme.surface,
              theme.primaryColor.withOpacity(0.05),
            ],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 800),
              child: ListView(
                padding: const EdgeInsets.all(24.0),
                children: [
                  GlassCard(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'ID: ${widget.report.id}',
                              style: theme.textTheme.titleSmall?.copyWith(
                                color: theme.textTheme.titleSmall?.color?.withOpacity(0.6),
                              ),
                            ),
                            Text(
                              DateFormat('MMM d, yyyy HH:mm').format(widget.report.timestamp),
                              style: theme.textTheme.titleSmall?.copyWith(
                                color: theme.textTheme.titleSmall?.color?.withOpacity(0.6),
                              ),
                            ),
                          ],
                        ),
                        const Divider(height: 32),
                        MarkdownBody(
                          data: widget.report.content,
                          selectable: true,
                          styleSheet: MarkdownStyleSheet(
                            h1: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold, color: theme.primaryColor),
                            h2: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                            h3: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                            p: theme.textTheme.bodyLarge?.copyWith(height: 1.6),
                            listBullet: theme.textTheme.bodyLarge,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}


