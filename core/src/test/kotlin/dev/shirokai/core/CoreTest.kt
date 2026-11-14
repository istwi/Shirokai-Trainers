package dev.shirokai.core

import org.junit.jupiter.api.Test
import org.junit.jupiter.api.io.TempDir
import java.nio.file.Files
import java.nio.file.Path
import java.util.UUID
import kotlin.random.Random
import kotlin.test.*

class CoreTest {
    @TempDir lateinit var dir: Path
    private fun context(p: PlayerProgress) = PlayerContext(p.uuid, "Ash", p, emptyMap(), 0) { false }
    private fun session(player: UUID, groups: List<RewardGroup> = emptyList(), simultaneous: Boolean = true): BattleSession {
        val d = Difficulty(team = listOf(PokemonSpec()), winRewards = groups)
        return BattleSession(UUID.randomUUID(), player, Trainer("brock", simultaneous = simultaneous, difficulties = listOf(d)), d, 1000)
    }

    @Test fun `invalid pokemon values and EV totals are rejected`() {
        assertFailsWith<IllegalArgumentException> { PokemonSpec(level = 101).validate() }
        assertFailsWith<IllegalArgumentException> { PokemonSpec(ivs = mapOf("hp" to 32)).validate() }
        assertFailsWith<IllegalArgumentException> { PokemonSpec(evs = mapOf("hp" to 252, "attack" to 252, "speed" to 7)).validate() }
        PokemonSpec().validate()
    }

    @Test fun `independent chance has exact zero and hundred boundaries`() {
        val r = Reward("always", RewardKind.ITEM, "minecraft:stone")
        val group = RewardGroup("win", rewards = listOf(r, r.copy(id = "never", chance = 0.0)))
        val p = PlayerProgress(UUID.randomUUID())
        val s = session(p.uuid, listOf(group))
        repeat(100) {
            assertEquals(listOf("always"), RewardEngine(Random(it)).select(s, Outcome.WIN, context(p), 1000).map { it.reward.id })
        }
    }

    @Test fun `weighted group selects one and uses weight rather than percent`() {
        val p = PlayerProgress(UUID.randomUUID())
        val a = Reward("a", RewardKind.ITEM, "minecraft:stone", chance = 0.0, weight = 1.0)
        val b = a.copy(id = "b", weight = 3.0)
        val s = session(p.uuid, listOf(RewardGroup("weighted", GroupMode.WEIGHTED_ONE, listOf(a, b))))
        val engine = RewardEngine(Random(42))
        val results = List(10000) { engine.select(s, Outcome.WIN, context(p), 1000).single().reward.id }
        assertTrue(results.count { it == "b" } in 7250..7750)
    }

    @Test fun `first win cooldown permission and limits gate rewards`() {
        val p = PlayerProgress(UUID.randomUUID())
        val r = Reward("a", RewardKind.ITEM, "minecraft:stone", first_win_only = true)
        val s = session(p.uuid, listOf(RewardGroup("win", rewards = listOf(r))))
        val engine = RewardEngine(Random(1))
        assertEquals(1, engine.select(s, Outcome.WIN, context(p), 1000).size)
        assertTrue(engine.select(s, Outcome.LOSS, context(p), 1000).isEmpty())
        p.trainers["brock"] = TrainerProgress(wins = 1)
        assertTrue(engine.select(s, Outcome.WIN, context(p), 1000).isEmpty())
        p.trainers.clear()
        p.claims["brock/normal/win/a"] = Claim(1, 1000)
        fun eligible(reward: Reward, now: Long = 2000) = engine.select(
            s.copy(difficulty = s.difficulty.copy(winRewards = listOf(RewardGroup("win", rewards = listOf(reward))))),
            Outcome.WIN, context(p), now)
        assertTrue(eligible(r.copy(repeatable = false)).isEmpty())
        assertTrue(eligible(r.copy(max_claims_per_player = 1)).isEmpty())
        assertTrue(eligible(r.copy(cooldown_seconds = 60)).isEmpty())
        assertEquals(1, eligible(r.copy(cooldown_seconds = 60), 61000).size)
        assertTrue(eligible(r.copy(required_permission = "test.reward")).isEmpty())
    }

    @Test fun `simultaneous sessions are independent and duplicate results do not duplicate rewards`() {
        val store = JsonStore(dir)
        val ledger = BattleLedger(store)
        val p = PlayerProgress(UUID.randomUUID())
        val q = PlayerProgress(UUID.randomUUID())
        val s = session(p.uuid, listOf(RewardGroup("win", rewards = listOf(Reward("a", RewardKind.ITEM, "minecraft:stone")))))
        val t = session(q.uuid)
        ledger.reserve(s); ledger.reserve(t)
        ledger.finish(s.id, Outcome.WIN, context(p), 2000)
        assertEquals(1, p.trainers["brock"]?.wins)
        assertEquals(1, p.deliveries.size)
        assertNull(q.trainers["brock"])
        assertTrue(t.id in ledger.sessions)
        // Simulates a replay after recovery, with an existing completion marker on disk.
        ledger.reserve(s.copy(outcome = null))
        ledger.finish(s.id, Outcome.WIN, context(p), 3000)
        assertEquals(1, p.trainers["brock"]?.wins)
        assertEquals(1, p.deliveries.size)
        var grants = 0
        ledger.deliver(p, { grants++ }, { _, _ -> })
        ledger.deliver(p, { grants++ }, { _, _ -> })
        assertEquals(1, grants)
        assertEquals(DeliveryState.DELIVERED, store.loadPlayer(p.uuid).deliveries.values.single().state)
    }

