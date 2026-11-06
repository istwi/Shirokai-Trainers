package dev.shirokai.fabric

import net.minecraft.core.registries.BuiltInRegistries
import net.minecraft.core.registries.Registries
import net.minecraft.nbt.CompoundTag
import net.minecraft.nbt.TagParser
import net.minecraft.resources.ResourceKey
import net.minecraft.resources.ResourceLocation
import net.minecraft.world.entity.Entity
import net.minecraft.world.entity.Mob
import java.util.UUID

/** Additional recovery copy. Native world persistence remains responsible for entity existence. */
class NpcSnapshots(private val mod: ShirokaiTrainers) {
    data class Snapshot(
        val uuid: UUID,
        val trainer: String,
        val entityType: String,
        val dimension: String,
        val x: Double,
        val y: Double,
        val z: Double,
        val yaw: Float,
        val pitch: Float,
        val entityData: String,
        val schemaVersion: Int = 1
    )
    private fun path(uuid: UUID) = mod.store.root.resolve("npcs/$uuid.json")
    private fun find(uuid: UUID): Entity? = mod.server.allLevels.firstNotNullOfOrNull { it.getEntity(uuid) }
    fun capture(uuid: UUID): Boolean {
        val trainer = mod.bindings.npcs[uuid] ?: error("NPC não vinculado")
        val entity = find(uuid) ?: return false // An unloaded entity is not a deleted entity.
        require(mod.isNpc(entity) && entity.isAlive)
        if (entity is Mob) entity.setPersistenceRequired()
        val tag = entity.saveWithoutId(CompoundTag())
        val snapshot = Snapshot(uuid, trainer, BuiltInRegistries.ENTITY_TYPE.getKey(entity.type).toString(),
            entity.level().dimension().location().toString(), entity.x, entity.y, entity.z, entity.yRot, entity.xRot, tag.toString())
        val previous = mod.store.read(path(uuid), Snapshot::class.java)
        if (previous != snapshot) mod.store.write(path(uuid), snapshot)
        return true
    }
    fun captureAll(): Int = mod.bindings.npcs.keys.count { uuid ->
        try { capture(uuid) } catch (e: Exception) { mod.log.error("Falha ao salvar configuração/localização do NPC {}", uuid, e); false }
    }
    fun restore(uuid: UUID, actor: String) {
        val snapshot = mod.store.read(path(uuid), Snapshot::class.java) ?: error("Snapshot inexistente")
        require(snapshot.schemaVersion == 1 && snapshot.uuid == uuid)
        require(mod.bindings.npcs[uuid] == snapshot.trainer) { "Vinculação mudou; revise o snapshot antes de restaurar" }
        require(mod.ledger.sessions.values.none { it.trainer.id == snapshot.trainer }) { "Treinador em batalha" }
        val entity = find(uuid) ?: error("NPC não está carregado. Carregue seu chunk; nenhuma entidade será recriada automaticamente")
        require(mod.isNpc(entity) && BuiltInRegistries.ENTITY_TYPE.getKey(entity.type).toString() == snapshot.entityType)
        val level = mod.server.getLevel(ResourceKey.create(Registries.DIMENSION, ResourceLocation.parse(snapshot.dimension)))
            ?: error("Dimensão indisponível: ${snapshot.dimension}")
        require(snapshot.x.isFinite() && snapshot.y.isFinite() && snapshot.z.isFinite() && snapshot.yaw.isFinite() && snapshot.pitch.isFinite())
        require(kotlin.math.abs(snapshot.x) <= 29999984 && kotlin.math.abs(snapshot.z) <= 29999984)
        val tag = TagParser.parseTag(snapshot.entityData)
        require(tag.hasUUID("UUID") && tag.getUUID("UUID") == uuid)
        require(!tag.contains("Passengers") && !entity.isPassenger && !entity.isVehicle) { "Desmonte NPC e passageiros antes de restaurar" }
        val before = entity.saveWithoutId(CompoundTag())
        // Archive both the recovery snapshot and the live state before applying the recovery.
        mod.store.write(mod.store.root.resolve("npc-restore-backups/${uuid}-${UUID.randomUUID()}.json"),
            Snapshot(uuid, snapshot.trainer, snapshot.entityType, entity.level().dimension().location().toString(),
                entity.x, entity.y, entity.z, entity.yRot, entity.xRot, before.toString()))
        try {
            entity.load(tag)
            check(entity.teleportTo(level, snapshot.x, snapshot.y, snapshot.z, emptySet(), snapshot.yaw, snapshot.pitch)) { "Teleporte recusado" }
            find(uuid)?.let { if (it is Mob) it.setPersistenceRequired() }
            mod.audit(actor, "npcrestore $uuid ${snapshot.dimension} ${snapshot.x} ${snapshot.y} ${snapshot.z}")
        } catch (e: Exception) {
            // No replacement entity is ever spawned. Preserve the backup for operator recovery.
            mod.log.error("Restauração de NPC {} falhou; estado anterior arquivado para recuperação", uuid, e)
            throw e
        }
    }
}
