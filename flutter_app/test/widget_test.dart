import 'package:flutter_test/flutter_test.dart';
import 'package:nexurance_app/main.dart';

void main() {
  testWidgets('App launches', (WidgetTester tester) async {
    await tester.pumpWidget(const NexuranceApp());
    expect(find.text('NEXURANCE'), findsOneWidget);
  });
}
