import 'dart:async';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../domain/models/agent_models.dart';
import '../../../domain/repositories/agent_repository.dart';
import '../../../core/platform/koras_platform_bridge.dart';

// ─── Conversation State ────────────────────────────────────────────────────────

class ConversationState {
  final AgentState agentState;
  final String? currentRunId;
  final AgentRunResult? lastResult;
  final List<ChatMessage> messages;
  final bool isListening;
  final bool isSpeaking;
  final String? currentTranscript;
  final String? error;
  final bool isOnline;

  const ConversationState({
    this.agentState = AgentState.idle,
    this.currentRunId,
    this.lastResult,
    this.messages = const [],
    this.isListening = false,
    this.isSpeaking = false,
    this.currentTranscript,
    this.error,
    this.isOnline = true,
  });

  ConversationState copyWith({
    AgentState? agentState,
    String? currentRunId,
    AgentRunResult? lastResult,
    List<ChatMessage>? messages,
    bool? isListening,
    bool? isSpeaking,
    String? currentTranscript,
    String? error,
    bool? isOnline,
  }) {
    return ConversationState(
      agentState: agentState ?? this.agentState,
      currentRunId: currentRunId ?? this.currentRunId,
      lastResult: lastResult ?? this.lastResult,
      messages: messages ?? this.messages,
      isListening: isListening ?? this.isListening,
      isSpeaking: isSpeaking ?? this.isSpeaking,
      currentTranscript: currentTranscript ?? this.currentTranscript,
      error: error,
      isOnline: isOnline ?? this.isOnline,
    );
  }
}

class ChatMessage {
  final String id;
  final String role; // 'user' or 'koras'
  final String content;
  final DateTime createdAt;
  final AgentState? agentState;
  final bool isFinal;

  const ChatMessage({
    required this.id,
    required this.role,
    required this.content,
    required this.createdAt,
    this.agentState,
    this.isFinal = true,
  });
}

class _DeviceExecution {
  final bool verified;
  final Map<String, dynamic> result;
  const _DeviceExecution(this.verified, [this.result = const {}]);
}

// ─── Providers ────────────────────────────────────────────────────────────────

final agentRepositoryProvider = Provider<AgentRepository>((ref) => AgentRepository());

final conversationProvider =
    StateNotifierProvider<ConversationNotifier, ConversationState>(
  (ref) => ConversationNotifier(ref.read(agentRepositoryProvider)),
);

// ─── Notifier ─────────────────────────────────────────────────────────────────

class ConversationNotifier extends StateNotifier<ConversationState> {
  final AgentRepository _repo;
  final SpeechToText _stt = SpeechToText();
  final FlutterTts _tts = FlutterTts();
  bool _sttAvailable = false;

  ConversationNotifier(this._repo) : super(const ConversationState()) {
    _initAudio();
  }

  Future<void> _initAudio() async {
    _sttAvailable = await _stt.initialize(
      onStatus: (status) {
        if (status == 'done' || status == 'notListening') {
          _onSpeechDone();
        }
      },
      onError: (error) => _handleSpeechError(error.errorMsg),
    );

    await _tts.setLanguage('fr-FR');
    await _tts.setSpeechRate(0.85);
    await _tts.setVolume(1.0);

    _tts.setCompletionHandler(() {
      state = state.copyWith(isSpeaking: false);
    });
  }

  // ─── Voice Input ──────────────────────────────────────────────────────────

  Future<void> startListening() async {
    // Interrupt current speech (Section 97)
    if (state.isSpeaking) {
      await _tts.stop();
      state = state.copyWith(isSpeaking: false);
    }

    if (!_sttAvailable) {
      state = state.copyWith(
        error: 'Microphone non disponible. Vérifiez les permissions.',
        agentState: AgentState.permissionDenied,
      );
      return;
    }

    state = state.copyWith(
      agentState: AgentState.listening,
      isListening: true,
      currentTranscript: null,
      error: null,
    );

    await _stt.listen(
      onResult: (result) {
        state = state.copyWith(currentTranscript: result.recognizedWords);
        if (result.finalResult && result.recognizedWords.isNotEmpty) {
          processInput(result.recognizedWords);
        }
      },
      localeId: 'fr_FR',
      cancelOnError: false,
      pauseFor: const Duration(seconds: 3),
    );
  }

  Future<void> stopListening() async {
    await _stt.stop();
    state = state.copyWith(isListening: false);
    if (state.currentTranscript?.isNotEmpty == true) {
      await processInput(state.currentTranscript!);
    }
  }

  void _onSpeechDone() {
    if (state.isListening && state.currentTranscript?.isEmpty != false) {
      state = state.copyWith(isListening: false, agentState: AgentState.idle);
    }
  }

  void _handleSpeechError(String errorMsg) {
    state = state.copyWith(
      isListening: false,
      agentState: AgentState.failed,
      error: 'Erreur microphone: $errorMsg',
    );
  }

  // ─── Text Input ───────────────────────────────────────────────────────────

