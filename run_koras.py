#!/usr/bin/env python3
"""
KORAS — Script de lancement rapide et d'exécution locale.
Usage :
  python run_koras.py backend    # Démarre l'API FastAPI KORAS
  python run_koras.py mcp        # Démarre le serveur MCP en mode stdio
  python run_koras.py test       # Exécute la suite de tests complète (pytest)
"""

import sys
import os
import subprocess

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

def run_backend():
    print("[*] Démarrage du backend FastAPI KORAS sur http://127.0.0.1:8000 ...")
    env = os.environ.copy()
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000", "--host", "0.0.0.0"]
    raise SystemExit(subprocess.run(cmd, cwd=backend_dir, env=env).returncode)

def run_mcp():
    print("[*] Démarrage du serveur KORAS MCP (JSON-RPC stdio) ...")
    mcp_script = os.path.join(os.path.dirname(__file__), "mcp", "koras_mcp_server.py")
    raise SystemExit(subprocess.run([sys.executable, mcp_script]).returncode)

def run_tests():
    print("[*] Lancement de la suite de tests KORAS...")
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    test_path = os.path.join(os.path.dirname(__file__), "tests", "backend")
    cmd = [sys.executable, "-m", "pytest", test_path, "-v"]
    raise SystemExit(subprocess.run(cmd, cwd=backend_dir).returncode)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "backend":
        run_backend()
    elif sys.argv[1] == "mcp":
        run_mcp()
    elif sys.argv[1] == "test":
        run_tests()
    else:
        print("Commande non reconnue. Options: backend | mcp | test")
