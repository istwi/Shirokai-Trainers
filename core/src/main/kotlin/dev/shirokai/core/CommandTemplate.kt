package dev.shirokai.core

import java.util.UUID

object CommandTemplate {
    private val tokens = setOf("player", "player_uuid", "trainer_id", "trainer_name", "battle_id")
    private val placeholder = Regex("%([^%]+)%")
    fun validate(command: String) {
        require(command.length in 1..2048 && !command.startsWith('/')) { "Comando sem /, máximo 2048 caracteres" }
        require(command.none { it.isISOControl() }) { "Caracteres de controle proibidos" }
        require(placeholder.findAll(command).all { it.groupValues[1] in tokens }) { "Placeholder desconhecido" }
        require('%' !in placeholder.replace(command, "")) { "Placeholder malformado" }
        require(command.substringBefore(' ').matches(Regex("[a-z0-9_:.]+"))) { "Raiz do comando deve ser literal" }
        // Never interpolate strings inside quoted JSON/NBT or escape-sensitive command arguments.
        placeholder.findAll(command).forEach {
            require(it.range.first == 0 || command[it.range.first - 1] == ' ') { "Placeholder deve ocupar um argumento" }
            require(it.range.last == command.lastIndex || command[it.range.last + 1] == ' ') { "Placeholder deve ocupar um argumento" }
        }
    }
    fun render(command: String, player: String, uuid: UUID, trainer: String, trainerName: String, battle: UUID): String {
        validate(command)
        require(player.matches(Regex("[A-Za-z0-9_]{1,16}")))
        require(validId(trainer))
        // Display names may contain formatting/quotes. Restrict their use in privileged commands.
        if ("%trainer_name%" in command) require(trainerName.matches(Regex("[A-Za-z0-9_-]{1,80}"))) {
            "%trainer_name% em comandos exige nome sem espaços ou caracteres especiais; use %trainer_id%"
        }
        val values = mapOf("player" to player, "player_uuid" to uuid.toString(), "trainer_id" to trainer,
            "trainer_name" to trainerName, "battle_id" to battle.toString())
        return placeholder.replace(command) { values.getValue(it.groupValues[1]) }
    }
}
