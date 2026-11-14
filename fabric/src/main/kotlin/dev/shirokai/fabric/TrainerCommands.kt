package dev.shirokai.fabric

import com.mojang.brigadier.CommandDispatcher
import com.mojang.brigadier.arguments.StringArgumentType
import dev.shirokai.core.*
import net.minecraft.commands.CommandSourceStack
import net.minecraft.commands.Commands.*
import net.minecraft.network.chat.Component
import net.minecraft.server.level.ServerPlayer
import java.util.UUID
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents

class TrainerCommands(private val mod: ShirokaiTrainers) {
    private data class Input(val text: StringBuilder = StringBuilder(), var expires: Long = System.currentTimeMillis() + 600000)
    private val inputs = mutableMapOf<UUID, Input>()
    fun register(dispatcher: CommandDispatcher<CommandSourceStack>) {
        ServerPlayConnectionEvents.DISCONNECT.register { handler, _ -> inputs.remove(handler.player.uuid) }
        dispatcher.register(literal("trainerclaim").executes { ctx -> protect(ctx.source) {
            mod.deliver(ctx.source.playerOrException)
            ctx.source.sendSystemMessage(Component.literal("Recompensas pendentes processadas.")); 1
        } })
        dispatcher.register(literal("trainerstatus").executes { ctx -> protect(ctx.source) {
            val p = mod.store.loadPlayer(ctx.source.playerOrException.uuid)
            val summary = p.trainers.entries.sortedBy { it.key }.joinToString("\n") { (id, data) -> "$id: ${data.wins} vitórias, ${data.losses} derrotas" }
            val pending = p.deliveries.values.count { it.state == DeliveryState.PENDING }
            val review = p.deliveries.values.count { it.state in setOf(DeliveryState.NEEDS_REVIEW, DeliveryState.IN_FLIGHT) }
            ctx.source.sendSystemMessage(Component.literal("${summary.ifEmpty { "Nenhuma batalha registrada." }}\nRecompensas pendentes: $pending; revisão administrativa: $review")); 1
        } })
        val admin = literal("traineradmin").requires(mod::admin)
            .executes { ctx -> protect(ctx.source) { TrainerMenus(mod).list(ctx.source.playerOrException, true); 1 } }
        ACTIONS.forEach { action ->
            admin.then(literal(action)
                .executes { ctx -> protect(ctx.source) { execute(ctx.source, action, ""); 1 } }
                .then(argument("args", StringArgumentType.greedyString()).executes { ctx -> protect(ctx.source) {
                    execute(ctx.source, action, StringArgumentType.getString(ctx, "args")); 1
                } }))
        }
        admin.then(argument("player", StringArgumentType.word())
            .then(literal("battle")
                .then(argument("battle", StringArgumentType.word())
                    .suggests { _, b -> mod.trainers.keys.forEach(b::suggest); b.buildFuture() }
                    .executes { ctx -> protect(ctx.source) {
                        startBattle(ctx.source, StringArgumentType.getString(ctx, "player"), StringArgumentType.getString(ctx, "battle")); 1
                    } })))
        dispatcher.register(admin)
    }
    private fun protect(source: CommandSourceStack, action: () -> Int): Int = try { action() } catch (e: Exception) {
        source.sendFailure(Component.literal(e.message ?: e.javaClass.simpleName))
        if (mod.debug) mod.log.error("Falha em comando por {}", source.textName, e)
        0
    }
    private fun parts(text: String, count: Int): List<String> {
        val values = text.trim().split(Regex("\\s+"), limit = count)
        require(values.size == count && values.none { it.isEmpty() }) { "Argumentos insuficientes; consulte /traineradmin help" }
        return values
    }
    private fun execute(source: CommandSourceStack, action: String, text: String) {
        require(mod.admin(source))
        val actor = source.textName
        fun trainer(id: String) = mod.trainers[id] ?: error("Treinador inexistente: $id")
        fun updateDifficulty(id: String, difficulty: String, transform: (Difficulty) -> Difficulty) {
            val t = trainer(id)
            require(t.difficulties.any { it.id == difficulty }) { "Dificuldade inexistente" }
            mod.save(t.copy(difficulties = t.difficulties.map { if (it.id == difficulty) transform(it) else it }), actor)
        }
        fun buffer(): String {
            val input = inputs[source.playerOrException.uuid] ?: error("Use input begin e input append primeiro")
            require(input.expires > System.currentTimeMillis()) { "Entrada expirada" }
            return input.text.toString()
        }
        when (action) {
            "npc" -> mod.npcs.command(source, text)
            "help" -> source.sendSystemMessage(Component.literal(HELP + "\n" + TrainerNpcs.HELP))
            "create" -> {
                val id = text.trim(); require(id !in mod.trainers) { "ID já existe" }
                mod.save(Trainer(id), actor)
                source.sendSystemMessage(Component.literal("Treinador criado. Configure a equipe: /traineradmin edit $id"))
            }
            "edit" -> TrainerMenus(mod).trainer(source.playerOrException, trainer(text.trim()))
            "name" -> { val (id, name) = parts(text, 2); mod.save(trainer(id).copy(name = name), actor) }
            "config" -> {
                val (id, json) = parts(text, 2)
                val t = mod.gson.fromJson(StrictJson.parse(if (json == "buffer") buffer() else json), Trainer::class.java)
                require(t.id == id && id in mod.trainers)
                mod.save(t, actor)
            }
            "show" -> source.sendSystemMessage(Component.literal(mod.gson.toJson(trainer(text.trim()))))
            "input" -> {
                val player = source.playerOrException
                val operation = text.substringBefore(' ')
                when (operation) {
                    "begin" -> inputs[player.uuid] = Input()
                    "clear" -> inputs.remove(player.uuid)
                    "append" -> {
                        val input = inputs[player.uuid] ?: error("Use input begin")
                        require(input.expires > System.currentTimeMillis())
                        val line = text.substringAfter(' ', "")
                        require(input.text.length + line.length < 24000)
                        if (input.text.isNotEmpty()) input.text.append('\n')
                        input.text.append(if (line == "<blank>") "" else line)
                        input.expires = System.currentTimeMillis() + 600000
                    }
                    else -> error("input begin | append <linha> | clear")
                }
                source.sendSystemMessage(Component.literal("Entrada: ${inputs[player.uuid]?.text?.length ?: 0} caracteres"))
            }
            "team" -> {
                val (id, difficulty, operation) = parts(text, 3)
                updateDifficulty(id, difficulty) { d -> when (operation) {
                    "clear" -> d.copy(team = emptyList())
                    "add" -> d.copy(team = d.team + PokemonSpec())
                    else -> error("team <id> <dificuldade> add|clear")
                } }
            }
            "pokemon" -> {
                val (id, difficulty, slotText, json) = parts(text, 4)
                val slot = slotText.toInt() - 1
                val spec = PokemonAdapter.normalize(mod.gson.fromJson(StrictJson.parse(if (json == "buffer") buffer() else json), PokemonSpec::class.java))
                updateDifficulty(id, difficulty) { d ->
                    require(slot in d.team.indices)
                    d.copy(team = d.team.toMutableList().also { it[slot] = spec })
                }
            }
            "remove" -> {
                val (id, difficulty, slot) = parts(text, 3)
                updateDifficulty(id, difficulty) { d ->
                    require(slot.toInt() - 1 in d.team.indices)
                    d.copy(team = d.team.filterIndexed { index, _ -> index != slot.toInt() - 1 })
                }
            }
            "copy" -> {
                val p = parts(text, 5)
                val from = trainer(p[0]).difficulties.first { it.id == p[1] }.team[p[2].toInt() - 1]
                updateDifficulty(p[3], p[4]) { it.copy(team = it.team + from.copy(ivs = from.ivs.toMap(), evs = from.evs.toMap(), moves = from.moves.toList())) }
            }
            "difficulty" -> {
                val (id, difficulty) = parts(text, 2)
                val t = trainer(id)
                require(t.difficulties.none { it.id == difficulty })
                mod.save(t.copy(difficulties = t.difficulties + Difficulty(id = difficulty)), actor)
            }
            "settings" -> {
                val (id, difficulty, json) = parts(text, 3)
                updateDifficulty(id, difficulty) { d -> merge(d, if (json == "buffer") buffer() else json, Difficulty::class.java).also { require(it.id == d.id) } }
            }
            "requirements" -> {
                val (id, difficulty, json) = parts(text, 3)
                updateDifficulty(id, difficulty) { it.copy(requirements = merge(it.requirements, if (json == "buffer") buffer() else json, Requirements::class.java)) }
            }
            "rewardgroup" -> {
                val (id, difficulty, outcome, groupId, mode) = parts(text, 5)
                require(outcome in setOf("win", "loss"))
                updateDifficulty(id, difficulty) { d ->
                    val groups = if (outcome == "win") d.winRewards else d.lossRewards
                    val updated = if (groups.any { it.id == groupId }) groups.map { if (it.id == groupId) it.copy(mode = GroupMode.valueOf(mode.uppercase())) else it }
                        else groups + RewardGroup(groupId, GroupMode.valueOf(mode.uppercase()))
                    if (outcome == "win") d.copy(winRewards = updated) else d.copy(lossRewards = updated)
                }
            }
            "reward" -> {
                val values = parts(text, 6)
                val (id, difficulty, outcome, groupId, rewardId) = values
                val json = values[5]
                require(outcome in setOf("win", "loss"))
                updateDifficulty(id, difficulty) { d ->
                    val groups = if (outcome == "win") d.winRewards else d.lossRewards
                    require(groups.any { it.id == groupId }) { "Crie o grupo com rewardgroup primeiro" }
                    val updated = groups.map { group -> if (group.id != groupId) group else {
                        val existing = group.rewards.firstOrNull { it.id == rewardId } ?: Reward(rewardId, RewardKind.ITEM, "minecraft:diamond")
                        val reward = merge(existing, if (json == "buffer") buffer() else json, Reward::class.java)
                        require(reward.id == rewardId)
                        group.copy(rewards = group.rewards.filterNot { it.id == rewardId } + reward)
                    } }
                    if (outcome == "win") d.copy(winRewards = updated) else d.copy(lossRewards = updated)
                }
            }
            "rewardremove" -> {
                val (id, difficulty, outcome, groupId, rewardId) = parts(text, 5)
                require(outcome in setOf("win", "loss"))
                updateDifficulty(id, difficulty) { d ->
                    val groups = (if (outcome == "win") d.winRewards else d.lossRewards).map {
                        if (it.id == groupId) it.copy(rewards = it.rewards.filterNot { it.id == rewardId }) else it
                    }
                    if (outcome == "win") d.copy(winRewards = groups) else d.copy(lossRewards = groups)
                }
            }
            "dialogue" -> {
                val (id, event, value) = parts(text, 3)
                val t = trainer(id)
                mod.save(t.copy(dialogues = t.dialogues + (event to (if (value == "buffer") buffer().lines() else value.split("|")))), actor)
            }
            "import" -> {
                val (id, difficulty) = parts(text, 2)
                val team = Showdown.parse(buffer(), PokemonAdapter::resolveSpecies).map(PokemonAdapter::normalize)
                updateDifficulty(id, difficulty) { it.copy(team = team) }
            }
            "export" -> {
                val (id, difficulty) = parts(text, 2)
                val team = trainer(id).difficulties.first { it.id == difficulty }.team
                val result = Showdown.export(team, itemLabel = { net.minecraft.resources.ResourceLocation.parse(PokemonAdapter.resolveItem(it)).path.replace('_', ' ') }) { p ->
                    val species = PokemonAdapter.species(p)
                    species.name + (p.form?.let { "-$it" } ?: "")
                }
                source.sendSystemMessage(Component.literal(result))
            }
            "template" -> {
                val (operation, name, id, difficulty) = parts(text, 4)
                require(validId(name))
                val path = mod.store.root.resolve("templates/$name.json")
                when (operation) {
                    "save" -> mod.store.write(path, TeamTemplate(trainer(id).difficulties.first { it.id == difficulty }.team))
                    "load" -> {
                        val template = mod.store.read(path, TeamTemplate::class.java) ?: error("Modelo inexistente")
                        updateDifficulty(id, difficulty) { it.copy(team = template.team) }
                    }
                    else -> error("template save|load <nome> <id> <dificuldade>")
                }
                mod.audit(actor, "template $operation $name $id $difficulty")
            }
            "battle" -> {
                val (playerName, trainerId) = parts(text, 2)
                startBattle(source, playerName, trainerId)
            }
            "data" -> {
                val id = UUID.fromString(text.trim())
                source.sendSystemMessage(Component.literal(mod.gson.toJson(mod.store.loadPlayer(id))))
            }
            "claim" -> { mod.deliver(source.playerOrException); source.sendSystemMessage(Component.literal("Recompensas pendentes processadas; use /trainerstatus para consultar.")) }
            "reset" -> {
                val (uuid, confirmation) = parts(text, 2)
                val id = UUID.fromString(uuid)
                require(confirmation == "confirm") { "Use reset <uuid> confirm" }
                require(mod.ledger.sessions.values.none { it.player == id }) { "Jogador possui batalha ativa" }
                mod.store.resetPlayer(id)
                mod.audit(actor, "reset $id")
            }
            "objective" -> {
                val (uuid, objective, mode) = parts(text, 3)
                val id = UUID.fromString(uuid)
                require(validId(objective))
                val progress = mod.store.loadPlayer(id)
                when (mode) { "grant" -> progress.objectives.add(objective); "revoke" -> progress.objectives.remove(objective); else -> error("Use grant|revoke") }
                mod.store.savePlayer(progress); mod.audit(actor, "objective $id $objective $mode")
            }
            "delivery" -> {
                val (uuid, deliveryId, resolution) = parts(text, 3)
                val progress = mod.store.loadPlayer(UUID.fromString(uuid))
                val delivery = progress.deliveries[deliveryId] ?: error("Entrega inexistente")
                require(delivery.state in setOf(DeliveryState.NEEDS_REVIEW, DeliveryState.IN_FLIGHT)) { "Entrega não requer revisão" }
                when (resolution) {
                    "retry_confirm" -> delivery.state = DeliveryState.PENDING
                    "delivered_confirm" -> delivery.state = DeliveryState.DELIVERED
                    else -> error("Após verificar inventário/comandos: retry_confirm ou delivered_confirm")
                }
                mod.store.savePlayer(progress); mod.audit(actor, "delivery $uuid $deliveryId $resolution")
                mod.server.playerList.getPlayer(progress.uuid)?.let(mod::deliver)
            }
            "reload" -> { mod.reload(); mod.audit(actor, "reload") }
            "retryresults" -> {
                mod.ledger.sessions.values.toList().filter { com.cobblemon.mod.common.battles.BattleRegistry.getBattle(it.id) == null }.forEach {
                    val saved = mod.store.read(mod.store.resolutionPath(it.id), BattleResolution::class.java)
                    mod.finish(it.id, saved?.outcome ?: Outcome.ABORTED)
                }
                mod.audit(actor, "retryresults")
            }
            "debug" -> {
                require(text in setOf("on", "off")); mod.debug = text == "on"
                mod.audit(actor, "debug $text")
            }
            else -> error("Ação desconhecida")
        }
        if (action !in setOf("help", "show", "data", "export", "input")) source.sendSystemMessage(Component.literal("§aOperação concluída."))
    }
    private fun startBattle(source: CommandSourceStack, playerName: String, trainerId: String) {
        val player = mod.server.playerList.getPlayerByName(playerName) ?: error("Jogador não está online: $playerName")
        mod.challenge(player, trainerId, null)
        mod.audit(source.textName, "battle $playerName $trainerId")
    }
    private fun <T> merge(base: T, text: String, type: Class<T>): T {
        val json = com.google.gson.GsonBuilder().serializeNulls().create().toJsonTree(base).asJsonObject
        val patch = StrictJson.parse(text).asJsonObject
        require(patch.keySet().all { json.has(it) }) { "Campo desconhecido: ${patch.keySet() - json.keySet()}" }
        patch.entrySet().forEach { json.add(it.key, it.value) }
        return mod.gson.fromJson(json, type)
    }
    data class TeamTemplate(val team: List<PokemonSpec>)
    companion object {
        val ACTIONS = listOf("npc", "help", "create", "edit", "name", "config", "show", "input", "team", "pokemon", "remove", "copy", "difficulty", "settings", "requirements", "rewardgroup", "reward", "rewardremove", "dialogue", "import", "export", "template", "battle", "data", "reset", "objective", "delivery", "claim", "reload", "retryresults", "debug")
        val HELP = """
            /traineradmin create <id> | edit <id> | name <id> <nome>
            /traineradmin team <id> <dificuldade> add|clear
            /traineradmin pokemon <id> <dificuldade> <slot 1..6> <JSON|buffer>
            /traineradmin remove <id> <dificuldade> <slot>
            /traineradmin copy <origem> <dificuldade> <slot> <destino> <dificuldade>
            /traineradmin difficulty <id> <nova_dificuldade>
            /traineradmin settings|requirements <id> <dificuldade> <JSON parcial|buffer>
            /traineradmin rewardgroup <id> <dificuldade> win|loss <grupo> <modo>
            /traineradmin reward <id> <dificuldade> win|loss <grupo> <recompensa> <JSON parcial|buffer>
            /traineradmin rewardremove <id> <dificuldade> win|loss <grupo> <recompensa>
            /traineradmin dialogue <id> <evento> <linhas separadas por | ou buffer>
            /traineradmin input begin | append <linha ou <blank>> | clear
            /traineradmin import <id> <dificuldade> — lê buffer Showdown
            /traineradmin export <id> <dificuldade>
            /traineradmin template save|load <nome> <id> <dificuldade>
            /traineradmin config <id> <JSON|buffer> | show <id>
            /traineradmin <jogador> battle <id_da_luta>
            /traineradmin battle <jogador> <id_da_luta>
            /traineradmin data <uuid> | reset <uuid> confirm
            /traineradmin objective <uuid> <objetivo> grant|revoke
            /traineradmin delivery <uuid> <id_entrega> retry_confirm|delivered_confirm
            /traineradmin reload | debug on|off
        """.trimIndent()
    }
}
