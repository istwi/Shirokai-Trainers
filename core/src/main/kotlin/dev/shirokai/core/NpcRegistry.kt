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
    val removed: Boolean = false,
    val clickCommand: NpcClickCommand? = null
) {
    fun validate() {
        require(trainer == null || clickCommand == null) { "NPC de batalha não pode ter comando de clique" }
        clickCommand?.validate()
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

/** Nullable on TrainerNpc so registries written before command NPCs remain compatible. */
data class NpcClickCommand(val executor: String, val command: String) {
    fun validate() {
        require(executor in setOf("player", "console")) { "Executor: player ou console" }
        CommandTemplate.validate(command)
        require(!Regex("%([^%]+)%").findAll(command).any {
            it.groupValues[1] !in setOf("player", "player_uuid")
        }) { "NPC aceita apenas %player% e %player_uuid%" }
    }
    fun render(player: String, uuid: UUID): String {
        validate()
        require(player.matches(Regex("[A-Za-z0-9_]{1,16}")))
        return command.replace("%player%", player).replace("%player_uuid%", uuid.toString())
    }
}
