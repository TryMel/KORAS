from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.config import settings

class PolicyCheckResult(BaseModel):
    allowed: bool
    requires_approval: bool
    requires_biometric: bool
    reason: str
    idempotency_key: Optional[str] = None

class PolicyEngine:
    @staticmethod
    def evaluate(
        action_name: str,
        parameters: Dict[str, Any],
        device_trusted: bool,
        battery_level: Optional[int] = None,
        is_offline: bool = False,
        user_vulnerable_mode: bool = False
    ) -> PolicyCheckResult:
        """
        Enforces system policy before planning or executing any action.
        """
        # 1. Device trust check
        if not device_trusted and action_name in ["transfer_money", "modify_setting", "revoke_device"]:
            return PolicyCheckResult(
                allowed=False,
                requires_approval=False,
                requires_biometric=False,
                reason="Appareil non certifié ou révoqué. Action sensible interdite."
            )

        # 2. Critical battery policy (Section 37 - E3)
        if battery_level is not None and battery_level <= 5 and action_name in ["transfer_money", "open_maps"]:
            return PolicyCheckResult(
                allowed=False,
                requires_approval=False,
                requires_biometric=False,
                reason="Batterie critique (<= 5%). Opération suspendue pour éviter une coupure en cours d'exécution."
            )

        # 3. Offline capability check (Section 29)
        if is_offline and action_name in ["transfer_money", "open_url", "search_web"]:
            return PolicyCheckResult(
                allowed=False,
                requires_approval=False,
                requires_biometric=False,
                reason="Connexion Internet indisponible pour ce service externe."
            )

        # 4. Financial transfer rules (Section 3.1 & 19)
        if action_name == "transfer_money":
            if not settings.ENABLE_FINANCIAL_CONNECTORS:
                return PolicyCheckResult(
                    allowed=False,
                    requires_approval=False,
                    requires_biometric=False,
                    reason="Les transferts financiers ne sont pas encore activés pour cette version."
                )
            amount = parameters.get("amount")
            recipient = parameters.get("recipient")
            if not amount or amount <= 0:
                return PolicyCheckResult(
                    allowed=False,
                    requires_approval=False,
                    requires_biometric=False,
                    reason="Le montant du transfert doit être supérieur à zéro."
                )
            if not recipient:
                return PolicyCheckResult(
                    allowed=False,
                    requires_approval=False,
                    requires_biometric=False,
                    reason="Destinataire manquant ou invalide pour le transfert."
                )

            return PolicyCheckResult(
                allowed=True,
                requires_approval=True,
                requires_biometric=True,
                reason="Action financière critique : accord explicite et authentification forte exigés."
            )

        # 5. External actions (SMS, Call)
        if action_name in ["send_sms", "call_contact", "create_event", "create_reminder", "accessibility_click"]:
            requires_approval = True
            if action_name == "send_sms" and not parameters.get("message"):
                return PolicyCheckResult(
                    allowed=False,
                    requires_approval=False,
                    requires_biometric=False,
                    reason="Contenu du SMS vide."
                )
            return PolicyCheckResult(
                allowed=True,
                requires_approval=requires_approval,
                requires_biometric=False,
                reason="Action de communication externe conforme."
            )

        # Default allowed
        return PolicyCheckResult(
            allowed=True,
            requires_approval=user_vulnerable_mode,
            requires_biometric=False,
            reason="Action autorisée par la politique système."
        )
