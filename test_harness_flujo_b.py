#!/usr/bin/env python3
"""
Test Harness Local — Flujo B Completo
Simula objetos Update/Context y ejecuta handlers directamente sin Telegram API.
"""
import asyncio
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Asegurar que el proyecto esté en el path
sys.path.insert(0, "/home/hermes/hermesdm")

from bot.telegram_handler import (
    ChatState,
    cmd_setup,
    _cmd_approve_setup,
    cmd_join,
    cmd_begin,
    cmd_attack,
    cmd_cast,
    cmd_status,
    cmd_roll,
)
from state.state_manager import load_state, save_state, new_state

GROUP_ID = -1003916745496
USER_ID = 7267426377
USERNAME = "shugar"


def make_update(text: str, args: list[str] | None = None):
    """Crea un mock de Update con message.text y context.args."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.effective_chat.id = GROUP_ID
    update.effective_user.id = USER_ID
    update.effective_user.first_name = USERNAME
    update.effective_user.username = USERNAME
    return update


def make_context(args: list[str] | None = None):
    """Crea un mock de Context con chat_data y bot."""
    context = MagicMock()
    context.args = args or []
    context.chat_data = {"_hermes_state": ChatState()}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot.delete_message = AsyncMock()
    context.bot.send_photo = AsyncMock()
    return context


class TestFlujoB:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log(self, msg: str):
        print(msg)
        self.results.append(msg)

    async def run(self):
        print("=" * 60)
        print("TEST HARNESS — FLUJO B COMPLETO")
        print("=" * 60)

        # Limpieza: eliminar campañas previas de test
        self._cleanup_test_campaigns()

        # --- TEST 1: /setup ---
        await self._test_setup()

        # --- TEST 2: approve setup (/perfecto) ---
        await self._test_approve_setup()

        # --- TEST 3: /join ---
        await self._test_join()

        # --- TEST 4: /begin ---
        await self._test_begin()

        # --- TEST 5: /attack Orco ---
        await self._test_attack()

        # --- TEST 6: /cast Fireball ---
        await self._test_cast()

        # --- TEST 7: /status ---
        await self._test_status()

        # --- RESUMEN ---
        print("\n" + "=" * 60)
        print(f"RESULTADOS: {self.passed} PASS | {self.failed} FAIL")
        print("=" * 60)
        return self.failed == 0

    def _cleanup_test_campaigns(self):
        state_dir = Path.home() / ".hermes" / "hermesdm" / "campaigns"
        if state_dir.exists():
            for d in state_dir.iterdir():
                if d.is_dir() and d.name.startswith("campaign_"):
                    try:
                        import shutil
                        shutil.rmtree(d)
                        print(f"[CLEANUP] Eliminado {d.name}")
                    except Exception as e:
                        print(f"[CLEANUP WARN] {e}")

    async def _test_setup(self):
        print("\n--- TEST 1: /setup ---")
        update = make_update("/setup dark fantasy en un puerto corrupto")
        update.message.reply_text = AsyncMock()
        context = make_context(args=["dark", "fantasy", "en", "un", "puerto", "corrupto"])

        try:
            await cmd_setup(update, context)
            cs: ChatState = context.chat_data["_hermes_state"]

            assert cs.setup_mode == True, "setup_mode debería ser True"
            assert cs.setup_state == "preview", f"setup_state debería ser 'preview', es {cs.setup_state}"
            assert cs.active_campaign is not None, "active_campaign no debería ser None"
            assert cs.pending_setup is not None, "pending_setup no debería ser None"

            # Verificar en disco
            st = load_state(cs.active_campaign)
            assert st is not None, "state no debería ser None"
            assert "setup" in st, "state debería tener 'setup'"

            print("✅ PASS: /setup crea campaña y entra en modo preview")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: /setup - {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ FAIL: /setup - Exception: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1

    async def _test_approve_setup(self):
        print("\n--- TEST 2: /perfecto (approve setup) ---")
        # Reusar el context del test anterior... necesitamos obtenerlo
        # Creamos de nuevo el flujo
        update = make_update("/setup dark fantasy en un puerto corrupto")
        context = make_context(args=["dark", "fantasy", "en", "un", "puerto", "corrupto"])
        await cmd_setup(update, context)
        cs: ChatState = context.chat_data["_hermes_state"]
        campaign_id = cs.active_campaign

        # Ahora aprobar
        update2 = make_update("/perfecto")
        try:
            await _cmd_approve_setup(update2, context)

            st = load_state(campaign_id)
            assert st["campaign"]["status"] == "active", f"status debería ser 'active', es {st['campaign']['status']}"
            assert st["setup"].get("approved") == True, "setup debería estar approved"

            print("✅ PASS: /perfecto aprueba setup y activa campaña")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: /perfecto - {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ FAIL: /perfecto - Exception: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1

    async def _test_join(self):
        print("\n--- TEST 3: /join ---")
        # Setup + approve primero
        update = make_update("/setup dark fantasy")
        context = make_context(args=["dark", "fantasy"])
        await cmd_setup(update, context)
        await _cmd_approve_setup(make_update("/perfecto"), context)
        cs: ChatState = context.chat_data["_hermes_state"]
        campaign_id = cs.active_campaign

        update_join = make_update("/join Valdric fighter 3")
        update_join.effective_user.id = USER_ID
        update_join.effective_user.first_name = USERNAME
        context_join = make_context(args=["Valdric", "fighter", "3"])
        context_join.chat_data = context.chat_data  # mismo chat_data

        try:
            await cmd_join(update_join, context_join)
            cs = context_join.chat_data["_hermes_state"]

            assert "valdric" in cs.characters, "valdric debería estar en characters"
            assert cs.telegram_characters.get(USER_ID) == "valdric", "telegram_characters debería mapear user_id -> valdric"

            # Verificar en disco
            st = load_state(campaign_id)
            chars = st.get("characters", {})
            assert "valdric" in chars, "valdric debería persistir en state"

            print("✅ PASS: /join registra personaje y persiste")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: /join - {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ FAIL: /join - Exception: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1

    async def _test_begin(self):
        print("\n--- TEST 4: /begin ---")
        # Setup completo previo
        update = make_update("/setup dark fantasy")
        context = make_context(args=["dark", "fantasy"])
        await cmd_setup(update, context)
        await _cmd_approve_setup(make_update("/perfecto"), context)

        update_join = make_update("/join Valdric fighter 3")
        context_join = make_context(args=["Valdric", "fighter", "3"])
        context_join.chat_data = context.chat_data
        await cmd_join(update_join, context_join)

        cs: ChatState = context.chat_data["_hermes_state"]
        campaign_id = cs.active_campaign

        update_begin = make_update("/begin")
        try:
            await cmd_begin(update_begin, context)
            st = load_state(campaign_id)

            assert st.get("adventure_started") == True, "adventure_started debería ser True"
            assert len(st.get("scenes", [])) > 0, "debería haber al menos una escena"

            print("✅ PASS: /begin inicia aventura y genera escena")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: /begin - {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ FAIL: /begin - Exception: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1

    async def _test_attack(self):
        print("\n--- TEST 5: /attack Orco ---")
        # Setup completo
        update = make_update("/setup dark fantasy")
        context = make_context(args=["dark", "fantasy"])
        await cmd_setup(update, context)
        await _cmd_approve_setup(make_update("/perfecto"), context)

        update_join = make_update("/join Valdric fighter 3")
        context_join = make_context(args=["Valdric", "fighter", "3"])
        context_join.chat_data = context.chat_data
        await cmd_join(update_join, context_join)
        await cmd_begin(make_update("/begin"), context)

        update_attack = make_update("/attack Orco")
        context_attack = make_context(args=["Orco"])
        context_attack.chat_data = context.chat_data

        try:
            await cmd_attack(update_attack, context_attack)
            cs: ChatState = context_attack.chat_data["_hermes_state"]

            assert len(cs.pending_attacks) > 0, "debería haber pending_attacks"
            attack = list(cs.pending_attacks.values())[0]
            assert attack["defender_name"] == "Orco", "defender debería ser Orco"

            print("✅ PASS: /attack Orco encola ataque")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: /attack - {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ FAIL: /attack - Exception: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1

    async def _test_cast(self):
        print("\n--- TEST 6: /cast Fireball ---")
        # Setup completo
        update = make_update("/setup dark fantasy")
        context = make_context(args=["dark", "fantasy"])
        await cmd_setup(update, context)
        await _cmd_approve_setup(make_update("/perfecto"), context)

        # Join con wizard para que tenga hechizos
        update_join = make_update("/join Gandalf wizard 5")
        context_join = make_context(args=["Gandalf", "wizard", "5"])
        context_join.chat_data = context.chat_data
        await cmd_join(update_join, context_join)
        await cmd_begin(make_update("/begin"), context)

        update_cast = make_update("/cast Fireball")
        context_cast = make_context(args=["Fireball"])
        context_cast.chat_data = context.chat_data

        try:
            await cmd_cast(update_cast, context_cast)
            # cmd_cast consume el hechizo inmediatamente (no pending)
            # Verificamos que no haya excepción y que el bot respondió
            assert update_cast.message.reply_text.called, "reply_text debería haber sido llamado"

            print("✅ PASS: /cast Fireball resuelve hechizo")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: /cast - {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ FAIL: /cast - Exception: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1

    async def _test_status(self):
        print("\n--- TEST 7: /status ---")
        update = make_update("/setup dark fantasy")
        context = make_context(args=["dark", "fantasy"])
        await cmd_setup(update, context)
        await _cmd_approve_setup(make_update("/perfecto"), context)

        update_join = make_update("/join Valdric fighter 3")
        context_join = make_context(args=["Valdric", "fighter", "3"])
        context_join.chat_data = context.chat_data
        await cmd_join(update_join, context_join)

        update_status = make_update("/status")
        context_status = make_context()
        context_status.chat_data = context.chat_data

        try:
            await cmd_status(update_status, context_status)
            assert update_status.message.reply_text.called, "reply_text debería haber sido llamado"
            call_args = update_status.message.reply_text.call_args[0][0]
            assert "Valdric" in call_args, "status debería mencionar a Valdric"

            print("✅ PASS: /status muestra estado del party")
            self.passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: /status - {e}")
            self.failed += 1
        except Exception as e:
            print(f"❌ FAIL: /status - Exception: {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1


if __name__ == "__main__":
    harness = TestFlujoB()
    success = asyncio.run(harness.run())
    sys.exit(0 if success else 1)
