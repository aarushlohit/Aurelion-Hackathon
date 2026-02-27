import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';

void main() {
  runApp(const ClaraApp());
}

// ─────────────────────────────────────────────
// Mock Data Scenarios
// ─────────────────────────────────────────────
class MockScenario {
  final String title;
  final String location;
  final String transcript;
  final String language;
  final Map<String, int> langMix;
  final String intent;
  final String device;
  final String symptom;
  final String component;
  final double confidence;
  final String severity;
  final Color severityColor;
  final String reportSummary;
  final String technician;
  final String ticketId;

  const MockScenario({
    required this.title,
    required this.location,
    required this.transcript,
    required this.language,
    required this.langMix,
    required this.intent,
    required this.device,
    required this.symptom,
    required this.component,
    required this.confidence,
    required this.severity,
    required this.severityColor,
    required this.reportSummary,
    required this.technician,
    required this.ticketId,
  });
}

const List<MockScenario> kScenarios = [
  MockScenario(
    title: 'Motor Pump Diagnostics',
    location: 'Site A – Coimbatore Plant',
    transcript:
        '"Indha motor pump-la noise adhikama irukku, capacitor check pannanuma?"',
    language: 'Tamil + English',
    langMix: {'Tamil': 68, 'English': 32},
    intent: 'diagnose_equipment_issue',
    device: 'motor pump',
    symptom: 'excessive noise',
    component: 'capacitor',
    confidence: 0.87,
    severity: 'Medium',
    severityColor: Color(0xFFFFB74D),
    reportSummary:
        'The motor pump unit at Site A is producing abnormal excessive noise during operation. A detailed inspection of the start capacitor and run capacitor is strongly recommended. Technician should check for capacitor bulging, leakage, or capacitance drift before resuming operations.',
    technician: 'Arjun S.',
    ticketId: 'TKT-2024-0041',
  ),
  MockScenario(
    title: 'Transformer Overheating',
    location: 'Site B – Tirupur Substation',
    transcript:
        '"Transformer romba heat aaguthu, oil level okay-a irukku, but temperature gauge high showing pannuthu."',
    language: 'Tamil + English',
    langMix: {'Tamil': 72, 'English': 28},
    intent: 'thermal_fault_detection',
    device: 'distribution transformer',
    symptom: 'overheating / high temperature',
    component: 'cooling fins & oil level sensor',
    confidence: 0.91,
    severity: 'High',
    severityColor: Color(0xFFEF5350),
    reportSummary:
        'The distribution transformer at Site B is exhibiting critical overheating conditions. The temperature gauge readings are above safe operating thresholds. While oil levels appear nominal, the cooling fin assembly and oil level sensor must be inspected immediately. Operations should be halted until clearance is obtained.',
    technician: 'Kavitha R.',
    ticketId: 'TKT-2024-0045',
  ),
  MockScenario(
    title: 'Inverter Charging Failure',
    location: 'Site C – Salem Warehouse',
    transcript:
        '"Inverter battery charge aagala, mains supply irukku but charging indicator light illai."',
    language: 'Tamil + English',
    langMix: {'Tamil': 65, 'English': 35},
    intent: 'power_system_fault',
    device: 'inverter / UPS unit',
    symptom: 'battery not charging',
    component: 'charging circuit / indicator LED',
    confidence: 0.83,
    severity: 'Low',
    severityColor: Color(0xFF66BB6A),
    reportSummary:
        'The inverter unit at Site C is not initiating battery charging despite mains supply being present. No charging indicator light is visible. The charging circuit board and LED indicator module require inspection. A blown fuse in the charging pathway is a likely root cause.',
    technician: 'Murugan P.',
    ticketId: 'TKT-2024-0049',
  ),
  MockScenario(
    title: 'Electrical Wiring Fault',
    location: 'Site D – Madurai Factory',
    transcript:
        '"Panel-la oru wire loose-a irukku, antha connection sparking pannuthu, MCB trip aaguthu."',
    language: 'Tamil + English',
    langMix: {'Tamil': 74, 'English': 26},
    intent: 'electrical_safety_hazard',
    device: 'MCC panel',
    symptom: 'loose wiring, sparking, MCB trip',
    component: 'terminal block / MCB',
    confidence: 0.94,
    severity: 'Critical',
    severityColor: Color(0xFFFF1744),
    reportSummary:
        'A critical electrical hazard has been identified at the MCC panel in Site D. A loose wire is causing visible sparking at the terminal block, resulting in repeated MCB trips. Immediate isolation of the affected circuit is mandatory. A certified electrician must re-terminate the connection and verify torque compliance before re-energisation.',
    technician: 'Senthil K.',
    ticketId: 'TKT-2024-0053',
  ),
];

// ─────────────────────────────────────────────
// Simulation State
// ─────────────────────────────────────────────
enum SimStage { idle, recording, processing, transcribed, extracted, reported }

