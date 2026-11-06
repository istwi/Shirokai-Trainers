package dev.shirokai.fabric

import com.cobblemon.mod.common.Cobblemon
import com.cobblemon.mod.common.api.events.CobblemonEvents
import com.cobblemon.mod.common.battles.*
import com.cobblemon.mod.common.battles.actor.PlayerBattleActor
import com.cobblemon.mod.common.battles.actor.TrainerBattleActor
import com.cobblemon.mod.common.battles.ai.StrongBattleAI
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon
import com.google.gson.GsonBuilder
import dev.shirokai.core.*
import me.lucko.fabric.api.permissions.v0.Permissions
import net.fabricmc.api.ModInitializer
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents
import net.fabricmc.fabric.api.event.player.UseEntityCallback
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents
import net.fabricmc.loader.api.FabricLoader
import net.minecraft.commands.CommandSourceStack
import net.minecraft.commands.CommandResultCallback
import net.minecraft.core.registries.BuiltInRegistries
import net.minecraft.network.chat.Component
import net.minecraft.resources.ResourceLocation
import net.minecraft.server.MinecraftServer
import net.minecraft.server.level.ServerPlayer
import net.minecraft.world.InteractionHand
import net.minecraft.world.InteractionResult
import net.minecraft.world.entity.Entity
import net.minecraft.world.item.ItemStack
import org.slf4j.LoggerFactory
import java.util.UUID

class ShirokaiTrainers : ModInitializer {
    val log = LoggerFactory.getLogger("ShirokaiTrainers")
    val gson = GsonBuilder().setPrettyPrinting().create()
    val store = JsonStore(FabricLoader.getInstance().configDir.resolve("shirokai_trainers")) { path, error ->
        log.error("JSON inválido preservado em {}; backup anterior carregado", path, error)
    }
    val ledger = BattleLedger(store)
    val npcSnapshots = NpcSnapshots(this)
    var trainers: Map<String, Trainer> = emptyMap()
        private set
    var bindings = Bindings()
    var debug = false
    lateinit var server: MinecraftServer
    private val waitingBind = mutableMapOf<UUID, Pair<String, Long>>()
    private val confirmingBind = mutableMapOf<UUID, BindRequest>()
    private val recoveryEnds = mutableMapOf<UUID, Outcome>()
    private var snapshotTicks = 0
    data class Bindings(val npcs: MutableMap<UUID, String> = mutableMapOf())
    data class BindRequest(val trainer: String, val entity: UUID, val dimension: String, val expires: Long)

    override fun onInitialize() {
        ServerLifecycleEvents.SERVER_STARTED.register { s ->
            server = s; reload()
            log.info("Recuperação de batalhas: {} registros", ledger.recover())
        }
        ServerLifecycleEvents.SERVER_STOPPING.register {
            npcSnapshots.captureAll()
            ledger.sessions.values.toList().forEach { finish(it.id, Outcome.ABORTED) }
        }
        CommandRegistrationCallback.EVENT.register { dispatcher, _, _ -> TrainerCommands(this).register(dispatcher) }
        ServerEntityEvents.ENTITY_UNLOAD.register { entity, _ ->
            if (entity.uuid in bindings.npcs && !entity.isRemoved) runCatching { npcSnapshots.capture(entity.uuid, entity) }
                .onFailure { log.error("Falha ao salvar NPC descarregado {}", entity.uuid, it) }
        }
        CobblemonEvents.BATTLE_VICTORY.subscribe { event ->
            if (::server.isInitialized) server.execute {
                val session = ledger.sessions[event.battle.battleId] ?: return@execute
                val outcome = when {
                    event.winners.any { it.uuid == session.player } -> Outcome.WIN
                    event.losers.any { it.uuid == session.player } -> Outcome.LOSS
                    else -> Outcome.ABORTED
                }
                finish(session.id, outcome)
            }
        }
        CobblemonEvents.BATTLE_FLED.subscribe { event ->
            if (::server.isInitialized) server.execute { finish(event.battle.battleId, Outcome.FLED) }
        }
        ServerPlayConnectionEvents.DISCONNECT.register { handler, _ ->
            val sessions = ledger.sessions.values.filter { it.player == handler.player.uuid }
            sessions.forEach { finish(it.id, Outcome.DISCONNECTED); BattleRegistry.getBattle(it.id)?.end() }
            waitingBind.remove(handler.player.uuid); confirmingBind.remove(handler.player.uuid)
        }
        ServerPlayConnectionEvents.JOIN.register { handler, _, _ ->
            runCatching { deliver(handler.player) }.onFailure { log.error("Falha ao recuperar entregas de {}", handler.player.uuid, it) }
        }
        ServerTickEvents.END_SERVER_TICK.register {
            if (++snapshotTicks >= 1200) {
                snapshotTicks = 0; npcSnapshots.captureAll()
                server.playerList.players.forEach { player ->
                    runCatching { deliver(player) }.onFailure { log.error("Falha ao processar entregas pendentes de {}", player.uuid, it) }
                }
            }
            val ended = recoveryEnds.toMap(); recoveryEnds.clear()
            ended.forEach { (id, outcome) -> if (id in ledger.sessions && BattleRegistry.getBattle(id) == null) finish(id, outcome) }
        }
        UseEntityCallback.EVENT.register(UseEntityCallback { player, world, hand, entity, _ ->
            if (world.isClientSide || player !is ServerPlayer || hand != InteractionHand.MAIN_HAND) return@UseEntityCallback InteractionResult.PASS
            try {
                require(player.distanceToSqr(entity) <= 64) { "Aproxime-se do NPC" }
                val waiting = waitingBind[player.uuid]
                if (waiting != null && admin(player.createCommandSourceStack())) {
                    waitingBind.remove(player.uuid)
                    require(waiting.second > System.currentTimeMillis()) { "Vinculação expirou; execute bind novamente" }
                    require(isNpc(entity)) { "Selecione uma entidade EasyNPC ou Cobblemon NPC" }
                    confirmingBind[player.uuid] = BindRequest(waiting.first, entity.uuid, world.dimension().location().toString(), System.currentTimeMillis() + 60000)
                    player.sendSystemMessage(Component.literal("Confirmar associação ${entity.uuid} → ${waiting.first}: /traineradmin bindconfirm"))
                    return@UseEntityCallback InteractionResult.SUCCESS
                }
                val trainer = bindings.npcs[entity.uuid] ?: return@UseEntityCallback InteractionResult.PASS
                // Deliberately preserve normal EasyNPC dialogs, tools and actions.
                if (!player.isShiftKeyDown || !player.mainHandItem.isEmpty) return@UseEntityCallback InteractionResult.PASS
                challenge(player, trainer, null)
                InteractionResult.SUCCESS
            } catch (e: Exception) {
                player.sendSystemMessage(Component.literal("§c${e.message}")); InteractionResult.FAIL
            }
        })
    }

