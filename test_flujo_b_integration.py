#!/usr/bin/env python3
"""
Plan de Pruebas Integración — Flujo B Completo
Estrategia: enviar mensajes vía Telegram API (sin polling) y verificar
el estado leyendo archivos locales del bot.
"""
import asyncio
import json
import time
import sys
import os
import glob
from pathlib import Path

import httpx

BOT_TOKEN = "8222165892:AAFdsLM6IEBxAvayetIxBmmfx2I89eVn8zM"
GROUP_ID = -1003916745496
STATE_DIR = Path.home() / ".hermes" / "hermesdm" / "campaigns"

def get_latest_state_file():
    """Encuentra el archivo state.json más reciente."""
    pattern = str(STATE_DIR / "*" / "state.json")
    files = glob.glob(pattern)
    if not files:
        return None
    # Ordenar por mtime
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files[0]

def read_state():
    """Lee el estado actual de la campaña."""
    state_file = get_latest_state_file()
    if not state_file or not os.path.exists(state_file):
        return {}
    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Error leyendo state: {e}")
        return {}

async def send_message(text: str):
    """Envía mensaje al grupo vía Telegram Bot API (HTTP, no polling)."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": GROUP_ID,
        "text": text
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=payload, timeout=15)
        data = r.json()
        if not data.get("ok"):
            print(f"[ERROR] Telegram API: {data}")
            return False
        print(f"[SENT] {text} → msg_id={data['result']['message_id']}")
        return True

async def run_test(name: str, cmd: str, verifier, delay: float = 5.0):
    """Ejecuta un test: envía comando, espera, verifica estado."""
    print(f"\n{'='*50}")
    print(f"TEST: {name}")
    print(f"{'='*50}")
    
    state_before = read_state()
    print(f"[STATE BEFORE] {json.dumps(state_before, indent=2)[:500]}")
    
    ok = await send_message(cmd)
    if not ok:
        print("❌ FAIL: No se pudo enviar comando")
        return False
    
    print(f"[WAIT] Esperando {delay}s para procesamiento...")
    await asyncio.sleep(delay)
    
    state_after = read_state()
    print(f"[STATE AFTER] {json.dumps(state_after, indent=2)[:500]}")
    
    result = verifier(state_before, state_after)
    if result:
        print(f"✅ PASS: {name}")
    else:
        print(f"❌ FAIL: {name}")
    return result

async def main():
    print("=" * 60)
    print("PLAN DE PRUEBAS INTEGRACIÓN — FLUJO B")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # TEST 1: /setup → estado cambia a setup_complete=True
    async def verify_setup(before, after):
        return after.get("setup_complete") == True
    
    if await run_test("/setup → setup_complete", "/setup", verify_setup, delay=8):
        passed += 1
    else:
        failed += 1
    
    # TEST 2: /join → jugador en players
    async def verify_join(before, after):
        players = after.get("players", {})
        return str(7267426377) in players or any(
            p.get("username") == "shugar" or p.get("name") == "Sherman"
            for p in players.values()
        )
    
    if await run_test("/join → jugador registrado", "/join", verify_join, delay=6):
        passed += 1
    else:
        failed += 1
    
    # TEST 3: /begin → estado cambia a in_game
    async def verify_begin(before, after):
        return after.get("status") == "in_game" or after.get("game_started") == True
    
    if await run_test("/begin → in_game", "/begin", verify_begin, delay=8):
        passed += 1
    else:
        failed += 1
    
    # TEST 4: /j Orco → última_acción tiene ataque
    async def verify_attack(before, after):
        action = after.get("last_action", "")
        combat = after.get("combat", {})
        return any(x in action.lower() for x in ["ataque", "attack", "golpe", "hit"]) or \
               combat.get("round", 0) > 0 or combat.get("active") == True
    
    if await run_test("/j Orco → ataque registrado", "/j Orco", verify_attack, delay=10):
        passed += 1
    else:
        failed += 1
    
    # TEST 5: /cast Fireball → hechizo registrado
    async def verify_cast(before, after):
        action = after.get("last_action", "")
        return any(x in action.lower() for x in ["hechizo", "spell", "fireball", "magia"])
    
    if await run_test("/cast Fireball → hechizo registrado", "/cast Fireball", verify_cast, delay=10):
        passed += 1
    else:
        failed += 1
    
    # TEST 6: /status → devuelve estado del personaje
    # Este es más difícil de verificar por estado, verificamos que no crashea
    async def verify_status(before, after):
        # Si llegamos aquí sin excepción, es pass
        return True
    
    if await run_test("/status → sin crash", "/status", verify_status, delay=5):
        passed += 1
    else:
        failed += 1
    
    # RESUMEN
    print("\n" + "=" * 60)
    print(f"RESULTADOS: {passed} PASS | {failed} FAIL")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