    @Test fun `exclusive trainer rejects second player and same player cannot reserve twice`() {
        val ledger = BattleLedger(JsonStore(dir))
        val s = session(UUID.randomUUID(), simultaneous = false)
        ledger.reserve(s)
        assertFails { ledger.reserve(session(UUID.randomUUID(), simultaneous = false)) }
        assertFails { ledger.reserve(session(s.player)) }
    }

    @Test fun `uncertain delivery is never retried automatically`() {
        val store = JsonStore(dir)
        val ledger = BattleLedger(store)
        val p = PlayerProgress(UUID.randomUUID())
        val s = session(p.uuid, listOf(RewardGroup("win", rewards = listOf(Reward("a", RewardKind.COMMAND, "say hello")))))
        ledger.reserve(s); ledger.finish(s.id, Outcome.WIN, context(p), 2000)
        var attempts = 0
        ledger.deliver(p, { attempts++; error("delivery interrupted") }, { _, _ -> })
        ledger.deliver(p, { attempts++ }, { _, _ -> })
        assertEquals(1, attempts)
        assertEquals(DeliveryState.NEEDS_REVIEW, store.loadPlayer(p.uuid).deliveries.values.single().state)
    }

    @Test fun `reset is per UUID and preserves other players plus backups`() {
        val store = JsonStore(dir)
        val a = PlayerProgress(UUID.randomUUID(), objectives = mutableSetOf("a"))
        val b = PlayerProgress(UUID.randomUUID(), objectives = mutableSetOf("b"))
        store.savePlayer(a); store.savePlayer(b)
        store.resetPlayer(a.uuid)
        assertTrue(store.loadPlayer(a.uuid).objectives.isEmpty())
        assertEquals(setOf("b"), store.loadPlayer(b.uuid).objectives)
        assertTrue(Files.exists(store.playerPath(a.uuid).resolveSibling("${a.uuid}.json.bak")))
    }

    @Test fun `corrupt JSON is preserved and previous valid backup is recoverable`() {
        val store = JsonStore(dir)
        val t = Trainer("brock")
        store.saveTrainer(t); store.saveTrainer(t.copy(name = "Brock"))
        val path = store.trainerPath(t.id)
        Files.writeString(path, "{broken")
        assertEquals("brock", store.loadTrainers().getValue("brock").name)
        assertEquals("{broken", Files.readString(path))
    }

    @Test fun `command templates reject unsafe interpolation and control characters`() {
        val id = UUID.randomUUID()
        assertEquals("give Ash minecraft:stone", CommandTemplate.render("give %player% minecraft:stone", "Ash", id, "brock", "Brock", id))
        listOf("op %unknown%", "say hi\nop Ash", "execute as @a run say %player%evil", "%player% hi", "say %player").forEach {
            assertFailsWith<IllegalArgumentException>(it) { CommandTemplate.validate(it) }
        }
        assertFails { CommandTemplate.render("say %player%", "Ash\nop Bob", id, "brock", "Brock", id) }
        assertFails { CommandTemplate.render("say %trainer_name%", "Ash", id, "brock", "Brock\" run op @a", id) }
    }

    @Test fun `strict JSON rejects comments duplicate fields trailing documents and NaN`() {
        listOf("{a:1}", "{\"a\":1,\"a\":2}", "{} {}", "{\"a\":NaN}", "{/* comment */}", "{\"a\":1,}").forEach {
            assertFails(it) { StrictJson.parse(it) }
        }
        assertTrue(StrictJson.parse("{\"a\": [1, true, null, \"text\"]}").isJsonObject)
    }

    @Test fun `durable result recovers the exact original draw once after interruption`() {
        val store = JsonStore(dir)
        val p = PlayerProgress(UUID.randomUUID())
        val s = session(p.uuid, listOf(RewardGroup("win", rewards = listOf(Reward("a", RewardKind.ITEM, "minecraft:stone")))))
        val ledger = BattleLedger(store)
        ledger.reserve(s)
        val selected = RewardEngine(Random(12)).select(s, Outcome.WIN, context(p), 2000)
        store.write(store.resolutionPath(s.id), BattleResolution(s, Outcome.WIN, 2000, selected))
        val restored = BattleLedger(store)
        assertTrue(restored.recover(3000) > 0)
        val result = store.loadPlayer(p.uuid)
        assertEquals(1, result.trainers["brock"]?.wins)
        assertEquals(selected.map { it.id }, result.deliveries.keys.toList())
        assertEquals(0, restored.recover(4000))
        assertEquals(1, store.loadPlayer(p.uuid).claims.values.single().count)
    }