    fun admin(source: CommandSourceStack): Boolean = Permissions.check(source, "shirokai.admin", 2)
    fun isNpc(entity: Entity): Boolean {
        val type = BuiltInRegistries.ENTITY_TYPE.getKey(entity.type)
        return type.namespace == "easy_npc" || (type.namespace == "cobblemon" && type.path == "npc")
    }
    fun beginBind(player: ServerPlayer, trainer: String) {
        require(trainer in trainers) { "Treinador inexistente" }
        waitingBind[player.uuid] = trainer to System.currentTimeMillis() + 60000
        confirmingBind.remove(player.uuid)
    }
    fun confirmBind(player: ServerPlayer) {
        val request = confirmingBind.remove(player.uuid) ?: error("Clique em um NPC primeiro")
        require(request.expires > System.currentTimeMillis()) { "Confirmação expirada" }
        val entity = player.serverLevel().getEntity(request.entity) ?: error("NPC indisponível nesta dimensão")
        require(player.level().dimension().location().toString() == request.dimension && isNpc(entity))
        require(player.distanceToSqr(entity) <= 64) { "Aproxime-se do NPC" }
        require(request.trainer in trainers)
        bindings.npcs[request.entity] = request.trainer
        store.write(store.root.resolve("bindings.json"), bindings)
        npcSnapshots.capture(request.entity)
        audit(player.scoreboardName, "bind ${request.entity} ${request.trainer}")
    }
    fun validate(t: Trainer) {
        t.validate()
        t.difficulties.forEach { d ->
            require(d.battleRules.all { it in ALLOWED_RULES }) { "Regra de batalha não suportada. Permitidas: $ALLOWED_RULES" }
            d.team.forEach { PokemonAdapter.create(it) }
            (d.winRewards + d.lossRewards).flatMap { it.rewards }.forEach { reward ->
                when (reward.kind) {
                    RewardKind.ITEM -> PokemonAdapter.resolveItem(reward.value)
                    RewardKind.POKEMON -> {
                        val p = gson.fromJson(StrictJson.parse(reward.value), PokemonSpec::class.java)
                        PokemonAdapter.create(p)
                        require(reward.amount == 1) { "Recompensa Pokémon entrega uma unidade" }
                    }
                    RewardKind.COMMAND -> {
                        val rendered = CommandTemplate.render(reward.value, "Validation", UUID(0, 0), t.id, t.name, UUID(0, 0))
                        val parsed = server.commands.dispatcher.parse(rendered, server.createCommandSourceStack())
                        require(!parsed.reader.canRead() && parsed.context.build(rendered).lastChild.command != null) { "Comando administrativo inválido: ${reward.id}" }
                        require(reward.amount == 1)
                    }
                }
            }
        }
    }
    fun save(t: Trainer, actor: String) {
        validate(t); store.saveTrainer(t); trainers = trainers + (t.id to t)
        audit(actor, "save ${t.id}")
    }
    fun reload() {
        // Load and validate the entire replacement before swapping any live configuration.
        val loaded = store.loadTrainers(::validate)
        val nextBindings = store.read(store.root.resolve("bindings.json"), Bindings::class.java) ?: Bindings()
        require(nextBindings.npcs.values.all { it in loaded }) { "Vinculação para treinador inexistente" }
        trainers = loaded; bindings = nextBindings
        log.info("Configuração carregada: {} treinadores, {} NPCs", trainers.size, bindings.npcs.size)
    }
    fun context(player: ServerPlayer, progress: PlayerProgress = store.loadPlayer(player.uuid)): PlayerContext {
        val scores = server.scoreboard.objectives.mapNotNull { objective ->
            server.scoreboard.getPlayerScoreInfo(player, objective)?.let { objective.name to it.value() }
        }.toMap()
        val gyms = trainers.values.count { it.gym && (progress.trainers[it.id]?.wins ?: 0) > 0 }
        return PlayerContext(player.uuid, player.scoreboardName, progress, scores, gyms) { Permissions.check(player, it, false) }
    }
    fun challenge(player: ServerPlayer, id: String, difficultyId: String?) {
        require(player.isAlive && !player.isSpectator) { "Não é possível desafiar nesse estado" }
        val t = trainers[id] ?: error("Treinador inexistente")
        require(t.enabled) { "Treinador desativado" }
        require(BattleRegistry.getBattleByParticipatingPlayer(player) == null) { "Você já está em batalha" }
        require(ledger.sessions.values.none { it.player == player.uuid }) { "Resultado anterior ainda em processamento" }
        require(t.simultaneous || ledger.sessions.values.none { it.trainer.id == id }) { "Treinador ocupado" }
        val ctx = context(player)
        val d = if (difficultyId != null) t.difficulties.find { it.id == difficultyId } ?: error("Dificuldade inexistente")
            else if (t.automaticDifficulty) t.difficulties.lastOrNull { it.requirements.missing(ctx) == null }
                ?: error(t.difficulties.first().requirements.missing(ctx) ?: "Nenhuma dificuldade disponível")
            else t.difficulties.first()
        d.requirements.missing(ctx)?.let { say(player, t, "requirements"); error(it) }
        val previous = ctx.progress.trainers[id]
        val remaining = (previous?.cooldowns?.get(d.id) ?: 0) - System.currentTimeMillis()
        if (remaining > 0) { say(player, t, "cooldown"); error("Aguarde ${(remaining + 999) / 1000}s") }
        require(d.team.isNotEmpty()) { "Equipe do treinador ainda não configurada" }
        val party = Cobblemon.storage.getParty(player)
        val team = party.toBattleTeam()
        require(team.any { it.health > 0 }) { "Você precisa de um Pokémon apto" }
        require(team.none { it.entity?.isBusy == true }) { "Pokémon ocupado" }
        val opponent = d.team.map { BattlePokemon.safeCopyOf(PokemonAdapter.create(it)) }
        val actor = TrainerBattleActor(t.name, UUID.randomUUID(), opponent, StrongBattleAI(d.skill))
        val format = BattleFormat.GEN_9_SINGLES.copy(ruleSet = BattleFormat.GEN_9_SINGLES.ruleSet + d.battleRules, adjustLevel = -1)
        val result = BattleRegistry.startBattle(format, BattleSide(PlayerBattleActor(player.uuid, team)), BattleSide(actor))
        result.ifSuccessful { battle ->
            val session = BattleSession(battle.battleId, player.uuid, t, d, System.currentTimeMillis())
            try { ledger.reserve(session) } catch (e: Exception) { battle.end(); throw e }
            battle.onEndHandlers.add { ended -> server.execute {
                recoveryEnds[ended.battleId] = when {
                    ended.fled -> Outcome.FLED
                    ended.winners.any { it.uuid == player.uuid } -> Outcome.WIN
                    ended.losers.any { it.uuid == player.uuid } -> Outcome.LOSS
                    else -> Outcome.ABORTED
                }
            } }
            say(player, t, if (previous == null) "first" else "rematch")
            say(player, t, "start")
            log.info("Batalha iniciada: {} jogador={} treinador={} dificuldade={}", session.id, player.uuid, t.id, d.id)
        }.ifErrored { error ->
            if (debug) log.debug("Falha ao iniciar batalha {}: {}", id, error)
            throw IllegalStateException("Cobblemon recusou a batalha; verifique equipes e disponibilidade")
        }
    }
    fun finish(id: UUID, outcome: Outcome) {
        val session = ledger.sessions[id] ?: return
        try {
            val player = server.playerList.getPlayer(session.player)
            val progress = store.loadPlayer(session.player)
            val ctx = player?.let { context(it, progress) } ?: PlayerContext(session.player, "Offline", progress, emptyMap(), 0) { false }
            ledger.finish(id, outcome, ctx, System.currentTimeMillis())
            log.info("Batalha encerrada: {} jogador={} resultado={}", id, session.player, outcome)
            if (player != null) {
                if (outcome == Outcome.WIN || outcome == Outcome.LOSS) say(player, session.trainer, if (outcome == Outcome.WIN) "win" else "loss")
                deliver(player)
            }
        } catch (e: Exception) {
            log.error("Não foi possível persistir resultado da batalha {}; sessão retida para revisão", id, e)
        }
    }
    fun deliver(player: ServerPlayer) {
        val p = store.loadPlayer(player.uuid)
        ledger.deliver(p, { delivery ->
            when (delivery.reward.kind) {
                RewardKind.ITEM -> {
                    val item = BuiltInRegistries.ITEM.get(ResourceLocation.parse(PokemonAdapter.resolveItem(delivery.reward.value)))
                    var remaining = delivery.reward.amount
                    // Preflight all space. Do not partially grant a reward and retry it later.
                    check(itemCapacity(player, item) >= remaining) { "Inventário mudou durante a entrega" }
                    while (remaining > 0) {
                        val amount = remaining.coerceAtMost(item.defaultMaxStackSize)
                        val stack = ItemStack(item, amount)
                        check(player.inventory.add(stack) && stack.isEmpty) { "Falha ao inserir item" }
                        remaining -= amount
                    }
                }
                RewardKind.POKEMON -> {
                    val spec = gson.fromJson(StrictJson.parse(delivery.reward.value), PokemonSpec::class.java)
                    check(Cobblemon.storage.getParty(player).add(PokemonAdapter.create(spec))) { "Equipe e PC sem espaço" }
                }
                RewardKind.COMMAND -> {
                    val command = CommandTemplate.render(delivery.reward.value, player.scoreboardName, player.uuid,
                        delivery.trainerId, delivery.trainerName, delivery.battleId)
                    log.info("Executando recompensa {}: {}", delivery.id, command)
                    var succeeded = false
                    var completed = false
                    var failed = false
                    val source = server.createCommandSourceStack().withPermission(4).withSuppressedOutput()
                        .withLevel(player.serverLevel()).withPosition(player.position())
                        .withCallback(CommandResultCallback { success, _ -> completed = true; succeeded = succeeded || success; failed = failed || !success })
                    server.commands.performPrefixedCommand(source, command)
                    check(completed && succeeded && !failed) { "Comando falhou ou não confirmou resultado completo" }
                }
            }
        }, { message, error -> if (error == null) log.info(message) else log.error(message, error) }, { delivery ->
            when (delivery.reward.kind) {
                RewardKind.ITEM -> {
                    val item = BuiltInRegistries.ITEM.get(ResourceLocation.parse(PokemonAdapter.resolveItem(delivery.reward.value)))
                    if (itemCapacity(player, item) < delivery.reward.amount) throw DeliveryDeferred("Inventário sem espaço")
                }
                RewardKind.POKEMON -> {
                    if (Cobblemon.storage.getParty(player).getFirstAvailablePosition() == null && Cobblemon.storage.getPC(player).getFirstAvailablePosition() == null)
                        throw DeliveryDeferred("Equipe e PC sem espaço")
                }
                else -> Unit
            }
        })
    }
    private fun itemCapacity(player: ServerPlayer, item: net.minecraft.world.item.Item): Int = (0 until 36).sumOf { slot ->
        val stack = player.inventory.getItem(slot)
        if (stack.isEmpty) item.defaultMaxStackSize
        else if (ItemStack.isSameItemSameComponents(stack, ItemStack(item))) (stack.maxStackSize - stack.count).coerceAtLeast(0)
        else 0
    }
    fun say(player: ServerPlayer, t: Trainer, key: String) {
        t.dialogues[key]?.forEach { player.sendSystemMessage(Component.literal(it.replace(Regex("&([0-9a-fk-orA-FK-OR])"), "§$1"))) }
    }
    fun audit(actor: String, action: String) { log.info("Admin {}: {}", actor, action) }
    companion object {
        val ALLOWED_RULES = setOf("Bag Clause", "Sleep Clause Mod", "Species Clause", "OHKO Clause", "Evasion Moves Clause", "Endless Battle Clause")
    }
}
