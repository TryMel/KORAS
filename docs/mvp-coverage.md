# Couverture MVP KORAS

Ce document suit strictement la section 4.1 du CDC. Une capacité n’est marquée
comme exécutée que lorsqu’elle passe par un connecteur Android ou une API réelle;
aucun résultat n’est simulé par le backend.

| Exigence MVP | Implémentation |
| --- | --- |
| Voix, texte, langue, intention, paramètres, clarification, contexte | `speech_to_text`, saisie Flutter, détection fr/en déterministe, `IntentResolver`, clarification multi-tour et contexte appareil/session |
| Ouvrir app, URL, Maps, navigation, web | Intent Android (`AppTool`) avec retour d’ouverture observé |
| Contacts, appel, SMS | recherche locale `ContactsContract`, permissions runtime, appel/SMS après confirmation backend |
| Notifications et messages | `NotificationListenerService` activé explicitement par l’utilisateur; les messages présents dans les notifications sont lus sans exfiltration |
| Rappels et événements | Intent calendrier Android prérempli; l’utilisateur confirme l’enregistrement dans l’application Calendrier |
| Informations système | batterie, réseau, modèle, version et identifiant Android collectés localement pour le contexte |
| Lecture/action accessible | `AccessibilityService` opt-in : lecture sémantique et clic strict par libellé, après confirmation |
| Historique, états, confirmation, annulation, répétition, erreurs, hors-ligne | API conversations/audit, états agent, feuille de confirmation, annulation, commande « répète », erreurs typées et actions locales encore disponibles hors ligne |
| Authentification, session, appareils | inscription/connexion JWT, sessions persistées, enregistrement/révocation d’appareil, trust check par identifiant Android |
| Permissions, validation, risque, audit, anomalie | permissions Android à l’exécution, validation des contrats d’outils, moteur de risque/politique, audit persistant et alerte après trois échecs consécutifs |

## Limites explicitement assumées par le MVP

- Les intégrations financières restent désactivées : elles sont prévues en V3 du
  CDC, après validation de partenaires autorisés.
- L’état « SMS remis » et « appel lancé » ne doit pas être interprété comme une
  livraison SMS ou une conversation effectivement aboutie. Android ne donne pas
  ces garanties via l’Intent d’appel; KORAS ne les annonce donc pas comme telles.
- La lecture des notifications et l’accessibilité exigent l’activation volontaire
  des services correspondants dans les réglages Android.