    @Test fun `running battle after crash is aborted without a fabricated victory`() {
        val store = JsonStore(dir)
        val s = session(UUID.randomUUID())
        BattleLedger(store).reserve(s)
        BattleLedger(store).recover(5000)
        val progress = store.loadPlayer(s.player)
        assertEquals(0, progress.trainers["brock"]?.wins)
        assertTrue(progress.deliveries.isEmpty())
        assertTrue(progress.trainers.getValue("brock").cooldowns.isEmpty())
        assertEquals(Outcome.ABORTED, store.read(store.resolutionPath(s.id), BattleResolution::class.java)?.outcome)
    }

    @Test fun `result already applied to player is not applied again if result journal write was interrupted`() {
        val store = JsonStore(dir)
        val p = PlayerProgress(UUID.randomUUID())
        val s = session(p.uuid)
        val ledger = BattleLedger(store)
        ledger.reserve(s); ledger.finish(s.id, Outcome.WIN, context(p), 2000)
        val result = store.read(store.resolutionPath(s.id), BattleResolution::class.java)!!
        result.applied = false
        store.write(store.resolutionPath(s.id), result)
        BattleLedger(store).recover()
        assertEquals(1, store.loadPlayer(p.uuid).trainers["brock"]?.wins)
    }

    @Test fun `lack of space defers delivery and later grants only once`() {
        val store = JsonStore(dir)
        val p = PlayerProgress(UUID.randomUUID())
        val s = session(p.uuid, listOf(RewardGroup("win", rewards = listOf(Reward("a", RewardKind.ITEM, "minecraft:stone")))))
        val ledger = BattleLedger(store)
        ledger.reserve(s); ledger.finish(s.id, Outcome.WIN, context(p), 2000)
        var granted = 0
        ledger.deliver(p, { granted++ }, { _, _ -> }, { throw DeliveryDeferred("Sem espaço") })
        assertEquals(0, granted)
        assertEquals(DeliveryState.PENDING, store.loadPlayer(p.uuid).deliveries.values.single().state)
        ledger.deliver(p, { granted++ }, { _, _ -> })
        ledger.deliver(p, { granted++ }, { _, _ -> })
        assertEquals(1, granted)
    }

    @Test fun `notification candidates contain only newly persisted successful rewards`() {
        val store = JsonStore(dir)
        val p = PlayerProgress(UUID.randomUUID())
        val rewards = listOf(
            Reward("money", RewardKind.COMMAND, "say money", message = "&aVocê ganhou 5000 dollars!"),
            Reward("tokens", RewardKind.COMMAND, "say tokens", chance = 0.0, message = "Tokens!"),
            Reward("failed", RewardKind.COMMAND, "say failed", message = "Não deve aparecer"),
            Reward("pending", RewardKind.ITEM, "minecraft:diamond", message = "Entregue depois")
        )
        val s = session(p.uuid, listOf(RewardGroup("prizes", rewards = rewards)))
        val ledger = BattleLedger(store)
        ledger.reserve(s); ledger.finish(s.id, Outcome.WIN, context(p), 2000)
        val delivered = ledger.deliver(p, { if (it.reward.id == "failed") error("Command failed") }, { _, _ -> }, {
            if (it.reward.id == "pending") throw DeliveryDeferred("No space")
        })
        assertEquals(listOf("money"), delivered.map { it.reward.id })
        assertEquals("&aVocê ganhou 5000 dollars!", delivered.single().reward.message)
        assertEquals(DeliveryState.DELIVERED, store.loadPlayer(p.uuid).deliveries.getValue(delivered.single().id).state)
        val later = ledger.deliver(store.loadPlayer(p.uuid), {}, { _, _ -> })
        assertEquals(listOf("pending"), later.map { it.reward.id })
        assertTrue(ledger.deliver(store.loadPlayer(p.uuid), {}, { _, _ -> }).isEmpty())
    }

    @Test fun `guaranteed plus random still respects eligibility and never invents loss rewards for flee`() {
        val p = PlayerProgress(UUID.randomUUID())
        val fixed = Reward("fixed", RewardKind.ITEM, "minecraft:stone", guaranteed = true, chance = 0.0)
        val forbidden = fixed.copy(id = "forbidden", required_permission = "missing")
        val s = session(p.uuid, listOf(RewardGroup("mixed", GroupMode.GUARANTEED_PLUS_RANDOM, listOf(fixed, forbidden))))
        val engine = RewardEngine(Random(0))
        assertEquals(listOf("fixed"), engine.select(s, Outcome.WIN, context(p), 2000).map { it.reward.id })
        assertTrue(engine.select(s, Outcome.FLED, context(p), 2000).isEmpty())
    }
}
