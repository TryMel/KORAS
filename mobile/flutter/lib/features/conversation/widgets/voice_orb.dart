import 'package:flutter/material.dart';

/// Section 32 & 95 — Voice Orb / Microphone button
class VoiceOrb extends StatefulWidget {
  final bool isListening;
  final bool isActive;
  final VoidCallback onPressed;

  const VoiceOrb({
    super.key,
    required this.isListening,
    required this.isActive,
    required this.onPressed,
  });

  @override
  State<VoiceOrb> createState() => _VoiceOrbState();
}

class _VoiceOrbState extends State<VoiceOrb> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.15)
        .chain(CurveTween(curve: Curves.easeInOut))
        .animate(_controller);
    _glowAnimation = Tween<double>(begin: 0.3, end: 1.0)
        .chain(CurveTween(curve: Curves.easeInOut))
        .animate(_controller);
  }

  @override
  void didUpdateWidget(VoiceOrb oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isListening && !_controller.isAnimating) {
      _controller.repeat(reverse: true);
    } else if (!widget.isListening) {
      _controller.stop();
      _controller.reset();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Semantics(
          button: true,
          label: widget.isListening
              ? 'Arrêter l\'écoute. KORAS vous écoute.'
              : 'Appuyez pour parler à KORAS',
          onTap: widget.onPressed,
          child: GestureDetector(
            onTap: widget.onPressed,
            child: Transform.scale(
              scale: widget.isListening ? _scaleAnimation.value : 1.0,
              child: Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: widget.isListening
                        ? [Colors.red.shade400, Colors.red.shade700]
                        : [const Color(0xFF6C63FF), const Color(0xFF4B44CC)],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: (widget.isListening ? Colors.red : const Color(0xFF6C63FF))
                          .withOpacity(widget.isListening ? _glowAnimation.value * 0.6 : 0.3),
                      blurRadius: widget.isListening ? 24 : 12,
                      spreadRadius: widget.isListening ? 4 : 2,
                    ),
                  ],
                ),
                child: Icon(
                  widget.isListening ? Icons.stop_rounded : Icons.mic_rounded,
                  color: Colors.white,
                  size: 30,
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
