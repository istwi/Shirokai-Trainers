package dev.shirokai.core

import java.util.UUID

fun validId(value: String) = value.matches(Regex("[a-z0-9][a-z0-9_-]{0,63}"))

data class PokemonSpec(
    val species: String = "pikachu",
    val form: String? = null,
    val level: Int = 50,
    val ivs: Map<String, Int> = STATS.associateWith { 31 },
    val evs: Map<String, Int> = STATS.associateWith { 0 },
    val nature: String = "hardy",
    val ability: String? = null,
    val moves: List<String> = listOf("tackle"),
    val heldItem: String? = null,
    val shiny: Boolean = false
) {
    fun validate() {
        require(species.isNotBlank()) { "Espécie vazia" }
        require(level in 1..100) { "Nível deve estar entre 1 e 100" }
        require(ivs.keys.all { it in STATS } && ivs.values.all { it in 0..31 }) { "IVs inválidos" }
        require(evs.keys.all { it in STATS } && evs.values.all { it in 0..252 } && evs.values.sum() <= 510) { "EVs inválidos" }
        require(moves.size in 1..4 && moves.distinct().size == moves.size) { "Use de 1 a 4 movimentos distintos" }
    }
    companion object { val STATS = listOf("hp", "attack", "defence", "special_attack", "special_defence", "speed") }
}

data class Requirements(
    val permission: String? = null,
    val scoreboard: Map<String, Int> = emptyMap(),
    val previousVictories: Map<String, Int> = emptyMap(),
    val gyms: Int = 0,
    val objectives: Set<String> = emptySet()
) {
    fun missing(context: PlayerContext): String? = when {
        permission != null && !context.hasPermission(permission) -> "Permissão necessária: $permission"
        scoreboard.any { (k, v) -> (context.scores[k] ?: Int.MIN_VALUE) < v } -> "Scoreboard necessário: ${scoreboard.filter { (k, v) -> (context.scores[k] ?: Int.MIN_VALUE) < v }}"
        previousVictories.any { (k, v) -> (context.progress.trainers[k]?.wins ?: 0) < v } -> "Vitórias necessárias: ${previousVictories.filter { (k, v) -> (context.progress.trainers[k]?.wins ?: 0) < v }}"
        context.defeatedGyms < gyms -> "Ginásios necessários: $gyms"
        !context.progress.objectives.containsAll(objectives) -> "Objetivos necessários: ${objectives - context.progress.objectives}"
        else -> null
    }
}

data class PlayerContext(
    val uuid: UUID,
    val name: String,
    val progress: PlayerProgress,
    val scores: Map<String, Int>,
    val defeatedGyms: Int,
    val hasPermission: (String) -> Boolean
)

enum class GroupMode { INDEPENDENT, WEIGHTED_ONE, GUARANTEED_PLUS_RANDOM }
enum class RewardKind { ITEM, POKEMON, COMMAND }
enum class Outcome { WIN, LOSS, FLED, DISCONNECTED, ABORTED }

data class Reward(
    val id: String,
    val kind: RewardKind,
    val value: String,
    val amount: Int = 1,
    val enabled: Boolean = true,
    val chance: Double = 100.0,
    val weight: Double = 1.0,
    val guaranteed: Boolean = false,
    val first_win_only: Boolean = false,
    val repeatable: Boolean = true,
    val cooldown_seconds: Long = 0,
    val max_claims_per_player: Int = 0,
    val required_permission: String? = null,
    val required_scoreboard: Map<String, Int> = emptyMap(),
    val required_previous_victories: Map<String, Int> = emptyMap()
) {
    fun validate() {
        require(validId(id)) { "ID de recompensa inválido" }
        require(chance.isFinite() && chance in 0.0..100.0) { "Chance deve estar entre 0 e 100" }
        require(weight.isFinite() && weight > 0) { "Peso deve ser positivo" }
        require(amount in 1..2304 && cooldown_seconds in 0..315360000 && max_claims_per_player >= 0)
        require(value.isNotBlank())
        if (kind == RewardKind.COMMAND) CommandTemplate.validate(value)
    }
}