  Future<void> processInput(String text) async {
    if (text.trim().isEmpty) return;

    if (text.trim().toLowerCase() == 'répète' || text.trim().toLowerCase() == 'repete') {
      final lastResponse = state.messages.lastWhere(
        (message) => message.role == 'koras',
        orElse: () => ChatMessage(id: 'none', role: 'koras', content: 'Je n’ai encore rien à répéter.', createdAt: DateTime.now()),
      );
      await _speak(lastResponse.content);
      return;
    }

    final resolvedText = _mergeClarification(text.trim());
    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      role: 'user',
      content: resolvedText,
      createdAt: DateTime.now(),
    );

    state = state.copyWith(
      agentState: AgentState.understanding,
      isListening: false,
      messages: [...state.messages, userMsg],
      currentTranscript: null,
      error: null,
    );

    try {
      // Check online status (Section 29)
      final isOnline = await KorasPlatformBridge.isNetworkAvailable();
      if (!isOnline) {
        state = state.copyWith(
          agentState: AgentState.offline,
          isOnline: false,
        );
        await _speak('Connexion indisponible. Seules les fonctions locales sont accessibles.');
      }

      // Get context from device
      final battery = await KorasPlatformBridge.getBatteryLevel();
      final deviceInfo = await KorasPlatformBridge.getDeviceInfo();

      state = state.copyWith(agentState: AgentState.thinking);

      final result = await _repo.runAgent(
        userInput: resolvedText,
        context: {
          'battery_level': battery,
          'is_offline': !isOnline,
          'device_model': deviceInfo['model'] ?? '',
        },
        deviceIdentifier: deviceInfo['device_identifier'] as String?,
      );

      await _handleAgentResult(result);
    } catch (e) {
      state = state.copyWith(
        agentState: AgentState.failed,
        error: e.toString(),
      );
      await _speak("Une erreur s'est produite. Veuillez réessayer.");
    }
  }

  String _mergeClarification(String answer) {
    final pending = state.lastResult;
    if (state.agentState != AgentState.waitingForClarification || pending == null) return answer;
    final feedback = pending.visualFeedback;
    final intent = feedback['intent'] as String?;
    final parameters = feedback['partial_parameters'] is Map
        ? Map<String, dynamic>.from(feedback['partial_parameters'] as Map) : const <String, dynamic>{};
    if (intent == 'transfer_money' && parameters['recipient'] != null) {
      return 'Envoie $answer francs à ${parameters['recipient']}';
    }
    if (intent == 'send_sms' && parameters['contact_name'] != null) {
      return 'Écris à ${parameters['contact_name']} que $answer';
    }
    return answer;
  }

  Future<void> _handleAgentResult(
    AgentRunResult result, {
    bool executeReadySteps = true,
  }) async {
    final korasMsg = ChatMessage(
      id: '${result.runId}_response',
      role: 'koras',
      content: result.spokenResponse,
      createdAt: DateTime.now(),
      agentState: result.state,
      isFinal: result.isTerminal,
    );

    state = state.copyWith(
      agentState: result.state,
      currentRunId: result.runId,
      lastResult: result,
      messages: [...state.messages, korasMsg],
    );

    // Speak the response (Section 32 & 33)
    await _speak(result.spokenResponse);

    if (executeReadySteps &&
        result.state == AgentState.executing &&
        !result.isTerminal) {
      await _executeReadySteps(result);
    }
  }

  /// Device actions are dispatched only after the API has applied policy and,
  /// where needed, the user has confirmed. A boolean launch result is an
  /// observation, not a guessed completion.
  Future<void> _executeReadySteps(AgentRunResult run) async {
    for (final step in run.steps.where((item) => item.status == 'ready')) {
      try {
        final observed = await _dispatchDeviceTool(step);
        final reported = await _repo.reportStepResult(
          runId: run.runId,
          stepId: step.stepId,
          status: observed.verified ? 'verified' : 'failed',
          result: observed.verified ? {'verified': true, 'tool_id': step.toolId, ...observed.result} : const {},
          error: observed.verified ? null : 'L’action Android n’a pas pu être lancée ou vérifiée.',
        );
        await _handleAgentResult(reported, executeReadySteps: false);
        if (reported.isTerminal ||
            reported.state == AgentState.waitingForConfirmation) {
          return;
        }
      } catch (error) {
        final reported = await _repo.reportStepResult(
          runId: run.runId,
          stepId: step.stepId,
          status: 'failed',
          error: error.toString(),
        );
        await _handleAgentResult(reported, executeReadySteps: false);
        return;
      }
    }
  }

  Future<_DeviceExecution> _dispatchDeviceTool(PlannedStepModel step) async {
    final p = step.parameters;
    Future<_DeviceExecution> simple(Future<bool> action) async => _DeviceExecution(await action);
    switch (step.toolId) {
      case 'open_app':
        return simple(KorasPlatformBridge.openApp(appName: p['app_name'] as String? ?? ''));
      case 'open_maps':
        return simple(KorasPlatformBridge.openMaps(destination: p['destination'] as String? ?? ''));
      case 'open_url':
        return simple(KorasPlatformBridge.openUrl(url: p['url'] as String? ?? ''));
      case 'search_web':
        return simple(KorasPlatformBridge.searchWeb(query: p['query'] as String? ?? ''));
      case 'call_contact':
        if (!await _allow(Permission.contacts) || !await _allow(Permission.phone)) return const _DeviceExecution(false);
        return simple(KorasPlatformBridge.callContact(
          contactName: p['contact_name'] as String? ?? '',
          phoneNumber: p['phone_number'] as String?,
        ));
      case 'send_sms':
        if (!await _allow(Permission.contacts) || !await _allow(Permission.sms)) return const _DeviceExecution(false);
        return simple(KorasPlatformBridge.sendSms(
          contactName: p['contact_name'] as String? ?? '',
          phoneNumber: p['phone_number'] as String?,
          message: p['message'] as String? ?? '',
        ));
      case 'create_reminder':
        return simple(KorasPlatformBridge.createReminder(title: p['title'] as String? ?? ''));
      case 'create_event':
        return simple(KorasPlatformBridge.createEvent(
          title: p['title'] as String? ?? '', description: p['description'] as String?,
        ));
      case 'read_notification':
        final notifications = await KorasPlatformBridge.readNotifications(
          limit: (p['limit'] as int?) ?? 3,
        );
        return _DeviceExecution(notifications.isNotEmpty, {'notifications': notifications});
      case 'search_contact':
        if (!await _allow(Permission.contacts)) return const _DeviceExecution(false);
        final contacts = await KorasPlatformBridge.searchContacts(p['query'] as String? ?? '');
        return _DeviceExecution(contacts.isNotEmpty, {'contacts': contacts});
      case 'read_screen':
        final screen = await KorasPlatformBridge.readScreenContent();
        return _DeviceExecution(screen['error'] == null, {'screen_content': screen});
      case 'accessibility_click':
        return simple(KorasPlatformBridge.performAccessibilityClick(p['label'] as String? ?? ''));
      // Notification reading and financial services require dedicated Android
      // or partner connectors and are deliberately not simulated.
      default:
        return const _DeviceExecution(false);
    }
  }

  Future<bool> _allow(Permission permission) async {
    final status = await permission.request();
    return status.isGranted;
  }

  // ─── Confirmation (Section 35 - CA-04, CA-05) ────────────────────────────

  Future<bool> confirmCurrentStep() async {
    final result = state.lastResult;
    final runId = state.currentRunId;
    if (result == null || runId == null || result.awaitingConfirmationStepId == null) {
      return false;
    }

    var biometricAuthenticated = false;
    final step = result.steps.firstWhere(
      (item) => item.stepId == result.awaitingConfirmationStepId,
    );
    if (step.requiresBiometric) {
      try {
        biometricAuthenticated = await KorasPlatformBridge.authenticateBiometric(
          reason: 'Confirmer ${step.toolName}',
        );
      } catch (error) {
        state = state.copyWith(error: error.toString());
        await _speak("L'authentification biométrique n'est pas disponible.");
        return false;
      }
      if (!biometricAuthenticated) {
        state = state.copyWith(error: "Authentification biométrique annulée.");
        return false;
      }
    }

    state = state.copyWith(agentState: AgentState.executing);

    try {
      final confirmed = await _repo.confirmStep(
        runId: runId,
        stepId: result.awaitingConfirmationStepId!,
        biometricAuthenticated: biometricAuthenticated,
      );
      await _handleAgentResult(confirmed);
      return true;
    } catch (e) {
      state = state.copyWith(
        agentState: AgentState.waitingForConfirmation,
        error: e.toString(),
      );
      await _speak("La confirmation a échoué. ${e.toString()}");
      return false;
    }
  }

  // ─── Cancellation (Section 36 - A4) ──────────────────────────────────────

  Future<void> cancelCurrentRun() async {
    final runId = state.currentRunId;
    if (runId == null) {
      state = state.copyWith(agentState: AgentState.cancelled);
      return;
    }

    try {
      final cancelled = await _repo.cancelRun(runId);
      await _handleAgentResult(cancelled);
    } catch (_) {
      state = state.copyWith(agentState: AgentState.cancelled);
    }
    await _speak('Opération annulée.');
  }

  // ─── TTS ──────────────────────────────────────────────────────────────────

  Future<void> _speak(String text) async {
    if (text.isEmpty) return;
    state = state.copyWith(isSpeaking: true);
    await _tts.speak(text);
  }

  Future<void> stopSpeaking() async {
    await _tts.stop();
    state = state.copyWith(isSpeaking: false);
  }

  // ─── Reset ────────────────────────────────────────────────────────────────

  void reset() {
    state = const ConversationState();
  }

  @override
  void dispose() {
    _stt.stop();
    _tts.stop();
    super.dispose();
  }
}
