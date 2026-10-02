import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Section 32 & 62 — Paramètres et mode utilisateur vulnérable
class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  bool _vulnerableMode = false;
  bool _voiceFeedbackAlways = true;
  double _voiceSpeed = 0.85;
  String _selectedLanguage = 'Français (Côte d\'Ivoire)';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0D0D),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1A1A2E),
        title: const Text('Paramètres', style: TextStyle(color: Colors.white)),
        elevation: 0,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Section Accessibilité & Vulnérabilité
          _buildSectionHeader('Accessibilité & Protection'),
          
          // Switch Mode Vulnérable (Section 62)
          SwitchListTile(
            title: const Text(
              'Mode protection renforcée',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
            ),
            subtitle: const Text(
              'Vocabulaire simplifié, confirmation systématique même pour les actions mineures et délais allongés.',
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
            value: _vulnerableMode,
            activeColor: const Color(0xFF6C63FF),
            tileColor: const Color(0xFF1A1A2E),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            onChanged: (val) => setState(() => _vulnerableMode = val),
          ),
          const SizedBox(height: 12),

          // Switch Retour vocal permanent
          SwitchListTile(
            title: const Text(
              'Retour vocal systématique',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600),
            ),
            subtitle: const Text(
              'KORAS lit oralement chaque résultat et étape d\'action.',
              style: TextStyle(color: Colors.white54, fontSize: 13),
            ),
            value: _voiceFeedbackAlways,
            activeColor: const Color(0xFF6C63FF),
            tileColor: const Color(0xFF1A1A2E),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            onChanged: (val) => setState(() => _voiceFeedbackAlways = val),
          ),
          const SizedBox(height: 24),

          // Section Voix & Langue
          _buildSectionHeader('Voix et Langue'),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF1A1A2E),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Langue d\'interaction', style: TextStyle(color: Colors.white70, fontSize: 14)),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: _selectedLanguage,
                  dropdownColor: const Color(0xFF1E1E2E),
                  style: const TextStyle(color: Colors.white, fontSize: 16),
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: Colors.white10,
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
                  ),
                  items: const [
                    DropdownMenuItem(value: 'Français (Côte d\'Ivoire)', child: Text('Français (Côte d\'Ivoire)')),
                    DropdownMenuItem(value: 'Français (Standard)', child: Text('Français (Standard)')),
                    DropdownMenuItem(value: 'Dioula (Bêmanan)', child: Text('Dioula (Bêmanan)')),
                    DropdownMenuItem(value: 'English', child: Text('English')),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _selectedLanguage = val);
                  },
                ),
                const SizedBox(height: 16),
                Text('Vitesse de la voix : ${(_voiceSpeed * 100).toInt()}%', style: const TextStyle(color: Colors.white70, fontSize: 14)),
                Slider(
                  value: _voiceSpeed,
                  min: 0.5,
                  max: 1.2,
                  divisions: 7,
                  activeColor: const Color(0xFF6C63FF),
                  onChanged: (val) => setState(() => _voiceSpeed = val),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Section Sécurité & Confidentialité (Section 73 & 75)
          _buildSectionHeader('Sécurité & Appareil'),
          _buildActionTile(
            title: 'Révoquer cet appareil',
            subtitle: 'Déconnecte la session et bloque toutes les actions sensibles.',
            icon: Icons.phonelink_erase,
            color: Colors.orange,
            onTap: () {
              _showRevokeDialog(context);
            },
          ),
          const SizedBox(height: 12),
          _buildActionTile(
            title: 'Supprimer mes données KORAS',
            subtitle: 'Suppression définitive de l\'historique et des préférences (Section 75).',
            icon: Icons.delete_forever,
            color: Colors.red,
            onTap: () {
              _showDeleteDataDialog(context);
            },
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10, left: 4),
      child: Text(
        title.toUpperCase(),
        style: const TextStyle(color: Color(0xFF6C63FF), fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 0.8),
      ),
    );
  }

  Widget _buildActionTile({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: color.withOpacity(0.15),
        child: Icon(icon, color: color, size: 22),
      ),
      title: Text(title, style: TextStyle(color: color, fontWeight: FontWeight.w600)),
      subtitle: Text(subtitle, style: const TextStyle(color: Colors.white54, fontSize: 12)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: color.withOpacity(0.3))),
      tileColor: const Color(0xFF1A1A2E),
      onTap: onTap,
    );
  }

  void _showRevokeDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E2E),
        title: const Text('Révoquer l\'appareil ?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'Toutes les autorisations locales et les clés de chiffrement de cet appareil seront révoquées.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Annuler', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Appareil révoqué avec succès.')),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
            child: const Text('Révoquer'),
          ),
        ],
      ),
    );
  }

  void _showDeleteDataDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E1E2E),
        title: const Text('Supprimer toutes les données ?', style: TextStyle(color: Colors.white)),
        content: const Text(
          'Conformément à la politique de confidentialité (Section 75), toutes vos conversations, historiques et consentements seront effacés.',
          style: TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Annuler', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Données supprimées avec succès.')),
              );
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Supprimer définitivement'),
          ),
        ],
      ),
    );
  }
}
