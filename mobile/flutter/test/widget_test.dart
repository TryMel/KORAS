import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:koras_mobile/main.dart';

void main() {
  testWidgets('KORAS app launches smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: KorasApp()));
    await tester.pumpAndSettle();
    expect(find.textContaining('KORAS'), findsWidgets);
  });
}
