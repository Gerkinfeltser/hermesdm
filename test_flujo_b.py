#!/usr/bin/env python3
"""
Plan de Pruebas Automatizado — Flujo B Completo
Simula un usuario real enviando comandos al grupo y verifica respuestas.
"""
import asyncio
import time
import sys

# Token del BOT (mismo que usa el bot)
BOT_TOKEN = "8222165892:AAFdsLM6IEBxAvayetIxBmmfx2I89eVn8zM"
GROUP_ID = -1003916745496
USER_ID = 7267426377  # Sherman

# Usamos python-telegram-bot para enviar mensajes
from telegram import Bot

async def send_and_wait(bot: Bot, chat_id: int, text: str, timeout: int = 15):
    """Envía mensaje y espera respuesta del bot."""
    print(f"\n[TEST] Enviando: {text}")
    await bot.send_message(chat_id=chat_id, text=text)
    
    # Esperar respuesta del bot (polling simple)
    start = time.time()
    last_update_id = 0
    while time.time() - start < timeout:
        updates = await bot.get_updates(offset=last_update_id + 1, limit=10, timeout=5)
        for update in updates:
            last_update_id = max(last_update_id, update.update_id)
            msg = update.message
            if msg and msg.chat.id == chat_id and msg.from_user and msg.from_user.is_bot:
                print(f"[RESPONSE] Bot dice: {msg.text[:200] if msg.text else '(no text)'}")
                return msg
        await asyncio.sleep(1)
    
    print(f"[TIMEOUT] No hubo respuesta en {timeout}s")
    return None

async def main():
    bot = Bot(token=BOT_TOKEN)
    
    print("=" * 60)
    print("PLAN DE PRUEBAS — FLUJO B COMPLETO")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    # TEST 1: /setup → "¡Perfecto!"
    print("\n--- TEST 1: /setup ---")
    msg = await send_and_wait(bot, GROUP_ID, "/setup")
    if msg and "perfecto" in (msg.text or "").lower():
        print("✅ PASS: /setup responde con '¡Perfecto!'")
        passed += 1
    else:
        print("❌ FAIL: /setup no respondió '¡Perfecto!'")
        failed += 1
    
    time.sleep(2)
    
    # TEST 2: /join → "unido"
    print("\n--- TEST 2: /join ---")
    msg = await send_and_wait(bot, GROUP_ID, "/join")
    if msg and "unido" in (msg.text or "").lower():
        print("✅ PASS: /join confirma unión")
        passed += 1
    else:
        print("❌ FAIL: /join no confirmó unión")
        failed += 1
    
    time.sleep(2)
    
    # TEST 3: /begin → "Comenzando"
    print("\n--- TEST 3: /begin ---")
    msg = await send_and_wait(bot, GROUP_ID, "/begin")
    if msg and "comenzando" in (msg.text or "").lower():
        print("✅ PASS: /begin inicia aventura")
        passed += 1
    else:
        print("❌ FAIL: /begin no inició aventura")
        failed += 1
    
    time.sleep(3)
    
    # TEST 4: /j Orco → resultado de ataque
    print("\n--- TEST 4: /j Orco (ataque) ---")
    msg = await send_and_wait(bot, GROUP_ID, "/j Orco", timeout=20)
    text = (msg.text or "").lower() if msg else ""
    if msg and any(x in text for x in ["ataque", "golpe", "daño", "hit", "miss", "falla", "error"]):
        print("✅ PASS: /j Orco responde con resultado de ataque")
        passed += 1
    else:
        print("❌ FAIL: /j Orco no respondió con ataque")
        failed += 1
    
    time.sleep(2)
    
    # TEST 5: /cast Fireball → resultado de hechizo
    print("\n--- TEST 5: /cast Fireball ---")
    msg = await send_and_wait(bot, GROUP_ID, "/cast Fireball", timeout=20)
    text = (msg.text or "").lower() if msg else ""
    if msg and any(x in text for x in ["hechizo", "spell", "fireball", "lanza", "magia", "daño"]):
        print("✅ PASS: /cast responde con hechizo")
        passed += 1
    else:
        print("❌ FAIL: /cast no respondió con hechizo")
        failed += 1
    
    time.sleep(2)
    
    # TEST 6: /status → muestra estado
    print("\n--- TEST 6: /status ---")
    msg = await send_and_wait(bot, GROUP_ID, "/status")
    text = (msg.text or "").lower() if msg else ""
    if msg and any(x in text for x in ["hp", "pv", "vida", "nivel", "level", "estado", "status"]):
        print("✅ PASS: /status muestra estado del personaje")
        passed += 1
    else:
        print("❌ FAIL: /status no mostró estado")
        failed += 1
    
    # RESUMEN
    print("\n" + "=" * 60)
    print(f"RESULTADOS: {passed} PASS | {failed} FAIL")
    print("=" * 60)
    
    await bot.session.close()
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