const List<String> kProcessingLogs = [
  'Initialising multilingual ASR engine...',
  'Audio stream segmented — 4.2s captured',
  'Language detection: Tamil 68%, English 32%',
  'Tokenising code-switched utterance...',
  'Running NLP hybrid intent classifier v2.1...',
  'Cross-lingual embedding computed',
  'Slot-filling: device, symptom, component',
  'Intent confidence score: 0.87',
  'Structured JSON payload generated',
  'Pipeline complete — ready for report generation',
];

// ─────────────────────────────────────────────
// App Root
// ─────────────────────────────────────────────
class ClaraApp extends StatelessWidget {
  const ClaraApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Clara AI – Vernacular Navigator',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF5C6BC0),
          brightness: Brightness.dark,
          surface: const Color(0xFF0B0D1A),
          primary: const Color(0xFF7986CB),
          secondary: const Color(0xFF9575CD),
          tertiary: const Color(0xFF4FC3F7),
          onSurface: const Color(0xFFE8EAF6),
        ),
        scaffoldBackgroundColor: const Color(0xFF0B0D1A),
        cardTheme: CardThemeData(
          color: const Color(0xFF111326),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFF1E2140), width: 1),
          ),
          margin: EdgeInsets.zero,
        ),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(
            fontSize: 15,
            height: 1.65,
            color: Color(0xFFCFD8DC),
          ),
          bodyMedium: TextStyle(fontSize: 13, color: Color(0xFF78909C)),
          labelLarge: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            letterSpacing: 1,
          ),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0B0D1A),
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          scrolledUnderElevation: 0,
        ),
        dividerColor: const Color(0xFF1E2140),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF4C5EC4),
            foregroundColor: Colors.white,
            elevation: 0,
            minimumSize: const Size(double.infinity, 54),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.4,
            ),
          ),
        ),
      ),
      home: const HomeScreen(),
    );
  }
}

