"""
Tests para SPEC-GENRE-FREE: genre validation eliminada.

Estos tests verifican que cualquier género inventado por el usuario
funciona sin necesidad de keyword matching.

Cubre el fix del bug:
  "samurais en Japón feudal" → ValueError("Genre validation failed...")
"""
import pytest
from unittest import mock


class TestGenreFreeGeneration:
    """El sistema debe funcionar con cualquier género sin validar keywords."""

    def test_samurai_input_does_not_raise_genre_error(self):
        """
        Bug original: /setup samurais en el Japón feudal
        fallaba con: ValueError("Genre validation failed for 'fantasy': ...")

        Después del fix: debe retornar setup válido, sin error de genre.
        """
        with mock.patch("os.getenv", return_value="fake_key"):
            with mock.patch("dm.provider_client.MiniMaxProvider") as MockProvider:
                mock_instance = mock.MagicMock()
                mock_instance.text.return_value = mock.MagicMock(
                    text='{"premise": "En el Japón feudal, samuráis buscan venganza...", "hook": "...", "starting_location": "Castillo Himeji", "starting_location_desc": "...", "main_threat": "El Shogun traidor", "factions": {"Clan Oni": "DOMINANT"}, "npcs": [{"name": "Kira", "role": "Ronin", "dialogue": "Lakatoshi..."}], "classes": ["Samurai", "Monje", "Ashigaru"], "starting_equipment": [{"name": "Katana", "description": "Espada curva", "is_consumable": false}], "story_arc": {"pacing_level": "medium", "milestones": [{"id": "hook", "type": "hook", "description": "Los samuráis descubren la traición del Shogun y deben huir del Castillo Himeji..."}]}}'
                )
                MockProvider.return_value = mock_instance

                # Import here to avoid stale cache
                from dm.world_builder import generate_setup_with_ai
                result = generate_setup_with_ai("samurais en el Japón feudal")

                # Should NOT raise ValueError("Genre validation failed...")
                assert result is not None
                assert "premise" in result
                assert "lore" in result
                assert "hook" in result

    def test_werewolf_input_does_not_raise_genre_error(self):
        """Hombres lobo no estaban en keywords — ahora debe funcionar."""
        with mock.patch("os.getenv", return_value="fake_key"):
            with mock.patch("dm.provider_client.MiniMaxProvider") as MockProvider:
                mock_instance = mock.MagicMock()
                mock_instance.text.return_value = mock.MagicMock(
                    text='{"premise": "En Transilvania, los licántropos atacan...", "hook": "...", "starting_location": "Pueblo de Braila", "starting_location_desc": "...", "main_threat": "La manada de hombres lobo", "factions": {"Cazadores": "RISING"}, "npcs": [{"name": "Dracu", "role": "Cazador", "dialogue": "Solo la plata puede detenerlos..."}], "classes": ["Licántropo", "Cazador", "Brujo"], "starting_equipment": [{"name": "Daga de plata", "description": "Arma contra licántropos", "is_consumable": false}], "story_arc": {"pacing_level": "medium", "milestones": [{"id": "hook", "type": "hook", "description": "Los hombres lobo atacan el pueblo..."}]}}'
                )
                MockProvider.return_value = mock_instance

                from dm.world_builder import generate_setup_with_ai
                result = generate_setup_with_ai("hombres lobo en Transilvania")

                assert result is not None
                assert "premise" in result

    def test_pirates_input_does_not_raise_genre_error(self):
        """Piratas funcionaban por luck (codigo estaba en keywords), pero el fix los mejora."""
        with mock.patch("os.getenv", return_value="fake_key"):
            with mock.patch("dm.provider_client.MiniMaxProvider") as MockProvider:
                mock_instance = mock.MagicMock()
                mock_instance.text.return_value = mock.MagicMock(
                    text='{"premise": "Corsarios del Mar del Diablo buscan el tesoro maldito...", "hook": "...", "starting_location": "Isla Tortuga", "starting_location_desc": "...", "main_threat": "La Flota del Almirante Negro", "factions": {"Hermandad de la Costa": "DOMINANT"}, "npcs": [{"name": "Barbarroja", "role": "Capitán pirata", "dialogue": "El tesoro es mío..."}], "classes": ["Pirata", "Navegante", "Espadachín"], "starting_equipment": [{"name": "Espada pirate", "description": "Sable curveado", "is_consumable": false}], "story_arc": {"pacing_level": "medium", "milestones": [{"id": "hook", "type": "hook", "description": "Los piratas descubren el mapa del tesoro..."}]}}'
                )
                MockProvider.return_value = mock_instance

                from dm.world_builder import generate_setup_with_ai
                result = generate_setup_with_ai("piratas buscando tesoro en el caribe")

                assert result is not None
                assert "premise" in result

    def test_custom_genre_invented_by_user(self):
        """Género inventado debe funcionar sin error."""
        with mock.patch("os.getenv", return_value="fake_key"):
            with mock.patch("dm.provider_client.MiniMaxProvider") as MockProvider:
                mock_instance = mock.MagicMock()
                mock_instance.text.return_value = mock.MagicMock(
                    text='{"premise": "Espías victorianos en el Londres de 1888...", "hook": "...", "starting_location": "Baker Street", "starting_location_desc": "...", "main_threat": "El Espía del Imperio", "factions": {"MI6": "RISING"}, "npcs": [{"name": "M", "role": "Jefe de espías", "dialogue": "El juego comienza..."}], "classes": ["Espía", "Detective", "Noble"], "starting_equipment": [{"name": "Pistola de duelo", "description": "Sencilla y letal", "is_consumable": false}], "story_arc": {"pacing_level": "medium", "milestones": [{"id": "hook", "type": "hook", "description": "Los espías descubren la conspiración..."}]}}'
                )
                MockProvider.return_value = mock_instance

                from dm.world_builder import generate_setup_with_ai
                result = generate_setup_with_ai("espías victorianos en el Londres de Jack el Destripador")

                assert result is not None
                assert "premise" in result

    def test_ninja_input_does_not_raise_genre_error(self):
        """Ninjas tampoco estaban en keywords — ahora debe funcionar."""
        with mock.patch("os.getenv", return_value="fake_key"):
            with mock.patch("dm.provider_client.MiniMaxProvider") as MockProvider:
                mock_instance = mock.MagicMock()
                mock_instance.text.return_value = mock.MagicMock(
                    text='{"premise": "Ninjas del Clan Kaguya ejecutan misiones de espionaje...", "hook": "...", "starting_location": "Aldea Konoha", "starting_location_desc": "...", "main_threat": "El Clan Otomo", "factions": {"Clan Kaguya": "DOMINANT"}, "npcs": [{"name": "Hidan", "role": "Ninja asesino", "dialogue": "No sientes dolor..."}], "classes": ["Ninja", "Samurai", "Monje"], "starting_equipment": [{"name": "Shuriken", "description": "Estrella arrojadiza", "is_consumable": true}], "story_arc": {"pacing_level": "medium", "milestones": [{"id": "hook", "type": "hook", "description": "Los ninjas reciben su primera misión..."}]}}'
                )
                MockProvider.return_value = mock_instance

                from dm.world_builder import generate_setup_with_ai
                result = generate_setup_with_ai("ninja clan en el Japón feudal")

                assert result is not None
                assert "premise" in result

    def test_samurai_fallback_also_works(self):
        """
        Cuando la API está down, el fallback genera contenido genérico.
        No debe fallar con genre validation error aunque el fallback
        genere contenido que no tiene keywords de fantasy.
        """
        with mock.patch("os.getenv", return_value="fake_key"):
            with mock.patch("dm.provider_client.MiniMaxProvider") as MockProvider:
                # API down
                MockProvider.side_effect = Exception("API down")

                from dm.world_builder import generate_setup_with_ai
                result = generate_setup_with_ai("samurais en el Japón feudal")

                # Should NOT raise ValueError("Genre validation failed...")
                assert result is not None
                assert "premise" in result
                # Fallback genera algo — puede ser genérico, pero no crashea
