import 'package:flutter/material.dart';
import '../../../domain/repositories/conversation_repository.dart';

/// Displays persisted API history; no sample actions are shown as real data.
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});
  @override State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  late Future<List<Map<String, dynamic>>> _history;
  @override void initState() { super.initState(); _history = ConversationRepository().list(); }
  @override Widget build(BuildContext context) => Scaffold(
    backgroundColor: const Color(0xFF0D0D0D),
    appBar: AppBar(backgroundColor: const Color(0xFF1A1A2E), title: const Text('Historique')),
    body: FutureBuilder<List<Map<String, dynamic>>>(
      future: _history,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError) return Center(child: Text('Historique indisponible', style: TextStyle(color: Colors.white70)));
        final items = snapshot.data ?? [];
        if (items.isEmpty) return const Center(child: Text('Aucune action enregistrée.', style: TextStyle(color: Colors.white70)));
        return RefreshIndicator(onRefresh: () async => setState(() => _history = ConversationRepository().list()), child: ListView.separated(
          padding: const EdgeInsets.all(16), itemCount: items.length, separatorBuilder: (_, __) => const SizedBox(height: 8),
          itemBuilder: (_, index) { final item = items[index]; return ListTile(
            tileColor: const Color(0xFF1A1A2E), leading: const Icon(Icons.history, color: Color(0xFF6C63FF)),
            title: Text(item['title']?.toString() ?? 'Conversation', style: const TextStyle(color: Colors.white)),
            subtitle: Text(item['updated_at']?.toString() ?? '', style: const TextStyle(color: Colors.white54)),
          ); },
        ));
      },
    ),
  );
}