// ─────────────────────────────────────────────
// Home Screen – stateful simulation controller
// ─────────────────────────────────────────────
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  SimStage _stage = SimStage.idle;
  int _scenarioIndex = 0;
  final List<String> _logs = [];
  int _logIndex = 0;
  Timer? _recordTimer;
  Timer? _logTimer;
  late AnimationController _waveController;
  late AnimationController _pulseController;
  final ScrollController _scrollController = ScrollController();

  MockScenario get _current => kScenarios[_scenarioIndex];

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _recordTimer?.cancel();
    _logTimer?.cancel();
    _waveController.dispose();
    _pulseController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _onMicTap() {
    if (_stage == SimStage.idle || _stage == SimStage.reported) {
      _startRecording();
    } else if (_stage == SimStage.recording) {
      _stopAndProcess();
    }
  }

  void _startRecording() {
    setState(() {
      _stage = SimStage.recording;
      _logs.clear();
      _logIndex = 0;
    });
    _recordTimer = Timer(const Duration(milliseconds: 3500), _stopAndProcess);
  }

  void _stopAndProcess() {
    _recordTimer?.cancel();
    setState(() => _stage = SimStage.processing);
    _logs.clear();
    _logIndex = 0;
    _runProcessingLogs();
  }

  void _runProcessingLogs() {
    _logTimer = Timer.periodic(const Duration(milliseconds: 420), (t) {
      if (_logIndex < kProcessingLogs.length) {
        setState(() => _logs.add(kProcessingLogs[_logIndex++]));
        _scrollToBottom();
      } else {
        t.cancel();
        Future.delayed(const Duration(milliseconds: 600), () {
          setState(() => _stage = SimStage.transcribed);
          Future.delayed(const Duration(milliseconds: 900), () {
            setState(() => _stage = SimStage.extracted);
          });
        });
      }
    });
  }

  void _generateReport() {
    setState(() => _stage = SimStage.reported);
    _scenarioIndex = (_scenarioIndex + 1) % kScenarios.length;
  }

  void _reset() {
    setState(() {
      _stage = SimStage.idle;
      _logs.clear();
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  bool get _showTranscript =>
      _stage == SimStage.transcribed ||
      _stage == SimStage.extracted ||
      _stage == SimStage.reported;

  bool get _showIntent =>
      _stage == SimStage.extracted || _stage == SimStage.reported;
  bool get _showReport => _stage == SimStage.reported;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: LayoutBuilder(
        builder: (context, constraints) {
          final maxW = constraints.maxWidth > 860
              ? 860.0
              : constraints.maxWidth;
          return Center(
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: maxW),
              child: CustomScrollView(
                controller: _scrollController,
                slivers: [
                  _buildSliverAppBar(),
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(18, 0, 18, 40),
                    sliver: SliverList(
                      delegate: SliverChildListDelegate([
                        const SizedBox(height: 8),
                        _StatsRow(stage: _stage),
                        const SizedBox(height: 20),
                        _ScenarioSelector(
                          current: _scenarioIndex,
                          total: kScenarios.length,
                          onNext:
                              _stage == SimStage.idle ||
                                  _stage == SimStage.reported
                              ? () => setState(() {
                                  _scenarioIndex =
                                      (_scenarioIndex + 1) % kScenarios.length;
                                  _stage = SimStage.idle;
                                })
                              : null,
                          scenarioTitle: _current.title,
                          location: _current.location,
                        ),
                        const SizedBox(height: 20),
                        _VoicePanel(
                          stage: _stage,
                          waveController: _waveController,
                          pulseController: _pulseController,
                          onMicTap: _onMicTap,
                          onReset: _stage != SimStage.idle ? _reset : null,
                        ),
                        const SizedBox(height: 20),
                        if (_stage == SimStage.processing) ...[
                          _ProcessingLogCard(logs: _logs),
                          const SizedBox(height: 20),
                        ],
                        _AnimatedReveal(
                          visible: _showTranscript,
                          child: Column(
                            children: [
                              _TranscriptCard(scenario: _current),
                              const SizedBox(height: 20),
                            ],
                          ),
                        ),
                        _AnimatedReveal(
                          visible: _showIntent,
                          child: Column(
                            children: [
                              _IntentCard(scenario: _current),
                              const SizedBox(height: 20),
                            ],
                          ),
                        ),
                        if (_showIntent && !_showReport)
                          _GenerateReportButton(onPressed: _generateReport),
                        _AnimatedReveal(
                          visible: _showReport,
                          child: Column(
                            children: [
                              const SizedBox(height: 20),
                              _ReportCard(scenario: _current),
                              const SizedBox(height: 20),
                              _ActionBar(onReset: _reset),
                            ],
                          ),
                        ),
                        if (_stage == SimStage.idle) ...[
                          const SizedBox(height: 20),
                          const _RecentCallsCard(),
                        ],
                      ]),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  SliverAppBar _buildSliverAppBar() {
    final colors = Theme.of(context).colorScheme;
    return SliverAppBar(
      pinned: true,
      backgroundColor: const Color(0xFF0B0D1A),
      surfaceTintColor: Colors.transparent,
      expandedHeight: 110,
      collapsedHeight: 64,
      flexibleSpace: FlexibleSpaceBar(
        collapseMode: CollapseMode.pin,
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF0F1230), Color(0xFF0B0D1A)],
            ),
          ),
        ),
        titlePadding: const EdgeInsets.fromLTRB(18, 0, 18, 14),
        title: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF5C6BC0), Color(0xFF7B1FA2)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(9),
              ),
              child: const Icon(
                Icons.graphic_eq_rounded,
                color: Colors.white,
                size: 18,
              ),
            ),
            const SizedBox(width: 10),
            Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Clara AI',
                  style: TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFFE8EAF6),
                    letterSpacing: 0.3,
                  ),
                ),
                Text(
                  'Vernacular Navigator',
                  style: TextStyle(
                    fontSize: 9.5,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 1.8,
                    color: colors.tertiary,
                  ),
                ),
              ],
            ),
            const Spacer(),
            _StatusPill(stage: _stage),
          ],
        ),
      ),
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(height: 1, color: const Color(0xFF1E2140)),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Status Pill
// ─────────────────────────────────────────────
class _StatusPill extends StatelessWidget {
  final SimStage stage;
  const _StatusPill({required this.stage});

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (stage) {
      SimStage.idle => ('READY', const Color(0xFF66BB6A)),
      SimStage.recording => ('RECORDING', const Color(0xFFEF5350)),
      SimStage.processing => ('PROCESSING', const Color(0xFFFFB74D)),
      SimStage.transcribed => ('TRANSCRIBED', const Color(0xFF4FC3F7)),
      SimStage.extracted => ('INTENT EXTRACTED', const Color(0xFF9575CD)),
      SimStage.reported => ('REPORT READY', const Color(0xFF66BB6A)),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        border: Border.all(color: color.withOpacity(0.35)),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 6,
            height: 6,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.1,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Stats Row
// ─────────────────────────────────────────────
class _StatsRow extends StatelessWidget {
  final SimStage stage;
  const _StatsRow({required this.stage});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _StatChip(
          value: '1,247',
          label: 'Sessions',
          icon: Icons.mic_rounded,
          color: const Color(0xFF7986CB),
        ),
        const SizedBox(width: 10),
        _StatChip(
          value: '91.4%',
          label: 'Avg Accuracy',
          icon: Icons.verified_rounded,
          color: const Color(0xFF66BB6A),
        ),
        const SizedBox(width: 10),
        _StatChip(
          value: '12',
          label: 'Languages',
          icon: Icons.language_rounded,
          color: const Color(0xFF4FC3F7),
        ),
      ],
    );
  }
}

