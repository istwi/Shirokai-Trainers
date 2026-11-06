package dev.shirokai.core

import java.util.UUID

/** All operations must run on the server thread. Persist before granting any external effects. */
class BattleLedger(private val store: JsonStore, private val rewards: RewardEngine = RewardEngine()) {
    val sessions = mutableMapOf<UUID, BattleSession>()
    fun reserve(session: BattleSession) {
        require(sessions.values.none { it.player == session.player }) { "Jogador já está batalhando" }
        require(session.trainer.simultaneous || sessions.values.none { it.trainer.id == session.trainer.id }) { "Treinador ocupado" }
        require(session.id !in sessions)
        sessions[session.id] = session
    }
    fun finish(id: UUID, outcome: Outcome, context: PlayerContext, now: Long): PlayerProgress {
        val s = sessions[id] ?: error("Batalha desconhecida")
        require(s.player == context.uuid)
        val p = context.progress
        if (id in p.completedBattles) { sessions.remove(id); return p }
        val selected = rewards.select(s, outcome, context, now)
        val progress = p.trainers.getOrPut(s.trainer.id) { TrainerProgress() }
        when (outcome) {
            Outcome.WIN -> { progress.wins++; if (progress.firstWin == null) progress.firstWin = now }
            Outcome.LOSS -> progress.losses++
            else -> Unit
        }
        progress.lastBattle = now
        progress.cooldowns[s.difficulty.id] = Math.addExact(now, Math.multiplyExact(s.difficulty.cooldownSeconds, 1000))
        selected.forEach { d ->
            p.deliveries[d.id] = d
            val claim = p.claims.getOrPut(d.rewardKey) { Claim() }
            claim.count++
            claim.lastClaim = now
        }
        p.completedBattles.add(id)
        store.savePlayer(p)
        s.outcome = outcome
        s.state = BattleState.RESULT_CONFIRMED
        sessions.remove(id)
        return p
    }
    fun deliver(p: PlayerProgress, grant: (Delivery) -> Unit, log: (String, Throwable?) -> Unit) {
        p.deliveries.values.filter { it.state == DeliveryState.PENDING }.forEach { d ->
            d.state = DeliveryState.IN_FLIGHT
            store.savePlayer(p)
            try {
                grant(d)
                d.state = DeliveryState.DELIVERED
                d.error = null
                store.savePlayer(p)
                log("Recompensa concedida: ${p.uuid} ${d.id}", null)
            } catch (e: Exception) {
                // External effects and disk writes cannot be one transaction. Never blindly retry.
                d.state = DeliveryState.NEEDS_REVIEW
                d.error = e.message
                store.savePlayer(p)
                log("Entrega requer revisão: ${p.uuid} ${d.id}", e)
            }
        }
    }
}
