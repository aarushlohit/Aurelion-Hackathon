import 'dart:async';
import 'dart:io';
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:record/record.dart';

import '../api_service.dart';
import '../models/report.dart';
import '../providers/app_state.dart';
import '../widgets/glass_card.dart';
import '../widgets/skeleton_loader.dart';
import 'report_detail_screen.dart';

// ─────────────────────────────────────────────────────────────────────────────

enum _InputMode { mic, upload }

// ─────────────────────────────────────────────────────────────────────────────

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  // ── Common ────────────────────────────────────────────────────────────────
  final _textController = TextEditingController();
  _InputMode _inputMode = _InputMode.mic;
  bool _isLoading = false;

  // ── Mic ───────────────────────────────────────────────────────────────────
  final _audioRecorder = AudioRecorder();
  bool _isRecording = false;
  String? _recordingPath;
  Uint8List? _recordedBytes;
  int _recordingSeconds = 0;
  Timer? _recordingTimer;
  String _micStatus = 'idle'; // idle | recording | done | error
  late AnimationController _pulseController;

  // ── Upload ────────────────────────────────────────────────────────────────
  Uint8List? _uploadedBytes;
  String? _uploadedFilename;
  String? _uploadedMime;

  // ── Debug ─────────────────────────────────────────────────────────────────
  Map<String, dynamic>? _echoResult;
  String? _debugProvider;
  int? _debugTranscriptWords;

  // ── Enrollment ────────────────────────────────────────────────────────────
  bool _showEnrollment = false;
  Uint8List? _enrollBytes;
  String? _enrollFilename;
  bool _enrollRecording = false;
  String? _enrollGender; // null = auto
  int _enrollSeconds = 0;
  Timer? _enrollTimer;
  String? _enrollResult;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _textController.dispose();
    _audioRecorder.dispose();
    _pulseController.dispose();
    _recordingTimer?.cancel();
    _enrollTimer?.cancel();
    super.dispose();
  }

  // ── Formatting helpers ────────────────────────────────────────────────────

  String _formatTime(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  String _guessContentType(String filename) {
    final ext = filename.split('.').last.toLowerCase();
    const map = {
      'wav': 'audio/wav',
      'mp3': 'audio/mpeg',
      'mp4': 'audio/mp4',
      'm4a': 'audio/mp4',
      'webm': 'audio/webm',
      'ogg': 'audio/ogg',
      'flac': 'audio/flac',
    };
    return map[ext] ?? 'audio/wav';
  }

  // ── Microphone recording ──────────────────────────────────────────────────

  Future<void> _startRecording() async {
    final hasPerm = await _audioRecorder.hasPermission();
    debugPrint('[Clara/mic] permission=$hasPerm');
    if (!hasPerm) {
      _showSnack('Microphone permission denied. Enable it in system settings.');
      setState(() => _micStatus = 'error');
      return;
    }

    final ts = DateTime.now().millisecondsSinceEpoch;
    final path = kIsWeb ? '' : '/tmp/clara_rec_$ts.wav';

    try {
      await _audioRecorder.start(
        RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 44100,
          bitRate: 128000,
          numChannels: 1,
        ),
        path: path,
      );
      _recordingPath = path;
      _recordingSeconds = 0;
      _recordingTimer = Timer.periodic(const Duration(seconds: 1), (_) {
        setState(() => _recordingSeconds++);
      });
      setState(() {
        _isRecording = true;
        _micStatus = 'recording';
        _recordedBytes = null;
        _echoResult = null;
      });
      debugPrint('[Clara/mic] recording started → $path');
    } catch (e) {
      debugPrint('[Clara/mic] start error: $e');
      _showSnack('Failed to start recording: $e');
      setState(() => _micStatus = 'error');
    }
  }

  Future<void> _stopRecording() async {
    _recordingTimer?.cancel();
    final stoppedPath = await _audioRecorder.stop();
    debugPrint('[Clara/mic] stopped path=$stoppedPath  duration=${_recordingSeconds}s');

    Uint8List bytes;
    if (kIsWeb || stoppedPath == null) {
      _showSnack('Web recording not yet supported in this build.');
      setState(() {
        _isRecording = false;
        _micStatus = 'error';
      });
      return;
    }

    final file = File(stoppedPath);
    if (!await file.exists()) {
      _showSnack('Recording file not found at $stoppedPath');
      setState(() {
        _isRecording = false;
        _micStatus = 'error';
      });
      return;
    }

    bytes = await file.readAsBytes();
    final first12 = bytes.length > 12 ? bytes.sublist(0, 12) : bytes;
    final hexStr = first12.map((b) => b.toRadixString(16).padLeft(2, '0')).join(' ');

    debugPrint('[Clara/mic] file=${stoppedPath}  size=${bytes.length} bytes  first12=$hexStr');

    setState(() {
      _isRecording = false;
      _recordedBytes = bytes;
      _recordingPath = stoppedPath;
      _micStatus = 'done';
    });
  }

  // ── Upload ────────────────────────────────────────────────────────────────

  Future<void> _pickAudioFile() async {
    final result = await FilePicker.platform.pickFiles(type: FileType.audio, withData: true);
    if (result == null || result.files.isEmpty) return;

    final f = result.files.single;
    final bytes = f.bytes ?? Uint8List(0);
    final name = f.name;
    final mime = _guessContentType(name);

    debugPrint('[Clara/upload] file=$name  size=${bytes.length}  mime=$mime');

    setState(() {
      _uploadedBytes = bytes;
      _uploadedFilename = name;
      _uploadedMime = mime;
      _echoResult = null;
    });
  }

  // ── Audio echo + main pipeline ────────────────────────────────────────────

  Future<void> _generateReport() async {
    final hasAudio = _inputMode == _InputMode.mic
        ? _recordedBytes != null
        : _uploadedBytes != null;
    final hasText = _textController.text.trim().isNotEmpty;

    if (!hasAudio && !hasText) {
      _showSnack('Please record audio, upload a file, or type your observations.');
      return;
    }

    setState(() {
      _isLoading = true;
      _echoResult = null;
      _debugProvider = null;
      _debugTranscriptWords = null;
    });

    try {
      final api = ApiService();
      // ── Step 1: audio echo (debug) ──────────────────────────────────────
      if (hasAudio) {
        final bytes = _inputMode == _InputMode.mic ? _recordedBytes! : _uploadedBytes!;
        final filename = _inputMode == _InputMode.mic
            ? 'recording.wav'
            : (_uploadedFilename ?? 'audio.wav');

        try {
          final echo = await api.audioEcho(bytes, filename);
          debugPrint('[Clara/echo] response=$echo');
          final fileSize = echo['file_size'] as int? ?? 0;
          if (fileSize < 1024) {
            _showSnack('⚠️ Mic capture may have failed — file too small ($fileSize bytes). Try again.');
            setState(() => _isLoading = false);
            return;
          }
          setState(() => _echoResult = echo);
        } catch (e) {
          debugPrint('[Clara/echo] error (non-fatal): $e');
          // Don't abort — echo failure is non-critical
        }
      }

      // ── Step 2: pipeline ─────────────────────────────────────────────────
      late final Report report;

      if (hasText && !hasAudio) {
        report = await api.generateReportFromText(_textController.text.trim());
      } else {
        final bytes = _inputMode == _InputMode.mic ? _recordedBytes! : _uploadedBytes!;
        final filename = _inputMode == _InputMode.mic
            ? 'recording.wav'
            : (_uploadedFilename ?? 'audio.wav');

        report = await api.generateReportFromAudio(bytes, filename);

        debugPrint('[Clara/process] provider=${report.providerUsed}  '
            'transcript_words=${report.transcriptLength}');

        if ((report.transcriptLength ?? 0) == 0) {
          _showSnack('⚠️ No speech detected in audio. Try speaking clearly and closer to the mic.');
          setState(() => _isLoading = false);
          return;
        }

        setState(() {
          _debugProvider = report.providerUsed;
          _debugTranscriptWords = report.transcriptLength;
        });
      }

      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => ReportDetailScreen(report: report)),
        );
      }
    } on Exception catch (e) {
      final msg = e.toString();
      if (msg.contains('Connection refused') || msg.contains('SocketException')) {
        _showSnack('Cannot reach backend. Is the server running at localhost:8000?');
      } else {
        _showSnack('Error: $msg');
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  // ── Gender enrollment ─────────────────────────────────────────────────────

  Future<void> _startEnrollRecording() async {
    final hasPerm = await _audioRecorder.hasPermission();
    if (!hasPerm) {
      _showSnack('Microphone permission denied.');
      return;
    }
    final ts = DateTime.now().millisecondsSinceEpoch;
    final path = '/tmp/clara_enroll_$ts.wav';
    await _audioRecorder.start(
      RecordConfig(encoder: AudioEncoder.wav, sampleRate: 44100, numChannels: 1),
      path: path,
    );
    _enrollSeconds = 0;
    _enrollTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      setState(() => _enrollSeconds++);
    });
    setState(() => _enrollRecording = true);
    debugPrint('[Clara/enroll] recording started → $path');
  }

  Future<void> _stopEnrollRecording() async {
    _enrollTimer?.cancel();
    final path = await _audioRecorder.stop();
    if (path == null) return;
    final bytes = await File(path).readAsBytes();
    debugPrint('[Clara/enroll] stopped  size=${bytes.length}  duration=${_enrollSeconds}s');
    setState(() {
      _enrollRecording = false;
      _enrollBytes = bytes;
      _enrollFilename = 'enroll.wav';
    });
  }

  Future<void> _pickEnrollFile() async {
    final result = await FilePicker.platform.pickFiles(type: FileType.audio, withData: true);
    if (result == null || result.files.isEmpty) return;
    final f = result.files.single;
    setState(() {
      _enrollBytes = f.bytes;
      _enrollFilename = f.name;
    });
    debugPrint('[Clara/enroll] file picked: ${f.name}  size=${f.bytes?.length}');
  }

  Future<void> _submitEnrollment() async {
    final appState = Provider.of<AppState>(context, listen: false);
    final userName = appState.userProfile?.name ?? '';
    if (userName.isEmpty) {
      _showSnack('No user name set. Complete onboarding first.');
      return;
    }
    if (_enrollBytes == null) {
      _showSnack('Please record or upload a 30-second voice sample first.');
      return;
    }

    setState(() => _enrollResult = 'Enrolling…');
    try {
      final api = ApiService();
      final result = await api.enrollVoiceLive(
        audioBytes: _enrollBytes!,
        filename: _enrollFilename ?? 'enroll.wav',
        userName: userName,
        gender: _enrollGender,
      );
      final genderDetected = result['gender_detected'] ?? '—';
      final voiceId = result['voice_id'] ?? '—';
      debugPrint('[Clara/enroll] gender_detected=$genderDetected  voice_id=$voiceId');
      setState(() => _enrollResult = '✅ Enrolled! Gender: $genderDetected  |  Voice ID: $voiceId');
    } catch (e) {
      debugPrint('[Clara/enroll] error: $e');
      setState(() => _enrollResult = '❌ Enrollment failed: $e');
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  void _showSnack(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final userName = Provider.of<AppState>(context).userProfile?.name ?? 'User';

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text('Hi, $userName 👋'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: CircleAvatar(
              backgroundColor: theme.primaryColor.withOpacity(0.2),
              child: Icon(Icons.person, color: theme.primaryColor),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 620),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Header
                  Text(
                    'What would you like to report?',
                    style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),

                  // Mode toggle
                  _buildModeToggle(theme),
                  const SizedBox(height: 20),

                  // Input section
                  if (_inputMode == _InputMode.mic)
                    _buildMicSection(theme)
                  else
                    _buildUploadSection(theme),

                  const SizedBox(height: 16),

                  // OR + text
                  _buildTextSection(theme),
                  const SizedBox(height: 16),

                  // Debug strip (after echo)
                  if (_echoResult != null) _buildDebugStrip(theme),
                  if (_echoResult != null) const SizedBox(height: 12),

                  // Generate button
                  if (_isLoading)
                    const SkeletonLoader(width: double.infinity, height: 56)
                  else
                    ElevatedButton.icon(
                      onPressed: _generateReport,
                      icon: const Icon(Icons.auto_awesome),
                      label: const Text(
                        'Generate Report',
                        style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: theme.primaryColor,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                        elevation: 4,
                        shadowColor: theme.primaryColor.withOpacity(0.35),
                      ),
                    ),

                  const SizedBox(height: 32),

                  // Gender Enrollment card
                  _buildEnrollmentCard(theme),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ── Sub-widgets ───────────────────────────────────────────────────────────

  Widget _buildModeToggle(ThemeData theme) {
    return SegmentedButton<_InputMode>(
      segments: const [
        ButtonSegment(value: _InputMode.mic, icon: Icon(Icons.mic), label: Text('Live Mic')),
        ButtonSegment(value: _InputMode.upload, icon: Icon(Icons.upload_file), label: Text('Upload File')),
      ],
      selected: {_inputMode},
      onSelectionChanged: (s) => setState(() {
        _inputMode = s.first;
        _echoResult = null;
      }),
      style: ButtonStyle(
        backgroundColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return theme.primaryColor.withOpacity(0.15);
          return null;
        }),
      ),
    );
  }

  Widget _buildMicSection(ThemeData theme) {
    return GlassCard(
      child: Column(
        children: [
          // Pulsing mic button
          GestureDetector(
            onTap: _isRecording ? _stopRecording : _startRecording,
            child: AnimatedBuilder(
              animation: _pulseController,
              builder: (_, __) => Container(
                height: 120,
                width: 120,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: _isRecording
                      ? Colors.red.withOpacity(0.1 + _pulseController.value * 0.15)
                      : theme.primaryColor.withOpacity(0.1),
                  border: Border.all(
                    color: _isRecording ? Colors.red : theme.primaryColor,
                    width: 2,
                  ),
                  boxShadow: _isRecording
                      ? [BoxShadow(color: Colors.red.withOpacity(0.3), blurRadius: 24 * _pulseController.value, spreadRadius: 8 * _pulseController.value)]
                      : [],
                ),
                child: Icon(
                  _isRecording ? Icons.stop_rounded : Icons.mic_rounded,
                  size: 52,
                  color: _isRecording ? Colors.red : theme.primaryColor,
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Timer / status
          if (_isRecording)
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.fiber_manual_record, color: Colors.red, size: 14),
                const SizedBox(width: 6),
                Text(
                  _formatTime(_recordingSeconds),
                  style: theme.textTheme.titleLarge?.copyWith(
                    color: Colors.red,
                    fontWeight: FontWeight.bold,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
                ),
              ],
            )
          else if (_micStatus == 'done' && _recordedBytes != null)
            _debugChip('✅ Captured: ${_recordedBytes!.length} bytes  •  ${_formatTime(_recordingSeconds)}', Colors.green)
          else
            Text(
              'Tap to start recording',
              style: theme.textTheme.bodyMedium?.copyWith(color: theme.textTheme.bodyMedium?.color?.withOpacity(0.6)),
            ),

          const SizedBox(height: 8),

          // Start/Stop button
          if (!_isRecording && _micStatus != 'done')
            OutlinedButton.icon(
              onPressed: _startRecording,
              icon: const Icon(Icons.mic),
              label: const Text('Start Recording'),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: theme.primaryColor.withOpacity(0.5)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
            )
          else if (_isRecording)
            FilledButton.tonal(
              onPressed: _stopRecording,
              style: FilledButton.styleFrom(backgroundColor: Colors.red.withOpacity(0.15)),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [Icon(Icons.stop, color: Colors.red), SizedBox(width: 6), Text('Stop Recording', style: TextStyle(color: Colors.red))],
              ),
            )
          else
            TextButton.icon(
              onPressed: _startRecording,
              icon: const Icon(Icons.refresh),
              label: const Text('Re-record'),
            ),
        ],
      ),
    );
  }

  Widget _buildUploadSection(ThemeData theme) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          OutlinedButton.icon(
            onPressed: _pickAudioFile,
            icon: const Icon(Icons.upload_file),
            label: Text(_uploadedFilename != null ? 'Change File' : 'Choose Audio File'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 16),
              side: BorderSide(color: theme.primaryColor.withOpacity(0.5)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
          if (_uploadedFilename != null) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                _debugChip('📄 ${_uploadedFilename!}', theme.primaryColor),
                _debugChip('${(_uploadedBytes?.length ?? 0)} bytes', Colors.grey),
                _debugChip(_uploadedMime ?? '?', Colors.blueGrey),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTextSection(ThemeData theme) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Row(
            children: [
              Expanded(child: Divider()),
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 16),
                child: Text('OR TYPE', style: TextStyle(color: Colors.grey, fontSize: 12)),
              ),
              Expanded(child: Divider()),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _textController,
            maxLines: 3,
            decoration: InputDecoration(
              hintText: 'Type your field observations here…',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
              filled: true,
              fillColor: theme.colorScheme.surface.withOpacity(0.5),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDebugStrip(ThemeData theme) {
    final echo = _echoResult!;
    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Backend confirmed receipt', style: theme.textTheme.labelSmall?.copyWith(color: Colors.green, fontWeight: FontWeight.bold)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              _debugChip('📦 ${echo['file_size']} bytes', Colors.green),
              _debugChip('🎙 ${echo['content_type']}', Colors.teal),
              _debugChip('0x ${echo['first_12_bytes_hex']}', Colors.blueGrey),
              if (_debugProvider != null) _debugChip('🤖 ASR: $_debugProvider', Colors.purple),
              if (_debugTranscriptWords != null) _debugChip('📝 $_debugTranscriptWords words', Colors.indigo),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEnrollmentCard(ThemeData theme) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            onTap: () => setState(() => _showEnrollment = !_showEnrollment),
            borderRadius: BorderRadius.circular(12),
            child: Row(
              children: [
                Icon(Icons.record_voice_over, color: theme.primaryColor),
                const SizedBox(width: 10),
                Text('Voice Enrollment', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                const Spacer(),
                Icon(_showEnrollment ? Icons.expand_less : Icons.expand_more),
              ],
            ),
          ),
          if (_showEnrollment) ...[
            const SizedBox(height: 16),
            Text(
              'Record or upload ~30 seconds of your voice.\nThe system auto-detects your gender for voice matching.',
              style: theme.textTheme.bodySmall?.copyWith(color: theme.textTheme.bodySmall?.color?.withOpacity(0.7)),
            ),
            const SizedBox(height: 12),

            // Gender override
            DropdownButtonFormField<String?>(
              value: _enrollGender,
              decoration: InputDecoration(
                labelText: 'Gender (optional — auto if blank)',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                filled: true,
                fillColor: theme.colorScheme.surface.withOpacity(0.5),
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              ),
              items: const [
                DropdownMenuItem(value: null, child: Text('Auto detect')),
                DropdownMenuItem(value: 'female', child: Text('Female')),
                DropdownMenuItem(value: 'male', child: Text('Male')),
              ],
              onChanged: (v) => setState(() => _enrollGender = v),
            ),
            const SizedBox(height: 12),

            // Record 30s
            Row(
              children: [
                Expanded(
                  child: _enrollRecording
                      ? FilledButton.tonal(
                          onPressed: _stopEnrollRecording,
                          style: FilledButton.styleFrom(backgroundColor: Colors.red.withOpacity(0.12)),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.stop, color: Colors.red, size: 18),
                              const SizedBox(width: 6),
                              Text('Stop  ${_formatTime(_enrollSeconds)}', style: const TextStyle(color: Colors.red)),
                            ],
                          ),
                        )
                      : OutlinedButton.icon(
                          onPressed: _startEnrollRecording,
                          icon: const Icon(Icons.mic, size: 18),
                          label: const Text('Record 30s'),
                          style: OutlinedButton.styleFrom(side: BorderSide(color: theme.primaryColor.withOpacity(0.4))),
                        ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _pickEnrollFile,
                    icon: const Icon(Icons.upload_file, size: 18),
                    label: const Text('Upload File'),
                    style: OutlinedButton.styleFrom(side: BorderSide(color: theme.primaryColor.withOpacity(0.4))),
                  ),
                ),
              ],
            ),

            if (_enrollBytes != null) ...[
              const SizedBox(height: 8),
              _debugChip('✅ Ready: ${_enrollFilename ?? "sample"}  (${_enrollBytes!.length} bytes)', Colors.green),
            ],

            const SizedBox(height: 12),

            ElevatedButton(
              onPressed: _enrollBytes != null ? _submitEnrollment : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: theme.primaryColor,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              child: const Text('Enroll Voice'),
            ),

            if (_enrollResult != null) ...[
              const SizedBox(height: 10),
              Text(_enrollResult!, style: theme.textTheme.bodySmall),
            ],
          ],
        ],
      ),
    );
  }

  Widget _debugChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(label, style: TextStyle(fontSize: 11, color: color, fontWeight: FontWeight.w600)),
    );
  }
}


