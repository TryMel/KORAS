"""
KORAS Model Context Protocol (MCP) Server.
Conforme à la spécification MCP officielle (Section 10.4 du CDC KORAS).
Expose les outils Android et services partenaires sous le protocole standard MCP.
"""

import sys
import json
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s [MCP] %(message)s")

TOOLS_DEFINITIONS = [
    {
        "name": "call_contact",
        "description": "Initie un appel téléphonique vers un contact ou numéro",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact_name": {"type": "string", "description": "Nom du contact"},
                "phone_number": {"type": "string", "description": "Numéro optionnel"}
            },
            "required": ["contact_name"]
        }
    },
    {
        "name": "send_sms",
        "description": "Envoie un SMS à un destinataire",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contact_name": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["contact_name", "message"]
        }
    },
    {
        "name": "open_app",
        "description": "Lance une application installée sur l'appareil Android",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string"}
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "read_screen_accessibility",
        "description": "Lit et normalise les éléments visibles à l'écran via AccessibilityService",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "transfer_money_preview",
        "description": "Génère un aperçu chiffré et vérifié d'une transaction financière sans exécution",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "recipient": {"type": "string"},
                "provider": {"type": "string", "default": "wave"}
            },
            "required": ["amount", "recipient"]
        }
    }
]

def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS_DEFINITIONS
            }
        }

    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        logging.info(f"Tool call requested: {name} with args {args}")

        if name in {"call_contact", "send_sms", "open_app", "read_screen_accessibility"}:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32001,
                    "message": "Exécution réservée au connecteur Android approuvé; résultat à rapporter par l'appareil."
                }
            }

        elif name == "call_contact":
            contact = args.get("contact_name")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Appel vers {contact} initié sur l'appareil."}]
                }
            }

        elif name == "send_sms":
            contact = args.get("contact_name")
            msg = args.get("message")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"SMS transmis à {contact} : {msg}"}]
                }
            }

        elif name == "open_app":
            app = args.get("app_name")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": f"Application {app} ouverte avec succès."}]
                }
            }

        elif name == "read_screen_accessibility":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "screen": "com.android.launcher",
                            "elements": [
                                {"type": "button", "label": "Téléphone", "clickable": True},
                                {"type": "button", "label": "Messages", "clickable": True}
                            ]
                        })
                    }]
                }
            }

        elif name == "transfer_money_preview":
            amount = args.get("amount")
            recipient = args.get("recipient")
            provider = args.get("provider", "wave")
            fee = round(amount * 0.01, 2)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "amount": amount,
                            "fee": fee,
                            "total": amount + fee,
                            "currency": "XOF",
                            "recipient": recipient,
                            "provider": provider,
                            "status": "preview_ready"
                        })
                    }]
                }
            }

        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Outil inconnu : {name}"}
            }

    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "resources": [
                    {
                        "uri": "koras://device/battery",
                        "name": "Niveau de batterie",
                        "mimeType": "application/json"
                    },
                    {
                        "uri": "koras://device/network",
                        "name": "État de la connectivité réseau",
                        "mimeType": "application/json"
                    }
                ]
            }
        }

    elif method == "prompts/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "prompts": [
                    {
                        "name": "clarification_prompt",
                        "description": "Demande une précision lorsque l'intention est incomplète"
                    }
                ]
            }
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Méthode non supportée : {method}"}
        }

def main():
    logging.info("KORAS MCP Server running (stdio)...")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            logging.error(f"Error processing request: {e}")

if __name__ == "__main__":
    main()