class _StatChip extends StatelessWidget {
  final String value;
  final String label;
  final IconData icon;
  final Color color;
  const _StatChip({
    required this.value,
    required this.label,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 14),
        decoration: BoxDecoration(
          color: const Color(0xFF111326),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF1E2140)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 16, color: color),
            const SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                color: color,
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: const TextStyle(
                fontSize: 10,
                color: Color(0xFF546E7A),
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Scenario Selector
// ─────────────────────────────────────────────
class _ScenarioSelector extends StatelessWidget {
  final int current;
  final int total;
  final String scenarioTitle;
  final String location;
  final VoidCallback? onNext;

  const _ScenarioSelector({
    required this.current,
    required this.total,
    required this.scenarioTitle,
    required this.location,
    required this.onNext,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      decoration: BoxDecoration(
        color: const Color(0xFF111326),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF1E2140)),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  colors.primary.withOpacity(0.3),
                  colors.secondary.withOpacity(0.3),
                ],
              ),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              Icons.folder_special_rounded,
              color: colors.primary,
              size: 20,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  scenarioTitle,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFFE8EAF6),
                  ),
                ),
                const SizedBox(height: 3),
                Row(
                  children: [
                    Icon(
                      Icons.location_on_outlined,
                      size: 12,
                      color: colors.tertiary,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      location,
                      style: TextStyle(
                        fontSize: 11,
                        color: colors.tertiary.withOpacity(0.8),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${current + 1}/$total',
                style: const TextStyle(
                  fontSize: 11,
                  color: Color(0xFF546E7A),
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              if (onNext != null)
                GestureDetector(
                  onTap: onNext,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: colors.primary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(
                        color: colors.primary.withOpacity(0.25),
                      ),
                    ),
                    child: Text(
                      'Next Scenario',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w700,
                        color: colors.primary,
                      ),
                    ),
                  ),
                )
              else
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1E2140),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: const Text(
                    'Locked',
                    style: TextStyle(fontSize: 10, color: Color(0xFF546E7A)),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Voice Panel with animated waveform
// ─────────────────────────────────────────────
class _VoicePanel extends StatelessWidget {
  final SimStage stage;
  final AnimationController waveController;
  final AnimationController pulseController;
  final VoidCallback onMicTap;
  final VoidCallback? onReset;

  const _VoicePanel({
    required this.stage,
    required this.waveController,
    required this.pulseController,
    required this.onMicTap,
    required this.onReset,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final isRecording = stage == SimStage.recording;
    final isProcessing = stage == SimStage.processing;

    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 32, 24, 28),
        child: Column(
          children: [
            Row(
              children: [
                _SectionLabel(label: 'VOICE INPUT', color: colors.tertiary),
                const Spacer(),
                if (onReset != null)
                  GestureDetector(
                    onTap: onReset,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 5,
                      ),
                      decoration: BoxDecoration(
                        color: const Color(0xFF1E2140),
                        borderRadius: BorderRadius.circular(7),
                      ),
                      child: const Text(
                        'Reset',
                        style: TextStyle(
                          fontSize: 11,
                          color: Color(0xFF78909C),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 28),
            if (isRecording) _WaveformVisualizer(controller: waveController),
            if (!isRecording) const SizedBox(height: 8),
            const SizedBox(height: 20),
            _MicButton(
              stage: stage,
              controller: pulseController,
              onTap: onMicTap,
            ),
            const SizedBox(height: 22),
            Text(
              isProcessing
                  ? 'Analysing multilingual speech...'
                  : isRecording
                  ? 'Recording — tap again to stop'
                  : stage == SimStage.idle
                  ? 'Tap to Record Mixed-Language Speech'
                  : 'Pipeline complete',
              style: TextStyle(
                fontSize: 13,
                color: isRecording
                    ? colors.error.withOpacity(0.9)
                    : isProcessing
                    ? const Color(0xFFFFB74D)
                    : const Color(0xFF546E7A),
                letterSpacing: 0.2,
                fontWeight: FontWeight.w500,
              ),
              textAlign: TextAlign.center,
            ),
            if (isRecording) ...[
              const SizedBox(height: 14),
              _PipelineSteps(active: 0),
            ],
            if (isProcessing) ...[
              const SizedBox(height: 14),
              _PipelineSteps(active: 1),
            ],
          ],
        ),
      ),
    );
  }
}

class _WaveformVisualizer extends StatefulWidget {
  final AnimationController controller;
  const _WaveformVisualizer({required this.controller});

  @override
  State<_WaveformVisualizer> createState() => _WaveformVisualizerState();
}

class _WaveformVisualizerState extends State<_WaveformVisualizer> {
  final List<double> _seeds = List.generate(30, (i) => Random().nextDouble());

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        return SizedBox(
          height: 52,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: List.generate(30, (i) {
              final t = widget.controller.value;
              final height =
                  6.0 +
                  (_seeds[i] * 40.0) *
                      (0.4 + 0.6 * (sin((t * 2 * pi) + (i * 0.4))).abs());
              final alpha = 0.45 + 0.55 * (_seeds[i]);
              return Container(
                width: 3,
                height: height.clamp(4.0, 48.0),
                margin: const EdgeInsets.symmetric(horizontal: 1.5),
                decoration: BoxDecoration(
                  color: const Color(0xFFEF5350).withOpacity(alpha),
                  borderRadius: BorderRadius.circular(2),
                ),
              );
            }),
          ),
        );
      },
    );
  }
}

