"""
dm/action_narrator.py — Narrative generation for player actions using LLM.

Provides ActionNarrator which connects to the LLM via provider_client
to generate contextual descriptions for combat, spells, skills, and NPC dialogue.

All prompts and responses are automatically logged via provider_client.
"""
from __future__ import annotations

from typing import Any

from dm.provider_client import LLMClient, get_provider


class ActionNarrator:
    """Generates narrative descriptions for D&D actions using an LLM."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        if llm_client is None:
            try:
                llm_client = get_provider("minimax")
            except Exception:
                llm_client = None
        self.llm = llm_client

    # ------------------------------------------------------------------ #
    # Combat narration
    # ------------------------------------------------------------------ #

    def narrate_attack(
        self,
        *,
        attacker: str,
        defender: str,
        weapon: str,
        attack_roll: int,
        hit: bool,
        damage: int | None = None,
        critical: bool = False,
        location: str = "",
        context: str = "",
    ) -> str | None:
        """Generate narrative for an attack resolution.

        Returns None if LLM unavailable or if the result is not noteworthy
        (e.g. a normal miss with no context).
        """
        if self.llm is None:
            return None

        # Skip narrating trivial misses
        if not hit and not critical and damage is None:
            return None

        prompt = self._build_attack_prompt(
            attacker=attacker,
            defender=defender,
            weapon=weapon,
            attack_roll=attack_roll,
            hit=hit,
            damage=damage,
            critical=critical,
            location=location,
            context=context,
        )

        result = self.llm.text(
            prompt=prompt,
            system=(
                "Eres un narrador de D&D 5e. Escribes en español, en segunda persona, "
                "2-4 oraciones, sin preguntas. Estilo cinematográfico, visceral. "
                "Solo narras la acción, no das instrucciones de juego."
            ),
            max_tokens=200,
            temperature=0.85,
        )
        return result.text.strip() if result.text else None

    def _build_attack_prompt(
        self,
        *,
        attacker: str,
        defender: str,
        weapon: str,
        attack_roll: int,
        hit: bool,
        damage: int | None,
        critical: bool,
        location: str,
        context: str,
    ) -> str:
        parts = [
            f"Atacante: {attacker}",
            f"Defensor: {defender}",
            f"Arma: {weapon}",
            f"Tirada de ataque: {attack_roll}",
        ]
        if critical:
            parts.append("Resultado: CRÍTICO")
        elif hit:
            parts.append(f"Resultado: IMPACTO por {damage} de daño")
        else:
            parts.append("Resultado: FALLO")
        if location:
            parts.append(f"Ubicación: {location}")
        if context:
            parts.append(f"Contexto: {context}")

        parts.append("\nNarra este momento de combate en 2-4 oraciones, en español, segunda persona.")
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # Spell narration
    # ------------------------------------------------------------------ #

    def narrate_spell(
        self,
        *,
        caster: str,
        spell_name: str,
        target: str,
        effect_description: str,
        damage: int | None = None,
        saved: bool | None = None,
        location: str = "",
    ) -> str | None:
        """Generate narrative for a spell being cast."""
        if self.llm is None:
            return None

        prompt = self._build_spell_prompt(
            caster=caster,
            spell_name=spell_name,
            target=target,
            effect_description=effect_description,
            damage=damage,
            saved=saved,
            location=location,
        )

        result = self.llm.text(
            prompt=prompt,
            system=(
                "Eres un narrador de D&D 5e. Escribes en español, en tercera persona, "
                "2-4 oraciones, sin preguntas. Estilo mágico y cinematográfico. "
                "Describe la manifestación visual del hechizo."
            ),
            max_tokens=200,
            temperature=0.85,
        )
        return result.text.strip() if result.text else None

    def _build_spell_prompt(
        self,
        *,
        caster: str,
        spell_name: str,
        target: str,
        effect_description: str,
        damage: int | None,
        saved: bool | None,
        location: str,
    ) -> str:
        parts = [
            f"Lanzador: {caster}",
            f"Hechizo: {spell_name}",
            f"Objetivo: {target}",
            f"Efecto: {effect_description}",
        ]
        if damage is not None:
            parts.append(f"Daño: {damage}")
        if saved is not None:
            parts.append(f"Salvación: {'éxito (mitigado)' if saved else 'fallo'}")
        if location:
            parts.append(f"Ubicación: {location}")

        parts.append("\nNarra la manifestación visual de este hechizo en 2-4 oraciones, en español, tercera persona.")
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # Skill check narration
    # ------------------------------------------------------------------ #

    def narrate_skill(
        self,
        *,
        character: str,
        skill: str,
        dc: int,
        roll_total: int,
        success: bool,
        margin: int,
        location: str = "",
    ) -> str | None:
        """Generate narrative for a skill check resolution."""
        if self.llm is None:
            return None

        # Skip trivial failures with no margin info
        if not success and margin < -5:
            return None

        prompt = self._build_skill_prompt(
            character=character,
            skill=skill,
            dc=dc,
            roll_total=roll_total,
            success=success,
            margin=margin,
            location=location,
        )

        result = self.llm.text(
            prompt=prompt,
            system=(
                "Eres un narrador de D&D 5e. Escribes en español, en segunda persona, "
                "1-3 oraciones, sin preguntas. Enfocate en cómo el personaje intentó "
                "la acción y qué resultado tuvo."
            ),
            max_tokens=150,
            temperature=0.8,
        )
        return result.text.strip() if result.text else None

    def _build_skill_prompt(
        self,
        *,
        character: str,
        skill: str,
        dc: int,
        roll_total: int,
        success: bool,
        margin: int,
        location: str,
    ) -> str:
        parts = [
            f"Personaje: {character}",
            f"Habilidad: {skill}",
            f"DC: {dc}",
            f"Resultado: {roll_total} ({'éxito' if success else 'fallo'} por {margin:+d})",
        ]
        if location:
            parts.append(f"Ubicación: {location}")

        parts.append("\nNarra este intento de habilidad en 1-3 oraciones, en español, segunda persona.")
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    # NPC dialogue
    # ------------------------------------------------------------------ #

    def narrate_npc_response(
        self,
        *,
        npc_name: str,
        npc_role: str,
        npc_personality: str,
        npc_memory: list[str],
        npc_secrets: list[str],
        disposition: int,
        player_name: str,
        player_message: str,
        location: str = "",
        recent_history: list[str] | None = None,
    ) -> str | None:
        """Generate an NPC response using LLM with full context.

        Returns None if LLM unavailable.
        """
        if self.llm is None:
            return None

        prompt = self._build_npc_prompt(
            npc_name=npc_name,
            npc_role=npc_role,
            npc_personality=npc_personality,
            npc_memory=npc_memory,
            npc_secrets=npc_secrets,
            disposition=disposition,
            player_name=player_name,
            player_message=player_message,
            location=location,
            recent_history=recent_history,
        )

        result = self.llm.text(
            prompt=prompt,
            system=(
                "Eres un personaje NPC en una campaña de D&D 5e. "
                "Respondes EN PRIMERA PERSONA como el NPC. "
                "Usas tu personalidad, secretos (si son relevantes) y memoria. "
                "Máximo 3-4 oraciones. En español. No rompas personaje. "
                "No digas 'como NPC' ni nada metajuego."
            ),
            max_tokens=250,
            temperature=0.85,
        )
        return result.text.strip() if result.text else None

    def _build_npc_prompt(
        self,
        *,
        npc_name: str,
        npc_role: str,
        npc_personality: str,
        npc_memory: list[str],
        npc_secrets: list[str],
        disposition: int,
        player_name: str,
        player_message: str,
        location: str,
        recent_history: list[str] | None,
    ) -> str:
        lines = [
            f"Tu nombre: {npc_name}",
            f"Tu rol: {npc_role}",
            f"Tu personalidad: {npc_personality}",
            f"Disposición hacia {player_name}: {disposition}/100 ({'amigable' if disposition > 50 else 'hostil' if disposition < -50 else 'neutral'})",
        ]

        if location:
            lines.append(f"Ubicación actual: {location}")

        if npc_memory:
            lines.append("\nMemorias que tienes sobre este personaje y eventos:")
            for mem in npc_memory[-5:]:
                lines.append(f"- {mem}")

        if npc_secrets:
            lines.append("\nSecretos que conoces (solo revela si es natural para la conversación):")
            for sec in npc_secrets[:2]:
                lines.append(f"- {sec}")

        if recent_history:
            lines.append("\nEventos recientes de la campaña:")
            for evt in recent_history[-3:]:
                lines.append(f"- {evt}")

        lines.append(
            f"\n{player_name} te dice: \"{player_message}\""
            f"\n\nResponde como {npc_name}, en primera persona, máximo 3-4 oraciones."
        )

        return "\n".join(lines)


# ── Singleton ─────────────────────────────────────────────────────────────────

_narrator: ActionNarrator | None = None


def get_narrator() -> ActionNarrator:
    """Return the global ActionNarrator instance."""
    global _narrator
    if _narrator is None:
        _narrator = ActionNarrator()
    return _narrator
