package dev.shirokai.smoke

import com.cobblemon.mod.common.api.battles.model.PokemonBattle
import com.cobblemon.mod.common.battles.*
import com.cobblemon.mod.common.battles.actor.TrainerBattleActor
import com.cobblemon.mod.common.battles.ai.StrongBattleAI
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon
import dev.shirokai.core.PokemonSpec
import dev.shirokai.fabric.EntityTrainerBattleActor
import dev.shirokai.fabric.PokemonAdapter
import net.fabricmc.api.ModInitializer
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents
import net.minecraft.server.MinecraftServer
import net.minecraft.server.level.ServerLevel
import net.minecraft.world.level.levelgen.Heightmap
import net.minecraft.world.phys.Vec3
import java.nio.file.Files
import java.nio.file.Path
import java.util.UUID

/** Runs real Showdown + send-out instructions without claiming to test the client's battle UI. */
class BattleSmokeTest : ModInitializer {
    private lateinit var server: MinecraftServer
    private lateinit var level: ServerLevel
    private var battle: PokemonBattle? = null
    private var actors = listOf<TrainerBattleActor>()
    private var ticks = 0
    private var stage = 0
    private var legacyMissing = false
    private var spawnedBoth = false
    private var finished = false
    private val decisions = linkedSetOf<DeferredActor>()
    private inner class DeferredActor(team: List<BattlePokemon>, name: String, position: Vec3) : EntityTrainerBattleActor(
        name, team, 5, EntityTrainerBattleActor.anchor(level, position), true
    ) {
        // Real players choose after battle.turn marks both sides. Two immediate AIs can race
        // Cobblemon's input dispatch; defer only the test bots to the end of that server tick.
        override fun onChoiceRequested() { decisions.add(this) }
        fun chooseNow() = super.onChoiceRequested()
    }

    override fun onInitialize() {
        Files.deleteIfExists(Path.of("battle-smoke-result.json"))
        ServerLifecycleEvents.SERVER_STARTED.register { s ->
            server = s
            level = s.allLevels.first { it.dimension().location().toString() == "minecraft:overworld" }
            level.setChunkForced(0, 0, true)
        }
        ServerTickEvents.END_SERVER_TICK.register {
            if (!::level.isInitialized || finished) return@register
            try {
                val queued = decisions.toList(); decisions.clear()
                queued.filter { it.mustChoose && it.request != null && !it.battle.ended }.forEach { it.chooseNow() }
                ticks++
                when (stage) {
                    0 -> if (ticks >= 20) { launch(legacy = true); stage = 1; ticks = 0 }
                    1 -> if (ticks >= 160) {
                        legacyMissing = actors[1].activePokemon.all { it.battlePokemon == null }
                        check(legacyMissing) { "Legacy regression was not reproduced" }
                        battle?.end(); cleanup()
                        launch(legacy = false); stage = 2; ticks = 0
                    }
                    2 -> {
                        val b = battle ?: error("Battle absent")
                        if (actors.all { it.activePokemon.any { slot -> slot.battlePokemon?.entity?.isAlive == true } }) spawnedBoth = true
                        if (b.ended) {
                            check(spawnedBoth && b.started && b.winners.isNotEmpty()) { "Fixed battle ended without both send-outs and a winner" }
                            finish(true, "Both Pokemon spawned; real AI battle completed with a winner")
                        } else if (ticks > 1200) error("Fixed battle timed out: started=${b.started}, turn=${b.turn}, spawnedBoth=$spawnedBoth")
                    }
                }
            } catch (e: Exception) { finish(false, e.toString()) }
        }
    }
    private fun launch(legacy: Boolean) {
        val y = level.getHeight(Heightmap.Types.MOTION_BLOCKING, 0, 0).toDouble() + 1
        fun team(level: Int) = listOf(BattlePokemon.safeCopyOf(PokemonAdapter.create(
            PokemonSpec(species = "geodude", level = level, moves = listOf("tackle")))))
        val a = DeferredActor(team(5), "Smoke A", Vec3(0.5, y, 0.5))
        val b = if (legacy) TrainerBattleActor("Legacy", UUID.randomUUID(), team(50), StrongBattleAI(5))
            else DeferredActor(team(50), "Smoke B", Vec3(8.5, y, 0.5))
        actors = listOf(a, b)
        BattleRegistry.startBattle(BattleFormat.GEN_9_SINGLES.copy(), BattleSide(a), BattleSide(b))
            .ifSuccessful { battle = it }.ifErrored { error("Battle refused: $it") }
    }
    private fun cleanup() {
        actors.forEach { if (it is EntityTrainerBattleActor) it.cleanup() else it.pokemonList.forEach { p -> p.effectedPokemon.recall() } }
    }
    private fun finish(success: Boolean, message: String) {
        finished = true
        runCatching { if (battle?.ended == false) battle?.end(); cleanup() }
        val json = com.google.gson.JsonObject().apply {
            addProperty("success", success); addProperty("legacyMissingOpponent", legacyMissing)
            addProperty("fixedSpawnedBoth", spawnedBoth); addProperty("message", message)
        }
        Files.writeString(Path.of("battle-smoke-result.json"), json.toString())
        println("SHIROKAI_BATTLE_SMOKE: $json")
        server.halt(false)
    }
}
