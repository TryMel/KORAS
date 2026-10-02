# KORAS — Inventaire et Audit du Prototype

**Date :** 29 Septembre 2026  
**Document :** docs/prototype-inventory.md  
**Conformité :** Sections 78 & 112 du Cahier des Charges KORAS v1.0  

---

## 1. État initial du dépôt

* **Dépôt Git :** `origin/main` initialisé avec un README minimal et le cahier des charges officiel dans `docs/cdc.txt`.
* **Code existant antérieur :** Aucun code legacy ou prototype obsolète présent sur la branche principale ; dépôt vierge prêt pour la mise en place de l'architecture cible KORAS (Flutter + Kotlin Android natif + FastAPI Python + PostgreSQL + Redis + MCP).
* **Environnement système détecté :**
  * Système hôte : Windows 11
  * Flutter SDK : 3.47.5 (Dart 3.13.4) installé dans `C:\flutter`
  * Android SDK : Installé dans `C:\Users\USER\AppData\Local\Android\Sdk` et `C:\android\platform-tools`
  * Java Runtime : Oracle Java SDK
  * Python Runtime : Python 3.13
  * Node.js : Node v22.23.1
  * Git : Version 2.x

---

## 2. Décisions d'ingénierie et architecture à initialiser

Conformément à la **Règle finale d'implémentation (Section 114)** :
> *Ne pas commencer par un chatbot. Ne pas commencer par Mobile Money. Ne pas commencer par le LLM seul.*  
> *Commencer par : L'ACTION RÉELLE SUR LE TÉLÉPHONE.*

### Composants à initialiser immédiatement (Monorepo KORAS) :

1. **`mobile/flutter/` & `android/` :**
   * Application Flutter 3.x avec gestion d'état réactive (architecture propre : Presentation / Domain / Infrastructure).
   * Couche native Kotlin (`com.koras`) :
     * `MethodChannel` & `EventChannel`
     * `KorasAccessibilityService` pour l'assistance et la lecture d'écran
     * Audio (`AudioCapture`, `VoiceActivityDetector`, `SpeechRecognizer`, `TtsManager`)
     * Communication & Télécom (`CallExecutor`, `SmsExecutor`, `ContactProvider`, `NotificationReader`)
     * Outils Android (`AppTool`, `PhoneTool`, `SmsTool`, `DeviceTool`)
     * Sécurité locale (`SecureStorage`, `BiometricAuthenticator`, `DeviceBinding`)
   * Écrans adaptés aux publics cibles (malvoyants, peu alphabétisés) : gros boutons, retours vocaux systématiques, contrastes élevés, TalkBack.

2. **`backend/` :**
   * Framework : Python FastAPI modulaire et asynchrone.
   * `app/core/` : configuration, sécurité JWT & clés d'API, hashing, idempotence, logging structuré.
   * `app/database/` : modèles SQLAlchemy (utilisateurs, appareils, sessions, conversations, intentions, agent_runs, actions, approbations, outils, politiques, transactions financières contrôlées, logs d'audit).
   * `app/agent/` : machine d'état de l'agent (`agent_runtime.py`, `intent_resolver.py`, `planner.py`, `executor.py`, `verifier.py`).
   * `app/policy/` & `app/risk/` : moteurs de politiques d'autorisation et d'évaluation des risques (Niveaux 0 à 4 avec approbation obligatoire et validation humaine préalable).
   * `app/tools/` : registre des outils avec contrats stricts d'entrée/sortie, idempotence et rollback.
   * `app/mcp/` : client et adaptateurs protocole Model Context Protocol (MCP).
   * `app/ai/` : abstraction `ModelProvider` (routage local / cloud, ASR, TTS, LLM) sans dépendance directe du coeur métier.
   * `app/audit/` : journalisation d'audit immuable de chaque action sensible.

3. **`mcp/` :**
   * Serveur MCP autonome exposant les capacités du device et les services autorisés sous le protocole MCP standard (JSON-RPC).

4. **`admin/` :**
   * Interface de supervision et backoffice d'administration (Next.js / TypeScript / Tailwind) pour la gestion des utilisateurs, des appareils révoqués, la visualisation des exécutions d'agents, les journaux d'audit et la simulation sandbox.

5. **`tests/` :**
   * Suites de tests unitaires et d'intégration pour le moteur d'intention, le risk engine, la politique d'idempotence et les endpoints d'action.