class _MicButton extends StatelessWidget {
  final SimStage stage;
  final AnimationController controller;
  final VoidCallback onTap;

  const _MicButton({
    required this.stage,
    required this.controller,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final isRecording = stage == SimStage.recording;
    final isProcessing = stage == SimStage.processing;
    final isDone = stage == SimStage.reported;

    final ringColor = isRecording
        ? colors.error
        : isProcessing
        ? const Color(0xFFFFB74D)
        : isDone
        ? const Color(0xFF66BB6A)
        : colors.primary;

    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final pulse = isRecording ? (1.0 + controller.value * 0.15) : 1.0;
        return GestureDetector(
          onTap: onTap,
          child: Transform.scale(
            scale: pulse,
            child: Stack(
              alignment: Alignment.center,
              children: [
                if (isRecording)
                  Container(
                    width: 116,
                    height: 116,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: ringColor.withOpacity(
                        0.08 * (1 - controller.value),
                      ),
                    ),
                  ),
                Container(
                  width: 96,
                  height: 96,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        ringColor.withOpacity(0.18),
                        ringColor.withOpacity(0.06),
                      ],
                    ),
                    border: Border.all(color: ringColor, width: 2),
                    boxShadow: [
                      BoxShadow(
                        color: ringColor.withOpacity(0.35),
                        blurRadius: 24,
                        spreadRadius: 1,
                      ),
                    ],
                  ),
                  child: Icon(
                    isRecording
                        ? Icons.stop_rounded
                        : isProcessing
                        ? Icons.hourglass_top_rounded
                        : isDone
                        ? Icons.check_rounded
                        : Icons.mic_none_rounded,
                    size: 38,
                    color: ringColor,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _PipelineSteps extends StatelessWidget {
  final int active;
  const _PipelineSteps({required this.active});

  static const steps = ['Record', 'Analyse', 'Extract', 'Report'];
  static const stepColors = [
    Color(0xFFEF5350),
    Color(0xFFFFB74D),
    Color(0xFF9575CD),
    Color(0xFF66BB6A),
  ];

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: List.generate(steps.length, (i) {
        final done = i < active;
        final cur = i == active;
        final c = stepColors[i];
        return Row(
          children: [
            Column(
              children: [
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: done || cur
                        ? c.withOpacity(0.15)
                        : const Color(0xFF1E2140),
                    border: Border.all(
                      color: done || cur ? c : const Color(0xFF2E3460),
                      width: 1.5,
                    ),
                  ),
                  child: Icon(
                    done ? Icons.check_rounded : Icons.circle,
                    size: done ? 14 : 7,
                    color: done || cur ? c : const Color(0xFF2E3460),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  steps[i],
                  style: TextStyle(
                    fontSize: 9,
                    color: done || cur ? c : const Color(0xFF2E3460),
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
            if (i < steps.length - 1)
              Container(
                width: 28,
                height: 1.5,
                margin: const EdgeInsets.only(bottom: 20),
                color: const Color(0xFF1E2140),
              ),
          ],
        );
      }),
    );
  }
}

// ─────────────────────────────────────────────
// Processing Log Card
// ─────────────────────────────────────────────
class _ProcessingLogCard extends StatelessWidget {
  final List<String> logs;
  const _ProcessingLogCard({required this.logs});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _SectionLabel(
                  label: 'NLP PIPELINE',
                  color: const Color(0xFFFFB74D),
                ),
                const Spacer(),
                const SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Color(0xFFFFB74D),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF060810),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF1E2140)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (int i = 0; i < logs.length; i++)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '[${(i + 1).toString().padLeft(2, '0')}] ',
                            style: const TextStyle(
                              fontFamily: 'monospace',
                              fontSize: 11,
                              color: Color(0xFF546E7A),
                            ),
                          ),
                          Expanded(
                            child: Text(
                              logs[i],
                              style: TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 11,
                                height: 1.5,
                                color: i == logs.length - 1
                                    ? const Color(0xFFFFB74D)
                                    : const Color(0xFF4FC3F7),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  if (logs.length < kProcessingLogs.length)
                    const Text(
                      '_',
                      style: TextStyle(
                        fontFamily: 'monospace',
                        fontSize: 12,
                        color: Color(0xFF4FC3F7),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Animated reveal wrapper
// ─────────────────────────────────────────────
class _AnimatedReveal extends StatefulWidget {
  final bool visible;
  final Widget child;
  const _AnimatedReveal({required this.visible, required this.child});

  @override
  State<_AnimatedReveal> createState() => _AnimatedRevealState();
}

class _AnimatedRevealState extends State<_AnimatedReveal>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _fade;
  late final Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _fade = CurvedAnimation(parent: _ctrl, curve: Curves.easeOut);
    _slide = Tween<Offset>(
      begin: const Offset(0, 0.06),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic));
    if (widget.visible) _ctrl.value = 1.0;
  }

  @override
  void didUpdateWidget(_AnimatedReveal old) {
    super.didUpdateWidget(old);
    if (widget.visible && !old.visible) _ctrl.forward();
    if (!widget.visible && old.visible) _ctrl.reverse();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fade,
      child: SlideTransition(position: _slide, child: widget.child),
    );
  }
}

// ─────────────────────────────────────────────
// Transcript Card
// ─────────────────────────────────────────────
class _TranscriptCard extends StatelessWidget {
  final MockScenario scenario;
  const _TranscriptCard({required this.scenario});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _SectionLabel(label: 'TRANSCRIPT', color: colors.secondary),
                const Spacer(),
                _Tag(label: 'ASR', color: const Color(0xFF546E7A)),
              ],
            ),
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF080A14),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF1E2140)),
              ),
              child: Text(
                scenario.transcript,
                style: const TextStyle(
                  fontSize: 15,
                  fontStyle: FontStyle.italic,
                  color: Color(0xFFE0E0E0),
                  height: 1.7,
                ),
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                _Tag(label: scenario.language, color: colors.secondary),
                const SizedBox(width: 8),
                _Tag(label: 'Code-Switched', color: colors.tertiary),
              ],
            ),
            const SizedBox(height: 14),
            _LangMixBar(mix: scenario.langMix),
          ],
        ),
      ),
    );
  }
}

