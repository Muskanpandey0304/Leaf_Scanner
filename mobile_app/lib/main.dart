import 'package:flutter/material.dart';

import 'app_state.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const LeafScannerApp());
}

class LeafScannerApp extends StatelessWidget {
  const LeafScannerApp({super.key});

  @override
  Widget build(BuildContext context) {
    const seed = Color(0xFF2E7D32);
    return MaterialApp(
      title: 'Leaf Scanner',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: seed), useMaterial3: true),
      darkTheme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: seed, brightness: Brightness.dark), useMaterial3: true),
      home: FutureBuilder<AppState>(
        future: AppState.load(),
        builder: (context, snap) {
          if (snap.hasError) {
            return Scaffold(
              body: Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text('Could not start the app:\n${snap.error}', textAlign: TextAlign.center),
                ),
              ),
            );
          }
          if (!snap.hasData) {
            return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          return HomeScreen(state: snap.data!);
        },
      ),
    );
  }
}
