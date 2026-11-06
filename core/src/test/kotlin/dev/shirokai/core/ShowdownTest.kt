package dev.shirokai.core

import org.junit.jupiter.api.Test
import kotlin.test.*

class ShowdownTest {
    @Test fun `round trip preserves all editor fields`() {
        val p = PokemonSpec("pikachu", level = 57, shiny = true, nature = "jolly", ability = "static",
            moves = listOf("thunderbolt", "quickattack"), heldItem = "lightball",
            evs = mapOf("attack" to 252, "speed" to 252, "hp" to 6), ivs = mapOf("attack" to 0))
        val parsed = Showdown.parse(Showdown.export(listOf(p))) { it to null }.single()
        assertEquals(p.species, parsed.species)
        assertEquals(p.level, parsed.level)
        assertEquals(p.moves, parsed.moves)
        assertEquals(p.ability, parsed.ability)
        assertEquals(p.heldItem, parsed.heldItem)
        assertEquals(p.nature, parsed.nature)
        assertEquals(p.shiny, parsed.shiny)
        PokemonSpec.STATS.forEach {
            assertEquals(p.evs[it] ?: 0, parsed.evs[it])
            assertEquals(p.ivs[it] ?: 31, parsed.ivs[it])
        }
    }
    @Test fun `invalid teams do not silently coerce values or ignore fields`() {
        listOf("Pikachu\nLevel: 101\n- Tackle", "Pikachu\nEVs: 253 Atk\n- Tackle",
            "Pikachu\nAbility: Static\nAbility: Lightning Rod\n- Tackle", "Pikachu\nUnknown: yes\n- Tackle").forEach {
            assertFails { Showdown.parse(it) { name -> name to null } }
        }
    }
    @Test fun `namespaced items survive export and import`() {
        val p = PokemonSpec(heldItem = "cobblemon:light_ball")
        assertEquals(p.heldItem, Showdown.parse(Showdown.export(listOf(p))) { it to null }.single().heldItem)
    }
}
