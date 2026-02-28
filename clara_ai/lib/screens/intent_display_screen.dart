import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../widgets/glass_card.dart';

class IntentDisplayScreen extends StatelessWidget {
  const IntentDisplayScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final pipelineJson = context.watch<AppState>().lastPipelineJson;

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: const Text('Intent Display'),
        actions: [
          if (pipelineJson != null)
            IconButton(
              icon: const Icon(Icons.copy),
              tooltip: 'Copy JSON',
              onPressed: () {
                final pretty = const JsonEncoder.withIndent('  ').convert(pipelineJson);
                Clipboard.setData(ClipboardData(text: pretty));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('JSON copied to clipboard')),
                );
              },
            ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 800),
            child: pipelineJson == null
                ? _buildEmptyState(theme)
                : _buildJsonView(theme, pipelineJson),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState(ThemeData theme) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.data_object, size: 72, color: theme.primaryColor.withOpacity(0.3)),
        const SizedBox(height: 16),
        Text(
          'No intent data yet',
          style: theme.textTheme.titleMedium?.copyWith(
            color: theme.textTheme.titleMedium?.color?.withOpacity(0.5),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Generate a report from the Home tab to see\nthe full intent analysis in JSON.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.textTheme.bodyMedium?.color?.withOpacity(0.4),
          ),
        ),
      ],
    );
  }

  Widget _buildJsonView(ThemeData theme, Map<String, dynamic> json) {
    // Extract sub-sections for the tabbed view
    final intentJson = json['intent'] as Map<String, dynamic>? ?? {};
    final codeswitchJson = json['codeswitch_analysis'] as Map<String, dynamic>? ?? {};
    final fullJson = json;

    return DefaultTabController(
      length: 3,
      child: Column(
        children: [
          // Summary chips
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: _buildSummaryChips(theme, intentJson),
          ),
          const SizedBox(height: 12),
          // Tab bar
          TabBar(
            labelColor: theme.primaryColor,
            unselectedLabelColor: theme.textTheme.bodyMedium?.color?.withOpacity(0.5),
            indicatorColor: theme.primaryColor,
            tabs: const [
              Tab(icon: Icon(Icons.psychology, size: 20), text: 'Intent'),
              Tab(icon: Icon(Icons.translate, size: 20), text: 'Code-Switch'),
              Tab(icon: Icon(Icons.data_object, size: 20), text: 'Full Response'),
            ],
          ),
          const SizedBox(height: 8),
          // Tab views
          Expanded(
            child: TabBarView(
              children: [
                _buildJsonSection(theme, intentJson),
                _buildJsonSection(theme, codeswitchJson),
                _buildJsonSection(theme, fullJson),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryChips(ThemeData theme, Map<String, dynamic> intent) {
    final urgency = (intent['urgency'] ?? '').toString();
    final confidence = intent['confidence_score'];
    final device = (intent['device'] ?? '').toString();
    final symptom = (intent['symptom'] ?? '').toString();

    Color urgencyColor;
    switch (urgency) {
      case 'high':
        urgencyColor = Colors.red;
        break;
      case 'medium':
        urgencyColor = Colors.orange;
        break;
      default:
        urgencyColor = Colors.green;
    }

    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          if (urgency.isNotEmpty)
            _chip('⚡ $urgency', urgencyColor),
          if (confidence != null)
            _chip('🎯 ${(confidence * 100).toStringAsFixed(0)}%', Colors.blue),
          if (device.isNotEmpty)
            _chip('📱 $device', Colors.teal),
          if (symptom.isNotEmpty)
            _chip('🔍 $symptom', Colors.purple),
        ],
      ),
    );
  }

  Widget _chip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600),
      ),
    );
  }

  Widget _buildJsonSection(ThemeData theme, Map<String, dynamic> json) {
    if (json.isEmpty) {
      return Center(
        child: Text(
          'No data available',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: theme.textTheme.bodyMedium?.color?.withOpacity(0.4),
          ),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      children: [
        // Pretty-printed JSON card
        GlassCard(
          padding: const EdgeInsets.all(16),
          child: SelectableText(
            const JsonEncoder.withIndent('  ').convert(json),
            style: TextStyle(
              fontFamily: 'monospace',
              fontSize: 13,
              height: 1.5,
              color: theme.textTheme.bodyMedium?.color,
            ),
          ),
        ),
        const SizedBox(height: 16),
        // Key-value breakdown
        ...json.entries.map((e) => _buildKeyValueTile(theme, e.key, e.value)),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildKeyValueTile(ThemeData theme, String key, dynamic value) {
    final isNested = value is Map || value is List;
    final displayValue = isNested
        ? const JsonEncoder.withIndent('  ').convert(value)
        : value.toString();

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: GlassCard(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              key,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: theme.primaryColor,
                letterSpacing: 0.5,
              ),
            ),
            const SizedBox(height: 4),
            SelectableText(
              displayValue,
              style: TextStyle(
                fontFamily: isNested ? 'monospace' : null,
                fontSize: isNested ? 12 : 14,
                height: 1.4,
                color: theme.textTheme.bodyMedium?.color?.withOpacity(0.85),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