data class RewardGroup(val id: String, val mode: GroupMode = GroupMode.INDEPENDENT, val rewards: List<Reward> = emptyList())
data class Difficulty(
    val id: String = "normal",
    val team: List<PokemonSpec> = emptyList(),
    val requirements: Requirements = Requirements(),
    val cooldownSeconds: Long = 300,
    val skill: Int = 3,
    val battleRules: List<String> = listOf("Bag Clause"),
    val winRewards: List<RewardGroup> = emptyList(),
    val lossRewards: List<RewardGroup> = emptyList()
)
data class Trainer(
    val id: String,
    val name: String = id,
    val enabled: Boolean = true,
    val simultaneous: Boolean = true,
    val gym: Boolean = false,
    val automaticDifficulty: Boolean = false,
    val difficulties: List<Difficulty> = listOf(Difficulty()),
    val dialogues: Map<String, List<String>> = DEFAULT_DIALOGUES,
    val schemaVersion: Int = 1
) {
    fun validate() {
        require(schemaVersion == 1) { "Versão de configuração não suportada: $schemaVersion" }
        require(validId(id)) { "ID inválido" }
        require(name.isNotBlank() && name.length <= 80 && name.none { it == '\n' || it == '\r' })
        require(difficulties.isNotEmpty() && difficulties.map { it.id }.distinct().size == difficulties.size)
        difficulties.forEach { d ->
            require(validId(d.id) && d.team.size <= 6 && d.cooldownSeconds in 0..315360000 && d.skill in 0..5)
            d.team.forEach { it.validate() }
            val groups = d.winRewards + d.lossRewards
            require(groups.map { it.id }.distinct().size == groups.size) { "IDs de grupo duplicados" }
            groups.forEach { g ->
                require(validId(g.id))
                require(g.rewards.map { it.id }.distinct().size == g.rewards.size)
                g.rewards.forEach { it.validate() }
                require(g.rewards.sumOf { it.weight }.isFinite())
            }
        }
        require(dialogues.keys.all { it in DEFAULT_DIALOGUES })
        require(dialogues.values.all { lines -> lines.size <= 30 && lines.all { it.length <= 1000 } })
    }
    companion object {
        val DEFAULT_DIALOGUES = mapOf(
            "first" to listOf("&ePronto para um desafio?"),
            "start" to listOf("&eVamos batalhar!"),
            "win" to listOf("&aVocê venceu!"),
            "loss" to listOf("&cTente novamente!"),
            "cooldown" to listOf("&cAguarde o cooldown."),
            "rematch" to listOf("&eUma revanche!"),
            "requirements" to listOf("&cVocê ainda não cumpre os requisitos.")
        )
    }
}

data class TrainerProgress(
    var wins: Int = 0,
    var losses: Int = 0,
    var firstWin: Long? = null,
    var lastBattle: Long? = null,
    val cooldowns: MutableMap<String, Long> = mutableMapOf()
)
data class Claim(var count: Int = 0, var lastClaim: Long = 0)
enum class DeliveryState { PENDING, IN_FLIGHT, DELIVERED, NEEDS_REVIEW }
data class Delivery(
    val id: String,
    val battleId: UUID,
    val trainerId: String,
    val trainerName: String,
    val rewardKey: String,
    val reward: Reward,
    var state: DeliveryState = DeliveryState.PENDING,
    var error: String? = null
)
data class PlayerProgress(
    val uuid: UUID,
    val trainers: MutableMap<String, TrainerProgress> = mutableMapOf(),
    val claims: MutableMap<String, Claim> = mutableMapOf(),
    val deliveries: MutableMap<String, Delivery> = mutableMapOf(),
    val completedBattles: MutableSet<UUID> = mutableSetOf(),
    val objectives: MutableSet<String> = mutableSetOf(),
    val schemaVersion: Int = 1
)
enum class BattleState { RUNNING, RESULT_CONFIRMED }
data class BattleSession(
    val id: UUID,
    val player: UUID,
    val trainer: Trainer,
    val difficulty: Difficulty,
    val started: Long,
    var outcome: Outcome? = null,
    var state: BattleState = BattleState.RUNNING
)
