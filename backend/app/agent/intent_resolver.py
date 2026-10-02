import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class IntentResult(BaseModel):
    intent_name: str
    tool_id: str
    parameters: Dict[str, Any]
    confidence: float
    is_ambiguous: bool = False
    clarification_question: Optional[str] = None
    original_text: str

class IntentResolver:
    @staticmethod
    def detect_language(text: str) -> str:
        """Lightweight on-device compatible language identification for the MVP."""
        lower = text.lower()
        if any(token in lower for token in ("hello", "please", "call ", "open ", "send ")):
            return "en"
        # The supported MVP language is French; unrecognised utterances stay in
        # French and can be clarified rather than silently sent to a cloud model.
        return "fr"

    @staticmethod
    def resolve(text: str, context: Optional[Dict[str, Any]] = None) -> List[IntentResult]:
        """
        Parses text and extracts normalized intents and entities.
        Supports multi-intent decomposition (Section 98).
        """
        if not text:
            return []

        cleaned_text = text.strip()
        language = IntentResolver.detect_language(cleaned_text)
        results: List[IntentResult] = []

        # Check for multi-intent connector: "puis", "ensuite", "et après"
        parts = re.split(r"\b(?:puis|ensuite|et\s+après)\b", cleaned_text, flags=re.IGNORECASE)

        for part in parts:
            part_str = part.strip()
            if not part_str:
                continue
            intent = IntentResolver._resolve_single(part_str, {**(context or {}), "language": language})
            results.append(intent)

        return results

    @staticmethod
    def _resolve_single(text: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        lower = text.lower()

        # 1. Money transfer (Section 2, 19, 35 - N5)
        # Patterns like: "envoie 5 000 francs à maman", "transfère 10000 à kouassi", "envoie de l'argent à paul"
        transfer_match = re.search(r"\b(?:envoie|transf[eè]re|donne|paye)\b", lower)
        if transfer_match and ("argent" in lower or "franc" in lower or "fcfa" in lower or "cfa" in lower or re.search(r"\d+", lower)):
            # Extract amount
            amount_match = re.search(r"(\d+(?:[\s.,]\d+)?)\s*(?:francs?|fcfa|cfa|f)?", lower)
            amount = None
            if amount_match:
                try:
                    amount_str = amount_match.group(1).replace(" ", "").replace(",", ".")
                    amount = float(amount_str)
                except ValueError:
                    amount = None

            # Extract recipient: "à maman", "à marie", "pour kouamé"
            recipient_match = re.search(r"(?:à|au|pour)\s+([a-zA-ZÀ-ÿ0-9\s]+?)(?:$|\s+(?:par|via|sur))", lower)
            recipient = recipient_match.group(1).strip() if recipient_match else None

            # If recipient is "maman" and context has contacts:
            if not amount:
                return IntentResult(
                    intent_name="transfer_money",
                    tool_id="transfer_money",
                    parameters={"recipient": recipient} if recipient else {},
                    confidence=0.85,
                    is_ambiguous=True,
                    clarification_question="Quel montant souhaitez-vous envoyer ?",
                    original_text=text
                )

            if not recipient:
                return IntentResult(
                    intent_name="transfer_money",
                    tool_id="transfer_money",
                    parameters={"amount": amount},
                    confidence=0.85,
                    is_ambiguous=True,
                    clarification_question="À qui souhaitez-vous envoyer cette somme ?",
                    original_text=text
                )

            return IntentResult(
                intent_name="transfer_money",
                tool_id="transfer_money",
                parameters={"amount": amount, "recipient": recipient, "currency": "XOF"},
                confidence=0.95,
                original_text=text
            )

        # 2. Call Contact (Section 35 - N1)
        # "appelle maman", "téléphone à jean", "passe un coup de fil à ali"
        call_match = re.search(r"\b(?:appelle|appeler|téléphone|téléphoner)\b(?:\s+(?:à|au))?\s+([a-zA-ZÀ-ÿ0-9\s]+)", lower)
        if call_match:
            contact = call_match.group(1).strip()
            # Clean contact string
            contact = re.sub(r"\b(?:sur son portable|directement|s'il te plaît)\b", "", contact).strip()
            return IntentResult(
                intent_name="call_contact",
                tool_id="call_contact",
                parameters={"contact_name": contact},
                confidence=0.96,
                original_text=text
            )

        # 3. Send SMS (Section 35 - N2)
        # "écris à paul que j'arrive", "envoie un sms à maman disant je viens", "envoie un message à koffi"
        sms_match = re.search(r"\b(?:écris|envoyer\s+un\s+sms|envoie\s+un\s+message|sms)\b(?:\s+à)?\s+([a-zA-ZÀ-ÿ0-9\s]+?)\s+(?:que|disant|pour\s+dire)\s+(.+)", lower)
        if sms_match:
            contact = sms_match.group(1).strip()
            msg = sms_match.group(2).strip()
            return IntentResult(
                intent_name="send_sms",
                tool_id="send_sms",
                parameters={"contact_name": contact, "message": msg},
                confidence=0.94,
                original_text=text
            )

        sms_short_match = re.search(r"\b(?:écris|envoie\s+un\s+message|envoie\s+un\s+sms)\b(?:\s+à)?\s+([a-zA-ZÀ-ÿ0-9\s]+)", lower)
        if sms_short_match and "argent" not in lower:
            contact = sms_short_match.group(1).strip()
            return IntentResult(
                intent_name="send_sms",
                tool_id="send_sms",
                parameters={"contact_name": contact},
                confidence=0.80,
                is_ambiguous=True,
                clarification_question=f"Quel message souhaitez-vous envoyer à {contact} ?",
                original_text=text
            )

        # 4. Open Application
        # "ouvre whatsapp", "lance facebook", "ouvre youtube"
        app_match = re.search(r"\b(?:ouvre|lance|démarrer|afficher)\b\s+([a-zA-ZÀ-ÿ0-9\s]+)", lower)
        if app_match and not any(k in lower for k in ["maps", "carte", "navigation", "position", "http", "www."]):
            app_name = app_match.group(1).strip()
            return IntentResult(
                intent_name="open_app",
                tool_id="open_app",
                parameters={"app_name": app_name},
                confidence=0.92,
                original_text=text
            )

        # 4b. Open a URL or search the web. URLs are routed before generic
        # "ouvre" application resolution so a web address is never treated as an app.
        url_match = re.search(r"\b(?:ouvre|va sur)\s+(https?://\S+|www\.\S+)", lower)
        if url_match:
            return IntentResult(intent_name="open_url", tool_id="open_url", parameters={"url": url_match.group(1)}, confidence=0.94, original_text=text)
        contact_match = re.search(r"\b(?:cherche|trouve)\s+(?:le )?contact\s+(.+)", lower)
        if contact_match:
            return IntentResult(intent_name="search_contact", tool_id="search_contact", parameters={"query": contact_match.group(1).strip()}, confidence=0.92, original_text=text)

        search_match = re.search(r"\b(?:cherche|recherche)\s+(.+)", lower)
        if search_match:
            return IntentResult(intent_name="search_web", tool_id="search_web", parameters={"query": search_match.group(1).strip()}, confidence=0.88, original_text=text)

        # 5. Maps / Navigation (Section 35 - N3)
        # "conduis-moi à l'hôpital", "ouvre maps", "emmène-moi au supermarché"
        nav_match = re.search(r"\b(?:conduis-moi|emmène-moi|itinéraire|navigation|direction)\b(?:\s+(?:à|au|vers))?\s*(.+)", lower)
        if nav_match or "maps" in lower:
            dest = nav_match.group(1).strip() if nav_match else "destination inconnue"
            return IntentResult(
                intent_name="open_maps",
                tool_id="open_maps",
                parameters={"destination": dest},
                confidence=0.90,
                original_text=text
            )

        # 6. Read Notification (Section 35 - N4)
        # "lis mes messages", "lis mes notifications", "qu'est-ce que j'ai reçu"
        if any(k in lower for k in ["notification", "notif", "dernier message", "nouveaux messages", "qu'est-ce que j'ai reçu"]):
            return IntentResult(
                intent_name="read_notification",
                tool_id="read_notification",
                parameters={"limit": 3},
                confidence=0.93,
                original_text=text
            )

        # 7. Create Reminder
        # "rappelle-moi demain à huit heures de lui envoyer le document"
        reminder_match = re.search(r"\b(?:rappelle-moi|rappel|alarme|souviens-toi)\b\s*(.+)", lower)
        if reminder_match:
            remind_content = reminder_match.group(1).strip()
            return IntentResult(
                intent_name="create_reminder",
                tool_id="create_reminder",
                parameters={"title": remind_content},
                confidence=0.88,
                original_text=text
            )

        event_match = re.search(r"\b(?:crée|créer|ajoute|ajouter)\s+(?:un )?(?:événement|evenement)\s+(.+)", lower)
        if event_match:
            return IntentResult(intent_name="create_event", tool_id="create_event", parameters={"title": event_match.group(1).strip()}, confidence=0.88, original_text=text)

        # 8. Read Screen / Accessibility
        if any(k in lower for k in ["lis l'écran", "qu'est-ce qu'il y a sur l'écran", "aide-moi à lire"]):
            return IntentResult(
                intent_name="read_screen",
                tool_id="read_screen",
                parameters={},
                confidence=0.95,
                original_text=text
            )

        click_match = re.search(r"\b(?:appuie|clique|sélectionne)\s+(?:sur )?(.+)", lower)
        if click_match:
            return IntentResult(intent_name="accessibility_click", tool_id="accessibility_click", parameters={"label": click_match.group(1).strip()}, confidence=0.82, original_text=text)

        # Fallback unknown or ambiguous
        return IntentResult(
            intent_name="unknown",
            tool_id="clarify",
            parameters={"raw_query": text},
            confidence=0.35,
            is_ambiguous=True,
            clarification_question="Je ne suis pas certain de comprendre votre demande. Pouvez-vous préciser ?",
            original_text=text
        )
