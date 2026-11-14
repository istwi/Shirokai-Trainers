package dev.shirokai.core

import java.nio.file.Files
import java.util.UUID
import kotlin.test.*
import org.junit.jupiter.api.Test

class NpcRegistryTest {
    private fun npc(id: String = "blue", uuid: UUID = UUID.randomUUID()) = TrainerNpc(
        id, uuid, true, "blue", "multiworld:arena", -17.5, 64.0, 32.0)

    @Test fun `persist stable identity dimension messages and unlink without touching trainer or progress`() {
        val root = Files.createTempDirectory("npc-registry")
        val store = JsonStore(root)
        val trainer = Trainer("blue")
        val player = PlayerProgress(UUID.randomUUID())
        store.saveTrainer(trainer); store.savePlayer(player)
        val trainerBytes = Files.readAllBytes(store.trainerPath(trainer.id))
        val playerBytes = Files.readAllBytes(store.playerPath(player.uuid))
        val first = npc().copy(message = "Olá!", confirmation = "Batalhar com Blue?")
        val file = root.resolve("npcs.json")
        store.write(file, NpcRegistry(npcs = listOf(first)))
        val reloaded = JsonStore(root).read(file, NpcRegistry::class.java) { it.validate() }!!
        assertEquals(first, reloaded.npcs.single())
        store.write(file, reloaded.copy(npcs = listOf(first.copy(trainer = null))))
        assertNull(store.read(file, NpcRegistry::class.java) { it.validate() }!!.npcs.single().trainer)
        assertContentEquals(trainerBytes, Files.readAllBytes(store.trainerPath(trainer.id)))
        assertContentEquals(playerBytes, Files.readAllBytes(store.playerPath(player.uuid)))
    }

    @Test fun `reject duplicate IDs and entity bindings`() {
        val first = npc()
        assertFailsWith<IllegalArgumentException> { NpcRegistry(npcs = listOf(first, npc())).validate() }
        assertFailsWith<IllegalArgumentException> { NpcRegistry(npcs = listOf(first, npc("red", first.entity))).validate() }
    }

    @Test fun `tombstone persists and cannot delete external entity`() {
        val first = npc().copy(removed = true, trainer = null)
        NpcRegistry(npcs = listOf(first)).validate()
        assertFailsWith<IllegalArgumentException> { first.copy(owned = false).validate() }
    }

    @Test fun `reject invalid version dimension position and IDs`() {
        assertFailsWith<IllegalArgumentException> { NpcRegistry(schemaVersion = 2).validate() }
        assertFailsWith<IllegalArgumentException> { npc().copy(dimension = "World Name").validate() }
        assertFailsWith<IllegalArgumentException> { npc().copy(x = Double.NaN).validate() }
        assertFailsWith<IllegalArgumentException> { npc().copy(trainer = "../trainer").validate() }
    }
}
