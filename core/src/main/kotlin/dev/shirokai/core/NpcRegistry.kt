package dev.shirokai.core

import java.util.UUID

/** Index only. Minecraft/Cobblemon owns entity NBT; this index never respawns entities. */
data class TrainerNpc(
    val id: String,
    val entity: UUID,
    val owned: Boolean,
    val trainer: String?,
    val dimension: String,
    val x: Double, val y: Double, val z: Double,
    val message: String = "Vamos batalhar?",
    val confirmation: String = "Confirmar desafio",
    val confirm: Boolean = true,
    val removed: Boolean = false
) {
    fun validate() {
        requireNotNull(entity) { "UUID de entidade ausente" }
        require(validId(id) && (trainer == null || validId(trainer))) { "ID de NPC/treinador inválido" }
        require(dimension.matches(Regex("[a-z0-9_.-]+:[a-z0-9/._-]+"))) { "Dimensão inválida" }
        require(listOf(x, y, z).all { it.isFinite() }) { "Posição inválida" }
        require(message.length <= 2000 && confirmation.length <= 200) { "Mensagem muito longa" }
        require(!removed || owned) { "NPC externo não pode ser apagado" }
    }
}
data class NpcRegistry(val schemaVersion: Int = 1, val npcs: List<TrainerNpc> = emptyList()) {
    fun validate() {
        require(schemaVersion == 1) { "Versão de NPCs não suportada" }
        npcs.forEach { it.validate() }
        require(npcs.map { it.id }.distinct().size == npcs.size) { "ID de NPC duplicado" }
        require(npcs.map { it.entity }.distinct().size == npcs.size) { "Entidade já vinculada" }
    }
}