class _LangMixBar extends StatelessWidget {
  final Map<String, int> mix;
  const _LangMixBar({required this.mix});

  @override
  Widget build(BuildContext context) {
    final entries = mix.entries.toList();
    const c1 = Color(0xFF9575CD);
    const c2 = Color(0xFF4FC3F7);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              entries[0].key,
              style: const TextStyle(
                fontSize: 10,
                color: c1,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.8,
              ),
            ),
            Text(
              entries[1].key,
              style: const TextStyle(
                fontSize: 10,
                color: c2,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.8,
              ),
            ),
          ],
        ),
        const SizedBox(height: 5),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: Row(
            children: [
              Expanded(
                flex: entries[0].value,
                child: Container(height: 6, color: c1),
              ),
              Expanded(
                flex: entries[1].value,
                child: Container(height: 6, color: c2),
              ),
            ],
          ),
        ),
        const SizedBox(height: 4),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '${entries[0].value}%',
              style: const TextStyle(fontSize: 10, color: Color(0xFF546E7A)),
            ),
            Text(
              '${entries[1].value}%',
              style: const TextStyle(fontSize: 10, color: Color(0xFF546E7A)),
            ),
          ],
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────
// Intent Card
// ─────────────────────────────────────────────
class _IntentCard extends StatelessWidget {
  final MockScenario scenario;
  const _IntentCard({required this.scenario});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final s = scenario;

    final json =
        '''{
  "intent": "${s.intent}",
  "device": "${s.device}",
  "symptom": "${s.symptom}",
  "suspected_component": "${s.component}",
  "confidence": ${s.confidence.toStringAsFixed(2)},
  "severity": "${s.severity.toLowerCase()}",
  "ticket_id": "${s.ticketId}"
}''';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _SectionLabel(
                  label: 'HYBRID INTENT EXTRACTION',
                  color: colors.primary,
                ),
                const Spacer(),
                _SeverityBadge(label: s.severity, color: s.severityColor),
              ],
            ),
            const SizedBox(height: 14),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF060810),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF1E2140)),
              ),
              child: _SyntaxHighlightedJson(json: json),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                _ConfidenceBar(value: s.confidence, color: colors.primary),
              ],
            ),
            const SizedBox(height: 14),
            _IntentSlots(scenario: s),
          ],
        ),
      ),
    );
  }
}

