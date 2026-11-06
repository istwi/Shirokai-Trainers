package dev.shirokai.core

import kotlin.random.Random

class RewardEngine(private val random: Random = Random.Default) {
    fun select(session: BattleSession, outcome: Outcome, context: PlayerContext, now: Long): List<Delivery> {
        if (outcome != Outcome.WIN && outcome != Outcome.LOSS) return emptyList()
        val groups = if (outcome == Outcome.WIN) session.difficulty.winRewards else session.difficulty.lossRewards
        val previousWins = context.progress.trainers[session.trainer.id]?.wins ?: 0
        return groups.flatMap { group ->
            fun key(r: Reward) = "${session.trainer.id}/${session.difficulty.id}/${group.id}/${r.id}"
            val eligible = group.rewards.filter { r ->
                val claim = context.progress.claims[key(r)] ?: Claim()
                r.enabled && (!r.first_win_only || (outcome == Outcome.WIN && previousWins == 0)) &&
                    (r.repeatable || claim.count == 0) &&
                    (r.max_claims_per_player == 0 || claim.count < r.max_claims_per_player) &&
                    (claim.count == 0 || now - claim.lastClaim >= r.cooldown_seconds * 1000) &&
                    Requirements(r.required_permission, r.required_scoreboard, r.required_previous_victories).missing(context) == null
            }
            val selected = when (group.mode) {
                GroupMode.INDEPENDENT -> eligible.filter { random.nextDouble(100.0) < it.chance }
                GroupMode.GUARANTEED_PLUS_RANDOM -> eligible.filter { it.guaranteed || random.nextDouble(100.0) < it.chance }
                GroupMode.WEIGHTED_ONE -> {
                    val total = eligible.sumOf { it.weight }
                    if (total == 0.0) emptyList() else {
                        var draw = random.nextDouble(total)
                        listOf(eligible.firstOrNull { draw -= it.weight; draw < 0 } ?: eligible.last())
                    }
                }
            }
            selected.map { r -> Delivery("${session.id}/${key(r)}", session.id, session.trainer.id, session.trainer.name, key(r), r) }
        }
    }
}
