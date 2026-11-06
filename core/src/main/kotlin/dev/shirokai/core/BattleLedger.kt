package dev.shirokai.core

import java.util.UUID

/** Server-thread ledger. Journal the confirmed result and random draw before updating progress. */
class BattleLedger(private val store: JsonStore, private val rewards: RewardEngine = RewardEngine()) {
    val sessions = mutableMapOf<UUID, BattleSession>()
    fun reserve(session: BattleSession) {
        require(sessions.values.none { it.player == session.player }) { "Jogador já está batalhando" }
        require(session.trainer.simultaneous || sessions.values.none { it.trainer.id == session.trainer.id }) { "Treinador ocupado" }
        require(session.id !in sessions)
        store.write(store.sessionPath(session.id), session)
        sessions[session.id] = session
    }
    fun finish(id: UUID, outcome: Outcome, context: PlayerContext, now: Long): PlayerProgress {
        val session = sessions[id] ?: error("Batalha desconhecida")
        require(session.player == context.uuid)
        val result = store.read(store.resolutionPath(id), BattleResolution::class.java) ?: BattleResolution(
            session.copy(outcome = outcome, state = BattleState.RESULT_CONFIRMED), outcome, now,
            rewards.select(session, outcome, context, now)
        ).also { store.write(store.resolutionPath(id), it) }
        val progress = apply(result, context.progress)
        context.progress.apply {
            trainers.clear(); trainers.putAll(progress.trainers)
            claims.clear(); claims.putAll(progress.claims)
            deliveries.clear(); deliveries.putAll(progress.deliveries)
            completedBattles.clear(); completedBattles.addAll(progress.completedBattles)
        }
        sessions.remove(id)
        return progress
    }
    private fun apply(result: BattleResolution, existing: PlayerProgress): PlayerProgress {
        val session = result.battle
        require(existing.uuid == session.player)
        val progress = store.copyPlayer(existing)
        if (session.id !in progress.completedBattles) {
            val trainer = progress.trainers.getOrPut(session.trainer.id) { TrainerProgress() }
            when (result.outcome) {
                Outcome.WIN -> { trainer.wins++; if (trainer.firstWin == null) trainer.firstWin = result.finished }
                Outcome.LOSS -> trainer.losses++
                else -> Unit
            }
            trainer.lastBattle = result.finished
            if (result.outcome != Outcome.ABORTED) {
                trainer.cooldowns[session.difficulty.id] = Math.addExact(result.finished, Math.multiplyExact(session.difficulty.cooldownSeconds, 1000))
            }
            result.deliveries.forEach { d ->
                progress.deliveries.putIfAbsent(d.id, d)
                val claim = progress.claims.getOrPut(d.rewardKey) { Claim() }
                claim.count++; claim.lastClaim = result.finished
            }
            progress.completedBattles.add(session.id)
            store.savePlayer(progress)
        }
        if (!result.applied) {
            result.applied = true
            store.write(store.resolutionPath(session.id), result)
        }
        store.write(store.sessionPath(session.id), session.copy(state = BattleState.COMPLETED, outcome = result.outcome))
        return progress
    }
    /** Reapply durable results; unconfirmed sessions become ABORTED, never wins. */
    fun recover(now: Long = System.currentTimeMillis()): Int {
        var count = 0
        store.loadResolutions().filter { !it.applied }.forEach { result ->
            apply(result, store.loadPlayer(result.battle.player)); count++
        }
        store.loadSessions().filter { it.state != BattleState.COMPLETED }.forEach { session ->
            val result = store.read(store.resolutionPath(session.id), BattleResolution::class.java) ?: BattleResolution(
                session.copy(outcome = Outcome.ABORTED, state = BattleState.RESULT_CONFIRMED), Outcome.ABORTED, now, emptyList()
            ).also { store.write(store.resolutionPath(session.id), it) }
            apply(result, store.loadPlayer(session.player)); sessions.remove(session.id); count++
        }
        return count
    }
    fun deliver(p: PlayerProgress, grant: (Delivery) -> Unit, log: (String, Throwable?) -> Unit, preflight: (Delivery) -> Unit = {}) {
        p.deliveries.values.filter { it.state == DeliveryState.PENDING }.forEach { d ->
            try { preflight(d) } catch (e: DeliveryDeferred) {
                if (d.error != e.message) {
                    d.error = e.message; store.savePlayer(p)
                    log("Entrega pendente: ${p.uuid} ${d.id}: ${e.message}", null)
                }
                return@forEach
            }
            d.state = DeliveryState.IN_FLIGHT
            store.savePlayer(p)
            try {
                grant(d)
                d.state = DeliveryState.DELIVERED; d.error = null
                store.savePlayer(p)
                log("Recompensa concedida: ${p.uuid} ${d.id}", null)
            } catch (e: Exception) {
                d.state = DeliveryState.NEEDS_REVIEW; d.error = e.message
                store.savePlayer(p)
                log("Entrega requer revisão: ${p.uuid} ${d.id}", e)
            }
        }
    }
}
