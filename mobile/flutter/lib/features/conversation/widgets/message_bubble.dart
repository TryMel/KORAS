import 'package:flutter/material.dart';
import '../providers/conversation_provider.dart';

class MessageBubble extends StatelessWidget {
  final ChatMessage message;

  const MessageBubble({super.key, required this.message});

  bool get _isUser => message.role == 'user';

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: _isUser ? 'Vous avez dit: ${message.content}' : 'KORAS a dit: ${message.content}',
      child: Align(
        alignment: _isUser ? Alignment.centerRight : Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 6),
          constraints: BoxConstraints(
            maxWidth: MediaQuery.of(context).size.width * 0.78,
          ),
          decoration: BoxDecoration(
            color: _isUser ? const Color(0xFF6C63FF) : const Color(0xFF1E1E2E),
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(20),
              topRight: const Radius.circular(20),
              bottomLeft: _isUser ? const Radius.circular(20) : const Radius.circular(4),
              bottomRight: _isUser ? const Radius.circular(4) : const Radius.circular(20),
            ),
            border: _isUser ? null : Border.all(color: Colors.white12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!_isUser)
                const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircleAvatar(
                      radius: 10,
                      backgroundColor: Color(0xFF6C63FF),
                      child: Text('K', style: TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold)),
                    ),
                    SizedBox(width: 6),
                    Text('KORAS', style: TextStyle(color: Color(0xFF6C63FF), fontSize: 11, fontWeight: FontWeight.bold)),
                  ],
                ),
              if (!_isUser) const SizedBox(height: 6),
              Text(
                message.content,
                style: TextStyle(
                  color: _isUser ? Colors.white : Colors.white,
                  fontSize: 16,
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                _formatTime(message.createdAt),
                style: const TextStyle(color: Colors.white38, fontSize: 11),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatTime(DateTime dt) {
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }
}