class _SeverityBadge extends StatelessWidget {
  final String label;
  final Color color;
  const _SeverityBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 5,
            height: 5,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 5),
          Text(
            label.toUpperCase(),
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.8,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

class _IntentSlots extends StatelessWidget {
  final MockScenario scenario;
  const _IntentSlots({required this.scenario});

  @override
  Widget build(BuildContext context) {
    final items = [
      (scenario.device, Icons.memory_rounded, 'Device'),
      (scenario.symptom, Icons.warning_amber_rounded, 'Symptom'),
      (scenario.component, Icons.settings_rounded, 'Component'),
    ];
    return Row(
      children: items
          .map(
            (t) => Expanded(
              child: Container(
                margin: const EdgeInsets.only(right: 8),
                padding: const EdgeInsets.all(11),
                decoration: BoxDecoration(
                  color: const Color(0xFF0D0F1E),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF1E2140)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(t.$2, size: 14, color: const Color(0xFF546E7A)),
                    const SizedBox(height: 6),
                    Text(
                      t.$3,
                      style: const TextStyle(
                        fontSize: 9,
                        letterSpacing: 0.8,
                        color: Color(0xFF546E7A),
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      t.$1,
                      maxLines: 2,
                      style: const TextStyle(
                        fontSize: 11,
                        color: Color(0xFFCFD8DC),
                        fontWeight: FontWeight.w600,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          )
          .toList(),
    );
  }
}

class _SyntaxHighlightedJson extends StatelessWidget {
  final String json;
  const _SyntaxHighlightedJson({required this.json});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: json.split('\n').map(_buildLine).toList(),
    );
  }

  Widget _buildLine(String line) {
    final m = RegExp(r'^(\s*)"([^"]+)"(\s*:\s*)(.*)$').firstMatch(line);
    if (m != null) {
      final value = m.group(4)!;
      Color vc = const Color(0xFF80CBC4);
      if (RegExp(r'^\d').hasMatch(value)) vc = const Color(0xFFFFCC80);
      if (value.startsWith('"')) vc = const Color(0xFFA5D6A7);
      return RichText(
        text: TextSpan(
          style: const TextStyle(
            fontFamily: 'monospace',
            fontSize: 12.5,
            height: 1.9,
          ),
          children: [
            TextSpan(
              text: m.group(1)!,
              style: const TextStyle(color: Color(0xFF37474F)),
            ),
            TextSpan(
              text: '"${m.group(2)!}"',
              style: const TextStyle(color: Color(0xFF82AAFF)),
            ),
            TextSpan(
              text: m.group(3)!,
              style: const TextStyle(color: Color(0xFF546E7A)),
            ),
            TextSpan(
              text: value,
              style: TextStyle(color: vc),
            ),
          ],
        ),
      );
    }
    return Text(
      line,
      style: const TextStyle(
        fontFamily: 'monospace',
        fontSize: 12.5,
        height: 1.9,
        color: Color(0xFF546E7A),
      ),
    );
  }
}

class _ConfidenceBar extends StatelessWidget {
  final double value;
  final Color color;
  const _ConfidenceBar({required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'CONFIDENCE SCORE',
                style: TextStyle(
                  fontSize: 10,
                  letterSpacing: 1.2,
                  fontWeight: FontWeight.w600,
                  color: color.withOpacity(0.7),
                ),
              ),
              Text(
                '${(value * 100).toStringAsFixed(0)}%',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 7),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: value,
              minHeight: 6,
              backgroundColor: color.withOpacity(0.10),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Generate Report Button
// ─────────────────────────────────────────────
class _GenerateReportButton extends StatelessWidget {
  final VoidCallback onPressed;
  const _GenerateReportButton({required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            color: Color(0x554C5EC4),
            blurRadius: 20,
            offset: Offset(0, 6),
          ),
        ],
      ),
      child: ElevatedButton.icon(
        onPressed: onPressed,
        icon: const Icon(Icons.description_outlined, size: 18),
        label: const Text('GENERATE FORMAL REPORT'),
      ),
    );
  }
}

// ─────────────────────────────────────────────
// Report Card
// ─────────────────────────────────────────────
class _ReportCard extends StatelessWidget {
  final MockScenario scenario;
  const _ReportCard({required this.scenario});

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;
    final s = scenario;

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF2E4040), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _SectionLabel(
                  label: 'FORMAL SERVICE REPORT',
                  color: const Color(0xFF66BB6A),
                ),
                const Spacer(),
                _Tag(label: s.ticketId, color: const Color(0xFF66BB6A)),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Auto-generated from voice input  •  27/02/2026  14:32 IST',
              style: TextStyle(fontSize: 11, color: Color(0xFF546E7A)),
            ),
            const SizedBox(height: 18),
            _HrDivider(),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _MetaCell(
                    label: 'Technician',
                    value: s.technician,
                    icon: Icons.person_outline_rounded,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _MetaCell(
                    label: 'Site',
                    value: s.location,
                    icon: Icons.location_on_outlined,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _MetaCell(
                    label: 'Severity',
                    value: s.severity,
                    icon: Icons.priority_high_rounded,
                    valueColor: s.severityColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _HrDivider(),
            const SizedBox(height: 16),
            _ReportRow(
              label: 'Equipment',
              value: _cap(s.device),
              color: colors.primary,
            ),
            const SizedBox(height: 12),
            _ReportRow(
              label: 'Issue Observed',
              value: _cap(s.symptom),
              color: colors.secondary,
            ),
            const SizedBox(height: 12),
            _ReportRow(
              label: 'Suspected Component',
              value: _cap(s.component),
              color: colors.tertiary,
            ),
            const SizedBox(height: 16),
            _HrDivider(),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0C18),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF1E3020)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 4,
                        height: 16,
                        decoration: BoxDecoration(
                          color: const Color(0xFF66BB6A),
                          borderRadius: BorderRadius.circular(2),
                        ),
                      ),
                      const SizedBox(width: 10),
                      const Text(
                        'DETAILED SUMMARY',
                        style: TextStyle(
                          fontSize: 10,
                          letterSpacing: 1.5,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF66BB6A),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    s.reportSummary,
                    style: const TextStyle(
                      fontSize: 14,
                      height: 1.75,
                      color: Color(0xFFCFD8DC),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _cap(String s) => s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);
}

class _MetaCell extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color? valueColor;

  const _MetaCell({
    required this.label,
    required this.value,
    required this.icon,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0D0F1E),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF1E2140)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 14, color: const Color(0xFF546E7A)),
          const SizedBox(height: 6),
          Text(
            label,
            style: const TextStyle(
              fontSize: 9,
              letterSpacing: 0.8,
              color: Color(0xFF546E7A),
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            value,
            maxLines: 2,
            style: TextStyle(
              fontSize: 11,
              color: valueColor ?? const Color(0xFFCFD8DC),
              fontWeight: FontWeight.w700,
              height: 1.3,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionBar extends StatelessWidget {
  final VoidCallback onReset;
  const _ActionBar({required this.onReset});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: onReset,
            icon: const Icon(Icons.replay_rounded, size: 16),
            label: const Text('NEW QUERY'),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: Color(0xFF2E3460)),
              foregroundColor: const Color(0xFF7986CB),
              minimumSize: const Size(0, 50),
              textStyle: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                letterSpacing: 1,
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.ios_share_rounded, size: 16),
            label: const Text('EXPORT PDF'),
            style: ElevatedButton.styleFrom(
              minimumSize: const Size(0, 50),
              backgroundColor: const Color(0xFF1B3A2A),
              foregroundColor: const Color(0xFF66BB6A),
              textStyle: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w700,
                letterSpacing: 1,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────
// Recent Calls (idle state)
// ─────────────────────────────────────────────
class _RecentCallsCard extends StatelessWidget {
  const _RecentCallsCard();

  static const _history = [
    (
      'TKT-2024-0040',
      'Fan belt slipping on lathe motor',
      'High',
      Color(0xFFEF5350),
      '2h ago',
    ),
    (
      'TKT-2024-0038',
      'Control panel fuse blown repeatedly',
      'Medium',
      Color(0xFFFFB74D),
      '5h ago',
    ),
    (
      'TKT-2024-0035',
      'Generator output voltage fluctuation',
      'Low',
      Color(0xFF66BB6A),
      'Yesterday',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SectionLabel(
              label: 'RECENT QUERIES',
              color: const Color(0xFF546E7A),
            ),
            const SizedBox(height: 14),
            for (int i = 0; i < _history.length; i++) ...[
              if (i != 0)
                Container(
                  height: 1,
                  margin: const EdgeInsets.symmetric(vertical: 10),
                  color: const Color(0xFF1E2140),
                ),
              _HistoryRow(
                ticketId: _history[i].$1,
                description: _history[i].$2,
                severity: _history[i].$3,
                severityColor: _history[i].$4,
                time: _history[i].$5,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _HistoryRow extends StatelessWidget {
  final String ticketId;
  final String description;
  final String severity;
  final Color severityColor;
  final String time;

  const _HistoryRow({
    required this.ticketId,
    required this.description,
    required this.severity,
    required this.severityColor,
    required this.time,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: severityColor.withOpacity(0.08),
            borderRadius: BorderRadius.circular(9),
            border: Border.all(color: severityColor.withOpacity(0.2)),
          ),
          child: Icon(
            Icons.receipt_long_rounded,
            size: 16,
            color: severityColor,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    ticketId,
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF546E7A),
                    ),
                  ),
                  const SizedBox(width: 8),
                  _SeverityBadge(label: severity, color: severityColor),
                ],
              ),
              const SizedBox(height: 3),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFFB0BEC5),
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Text(
          time,
          style: const TextStyle(fontSize: 11, color: Color(0xFF37474F)),
        ),
      ],
    );
  }
}

class _ReportRow extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _ReportRow({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 3,
          height: 34,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label.toUpperCase(),
                style: TextStyle(
                  fontSize: 9.5,
                  letterSpacing: 1.2,
                  fontWeight: FontWeight.w700,
                  color: color.withOpacity(0.7),
                ),
              ),
              const SizedBox(height: 3),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 14,
                  color: Color(0xFFCFD8DC),
                  height: 1.4,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────
// Shared Widgets
// ─────────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final String label;
  final Color color;
  const _SectionLabel({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 3,
          height: 13,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 9),
        Text(
          label,
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.6,
            color: color,
          ),
        ),
      ],
    );
  }
}

class _Tag extends StatelessWidget {
  final String label;
  final Color color;
  const _Tag({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.09),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withOpacity(0.22)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10.5,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.2,
          color: color,
        ),
      ),
    );
  }
}

class _HrDivider extends StatelessWidget {
  @override
  Widget build(BuildContext context) =>
      Container(height: 1, color: const Color(0xFF1E2140));
}
