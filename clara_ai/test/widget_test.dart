import 'package:flutter_test/flutter_test.dart';
import 'package:clara_ai/main.dart';
import 'package:provider/provider.dart';
import 'package:clara_ai/providers/app_state.dart';

void main() {
  testWidgets('App loads smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      ChangeNotifierProvider(
        create: (_) => AppState(),
        child: const ClaraApp(),
      ),
    );
    expect(find.byType(ClaraApp), findsOneWidget);
  });
}
