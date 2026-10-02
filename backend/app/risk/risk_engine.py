from typing import Dict, Any, Tuple
from enum import IntEnum

class RiskLevel(IntEnum):
    LEVEL_0_READ = 0           # Pure read: time, weather, read authorized notice
    LEVEL_1_LOCAL_REVERSIBLE = 1  # Open app, view screen
    LEVEL_2_EXTERNAL = 2       # Send message, call contact, create reminder
    LEVEL_3_SENSITIVE = 3      # Delete item, change settings
    LEVEL_4_CRITICAL = 4       # Financial transfer, payment, irreversible

class RiskEngine:
    @staticmethod
    def assess_risk(
        tool_id: str,
        parameters: Dict[str, Any],
        user_vulnerable_mode: bool = False
    ) -> Tuple[RiskLevel, bool, str]:
        """
        Returns: (RiskLevel, requires_confirmation, rationale)
        """
        # Mapping base tool risk levels
        tool_risk_map = {
            "get_time": RiskLevel.LEVEL_0_READ,
            "get_weather": RiskLevel.LEVEL_0_READ,
            "read_notification": RiskLevel.LEVEL_0_READ,
            "read_screen": RiskLevel.LEVEL_0_READ,
            "search_contact": RiskLevel.LEVEL_0_READ,
            
            "open_app": RiskLevel.LEVEL_1_LOCAL_REVERSIBLE,
            "open_url": RiskLevel.LEVEL_1_LOCAL_REVERSIBLE,
            "open_maps": RiskLevel.LEVEL_1_LOCAL_REVERSIBLE,
            "accessibility_click": RiskLevel.LEVEL_1_LOCAL_REVERSIBLE,
            
            "call_contact": RiskLevel.LEVEL_2_EXTERNAL,
            "send_sms": RiskLevel.LEVEL_2_EXTERNAL,
            "create_reminder": RiskLevel.LEVEL_2_EXTERNAL,
            "create_event": RiskLevel.LEVEL_2_EXTERNAL,
            
            "delete_reminder": RiskLevel.LEVEL_3_SENSITIVE,
            "modify_setting": RiskLevel.LEVEL_3_SENSITIVE,
            "revoke_device": RiskLevel.LEVEL_3_SENSITIVE,
            
            "transfer_money": RiskLevel.LEVEL_4_CRITICAL,
            "payment": RiskLevel.LEVEL_4_CRITICAL,
        }

        level = tool_risk_map.get(tool_id, RiskLevel.LEVEL_2_EXTERNAL)

        # Elevate risk if parameters involve high amount or unknown entities
        if tool_id == "transfer_money":
            amount = parameters.get("amount", 0)
            if amount > 50000:
                rationale = f"Transfert d'un montant élevé ({amount} XOF). Niveau critique avec confirmation renforcée."
            else:
                rationale = f"Transfert financier ({amount} XOF). Niveau critique obligatoire."
            return (RiskLevel.LEVEL_4_CRITICAL, True, rationale)

        # In vulnerable mode, enforce confirmation on Level 1 and Level 2
        if user_vulnerable_mode:
            if level >= RiskLevel.LEVEL_1_LOCAL_REVERSIBLE:
                return (
                    level,
                    True,
                    f"Mode utilisateur protégé actif : confirmation requise pour '{tool_id}'."
                )

        requires_conf = level >= RiskLevel.LEVEL_2_EXTERNAL
        rationale = f"Outil '{tool_id}' classifié niveau {level.value} ({level.name})."
        return (level, requires_conf, rationale)
