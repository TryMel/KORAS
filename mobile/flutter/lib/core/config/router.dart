import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../features/conversation/screens/conversation_screen.dart';
import '../../features/history/screens/history_screen.dart';
import '../../features/settings/screens/settings_screen.dart';
import '../../features/onboarding/screens/onboarding_screen.dart';
import '../../features/onboarding/screens/auth_screen.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/onboarding',
  routes: [
    GoRoute(
      path: '/onboarding',
      builder: (context, state) => const OnboardingScreen(),
    ),
    GoRoute(path: '/auth', builder: (context, state) => const AuthScreen()),
    ShellRoute(
      builder: (context, state, child) => KorasShell(child: child),
      routes: [
        GoRoute(
          path: '/home',
          builder: (context, state) => const ConversationScreen(),
        ),
        GoRoute(
          path: '/history',
          builder: (context, state) => const HistoryScreen(),
        ),
        GoRoute(
          path: '/settings',
          builder: (context, state) => const SettingsScreen(),
        ),
      ],
    ),
  ],
);

/// Bottom navigation shell wrapping authenticated screens
class KorasShell extends StatelessWidget {
  final Widget child;
  const KorasShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      body: child,
      bottomNavigationBar: _KorasBottomNav(),
    );
  }
}

class _KorasBottomNav extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.toString();

    return Semantics(
      label: 'Navigation principale',
      child: Container(
        decoration: const BoxDecoration(
          color: Color(0xFF1A1A2E),
          border: Border(top: BorderSide(color: Colors.white12)),
        ),
        child: BottomNavigationBar(
          backgroundColor: Colors.transparent,
          selectedItemColor: const Color(0xFF6C63FF),
          unselectedItemColor: Colors.white38,
          elevation: 0,
          currentIndex: _indexFor(location),
          onTap: (i) {
            switch (i) {
              case 0: context.go('/home'); break;
              case 1: context.go('/history'); break;
              case 2: context.go('/settings'); break;
            }
          },
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.mic_rounded),
              label: 'KORAS',
              tooltip: 'Assistant vocal',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.history_rounded),
              label: 'Historique',
              tooltip: 'Historique des actions',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.settings_rounded),
              label: 'Paramètres',
              tooltip: 'Paramètres et accessibilité',
            ),
          ],
        ),
      ),
    );
  }

  int _indexFor(String location) {
    if (location.startsWith('/history')) return 1;
    if (location.startsWith('/settings')) return 2;
    return 0;
  }
}
