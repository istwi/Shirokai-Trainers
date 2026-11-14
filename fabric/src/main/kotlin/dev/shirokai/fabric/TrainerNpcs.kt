package dev.shirokai.fabric

import com.cobblemon.mod.common.api.npc.NPCClasses
import com.cobblemon.mod.common.entity.npc.NPCEntity
import com.cobblemon.mod.common.entity.npc.NPCPlayerModelType
import com.cobblemon.mod.common.entity.npc.NPCPlayerTexture
import dev.shirokai.core.*
import net.fabricmc.fabric.api.event.player.UseEntityCallback
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents
import net.minecraft.commands.CommandSourceStack
import net.minecraft.core.registries.Registries
import net.minecraft.network.chat.Component
import net.minecraft.resources.ResourceKey
import net.minecraft.resources.ResourceLocation
import net.minecraft.server.level.ServerPlayer
import net.minecraft.world.InteractionHand
import net.minecraft.world.InteractionResult
import java.nio.file.Files
import java.util.UUID
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.ThreadPoolExecutor
import java.util.concurrent.TimeUnit
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents

class TrainerNpcs(private val mod: ShirokaiTrainers) {
    private val path = mod.store.root.resolve("npcs.json")
    var records: Map<String, TrainerNpc> = emptyMap(); private set
    private data class Selection(val id: String?, val trainer: String?, val expires: Long)
    private val selections = mutableMapOf<UUID, Selection>()
    private val clickTimes = mutableMapOf<UUID, Long>()

    private val skinRequests = mutableMapOf<UUID, UUID>()
    @Volatile private var skinsClosed = false
    private val skinDownloads = ThreadPoolExecutor(2, 2, 0L, TimeUnit.SECONDS, ArrayBlockingQueue<Runnable>(16),
        java.util.concurrent.ThreadFactory { task -> Thread(task, "Shirokai-Skins").apply { isDaemon = true } })

    fun load() {
        val registry = mod.store.read(path, NpcRegistry::class.java) { it.validate() } ?: NpcRegistry()
        records = registry.npcs.associateBy { it.id }
    }
    private fun commit(next: Map<String, TrainerNpc>) {
        val registry = NpcRegistry(npcs = next.values.toList()); registry.validate()
        mod.store.write(path, registry); records = next
    }
    private fun put(record: TrainerNpc) = commit(records + (record.id to record))
    private fun at(entity: NPCEntity, record: TrainerNpc) = record.copy(
        dimension = entity.level().dimension().location().toString(), x = entity.x, y = entity.y, z = entity.z)
    private fun record(id: String) = records[id]?.takeUnless { it.removed } ?: error("NPC inexistente/removido: $id")
    private fun trainer(id: String) { require(id in mod.trainers) { "Treinador inexistente: $id" } }

    fun register() {
        ServerLifecycleEvents.SERVER_STOPPING.register {
            skinsClosed = true; skinRequests.clear(); skinDownloads.shutdownNow()
        }
        ServerPlayConnectionEvents.DISCONNECT.register { h, _ -> selections.remove(h.player.uuid); clickTimes.remove(h.player.uuid) }
        ServerEntityEvents.ENTITY_LOAD.register { entity, _ ->
            if (entity is NPCEntity) records.values.find { it.entity == entity.uuid }?.let {
                if (it.removed) entity.discard()
                else if (at(entity, it) != it) runCatching { put(at(entity, it)) }
                    .onFailure { e -> mod.log.error("Falha ao atualizar índice do NPC {}", it.id, e) }
            }
        }
        ServerEntityEvents.ENTITY_UNLOAD.register { entity, _ ->
            if (entity is NPCEntity) records.values.find { it.entity == entity.uuid && !it.removed }?.let {
                if (at(entity, it) != it) runCatching { put(at(entity, it)) }
                    .onFailure { e -> mod.log.error("Falha ao salvar posição do NPC {}", it.id, e) }
            }
        }
        UseEntityCallback.EVENT.register { player, world, hand, entity, _ ->
            if (entity !is NPCEntity || world.isClientSide || player !is ServerPlayer) return@register InteractionResult.PASS
            val selected = selections[player.uuid]?.takeIf { it.expires >= System.currentTimeMillis() }
            if (selected == null) selections.remove(player.uuid)
            val linked = records.values.find { it.entity == entity.uuid }
            if (selected == null && linked == null) return@register InteractionResult.PASS
            // Consume both hands before NPCEntity.mobInteract, including its native editor/dialogue.
            if (hand != InteractionHand.MAIN_HAND) return@register InteractionResult.SUCCESS
            try {
                if (selected != null) {
                    require(mod.admin(player.createCommandSourceStack())) { "Permissão administrativa revogada" }
                    selections.remove(player.uuid)
                    if (selected.id == null) {
                        require(linked != null) { "NPC não vinculado" }
                        unlink(linked.id)
                    } else {
                        require(linked == null || linked.id == selected.id) { "Entidade já vinculada: ${linked?.id}" }
                        require(!entity.isInBattle()) { "NPC em batalha nativa; aguarde antes de vincular" }
                        trainer(selected.trainer!!)
                        val old = records[selected.id]
                        require(old == null || old.entity == entity.uuid) { "ID já usado; selecione outro ID" }
                        put(at(entity, old?.copy(trainer = selected.trainer) ?: TrainerNpc(selected.id, entity.uuid, false,
                            selected.trainer, world.dimension().location().toString(), entity.x, entity.y, entity.z)))
                    }
                    mod.audit(player.scoreboardName, "npc selection ${selected.id ?: "unlink"} ${entity.uuid}")
                    player.sendSystemMessage(Component.literal("§aVínculo atualizado."))
                } else if (linked != null) {
                    require(!linked.removed) { "NPC removido; aguardando limpeza da entidade" }
                    val trainerId = linked.trainer ?: error("NPC sem treinador vinculado")
                    trainer(trainerId)
                    require(player.isAlive && !player.isSpectator) { "Não é possível desafiar nesse estado" }
                    val now = System.currentTimeMillis()
                    if (now - (clickTimes[player.uuid] ?: 0L) >= 750) {
                        clickTimes[player.uuid] = now
                        player.sendSystemMessage(Component.literal(linked.message))
                        if (linked.confirm) TrainerMenus(mod).npcChallenge(player, linked)
                        else challenge(player, linked.id, entity.uuid)
                    }
                }
            } catch (e: Exception) { player.sendSystemMessage(Component.literal("§c${e.message}")) }
            InteractionResult.SUCCESS
        }
    }
    fun challenge(player: ServerPlayer, id: String, uuid: UUID) {
        val r = record(id)
        require(r.entity == uuid) { "Vínculo alterado; clique novamente" }
        val trainerId = r.trainer ?: error("NPC sem treinador vinculado")
        val entity = player.serverLevel().getEntity(uuid) as? NPCEntity ?: error("NPC indisponível neste mundo")
        require(!entity.isInBattle()) { "NPC ocupado em batalha nativa" }
        require(entity.isAlive && entity.distanceToSqr(player) <= 64.0) { "Aproxime-se do NPC" }
        mod.challenge(player, trainerId, null)
    }
    private fun entity(r: TrainerNpc): NPCEntity {
        // Never construct a replacement, even if the indexed chunk no longer contains this UUID.
        mod.server.allLevels.forEach { level -> (level.getEntity(r.entity) as? NPCEntity)?.let { return it } }
        val level = mod.server.getLevel(ResourceKey.create(Registries.DIMENSION, ResourceLocation.parse(r.dimension)))
            ?: error("Mundo indisponível: ${r.dimension}; vínculo preservado")
        level.getChunk(kotlin.math.floor(r.x).toInt() shr 4, kotlin.math.floor(r.z).toInt() shr 4)
        return level.getEntity(r.entity) as? NPCEntity
            ?: error("NPC removido ou não carregado em ${r.dimension} ${r.x}, ${r.y}, ${r.z}; índice preservado. Carregue o local e tente novamente")
    }
    fun unlink(id: String) {
        val r = record(id)
        if (r.owned) put(r.copy(trainer = null)) else commit(records - id)
    }
    fun command(source: CommandSourceStack, text: String) {
        require(mod.admin(source)) { "Sem permissão administrativa" }
        val args = text.trim().split(Regex("\\s+"), limit = 3)
        val action = args.firstOrNull().orEmpty()
        val id = args.getOrNull(1).orEmpty()
        val value = args.getOrNull(2).orEmpty()
        when (action) {
            "", "help" -> source.sendSystemMessage(Component.literal(HELP))
            "menu" -> TrainerMenus(mod).npcs(source.playerOrException)
            "list" -> source.sendSystemMessage(Component.literal(records.values.joinToString("\n") {
                "${it.id} → ${it.trainer ?: "sem vínculo"} [${if (it.removed) "removido" else if (it.owned) "próprio" else "externo"}] ${it.dimension} (${it.x}, ${it.y}, ${it.z})"
            }.ifEmpty { "Nenhum NPC registrado" }))
            "classes" -> source.sendSystemMessage(Component.literal(NPCClasses.classes.joinToString { it.id.toString() }))
            "cancel" -> selections.remove(source.playerOrException.uuid)
            "select" -> {
                val p = source.playerOrException
                require(validId(id) && id !in records) { "ID inválido ou já usado" }; trainer(value)
                selections[p.uuid] = Selection(id, value, System.currentTimeMillis() + 60000)
                source.sendSystemMessage(Component.literal("Clique direito em um NPC Cobblemon em até 60s. /traineradmin npc cancel cancela."))
            }
            "unselect" -> {
                selections[source.playerOrException.uuid] = Selection(null, null, System.currentTimeMillis() + 60000)
                source.sendSystemMessage(Component.literal("Clique no NPC para desvincular (60s)."))
            }
            "create" -> {
                val p = source.playerOrException
                require(validId(id) && id !in records) { "ID inválido ou já usado" }; trainer(value)
                val npcClass = NPCClasses.getByIdentifier(ResourceLocation.parse("cobblemon:standard"))
                    ?: error("Classe cobblemon:standard indisponível; verifique os datapacks")
                val npc = NPCEntity(p.serverLevel())
                npc.npc = npcClass; npc.initialize(1)
                npc.customName = Component.literal(id); npc.moveTo(p.x, p.y, p.z, p.yRot, p.xRot)
                npc.yHeadRot = p.yRot; npc.yBodyRot = p.yRot
                npc.setPersistenceRequired(); npc.setNoAi(true); npc.isMovable = false
                npc.setNoGravity(true); npc.isInvulnerable = true
                val r = TrainerNpc(id, npc.uuid, true, value, p.serverLevel().dimension().location().toString(), p.x, p.y, p.z)
                put(r) // Reserve identity before spawn; a crash leaves a visible missing record, never a duplicate.
                check(p.serverLevel().addFreshEntity(npc)) { "Não foi possível criar entidade; índice preservado para diagnóstico" }
            }
            "show" -> {
                val r = record(id)
                val status = runCatching { entity(r).let { "classe=${it.npc.id}, recurso=${it.resourceIdentifier}, aspectos=${it.aspects}" } }
                    .getOrElse { it.message.orEmpty() }
                source.sendSystemMessage(Component.literal(mod.gson.toJson(r) + "\n" + status))
            }
            "link" -> { trainer(value); put(record(id).copy(trainer = value)) }
            "unlink" -> unlink(id)
            "remove" -> {
                val r = record(id); require(r.owned) { "NPC externo: use unlink; entidade será preservada" }
                put(r.copy(removed = true, trainer = null)) // Tombstone survives missing/unloaded entities.
                runCatching { entity(r).discard() }.onFailure { source.sendSystemMessage(Component.literal("Remoção registrada; entidade será descartada quando carregar. ${it.message}")) }
            }
            "message", "confirmation", "confirm" -> {
                val r = record(id)
                val next = when (action) {
                    "message" -> r.copy(message = value)
                    "confirmation" -> r.copy(confirmation = value)
                    else -> r.copy(confirm = boolean(value))
                }
                put(next)
            }
            "skin" -> {
                skin(source, record(id), value)
                return
            }
            "name", "class", "resource", "aspects", "stationary", "move", "rotate" -> {
                val r = record(id); val npc = entity(r)
                when (action) {
                    "name" -> { require(value.isNotBlank() && value.length <= 200); npc.customName = Component.literal(value) }
                    "class" -> {
                        val name = npc.customName
                        npc.npc = NPCClasses.getByIdentifier(ResourceLocation.parse(value)) ?: error("Classe NPC inexistente; use npc classes")
                        npc.initialize(1); npc.customName = name
                    }
                    "resource" -> npc.forcedResourceIdentifier = if (value == "default") null else ResourceLocation.parse(value)
                    "aspects" -> {
                        val aspects = if (value == "clear") emptyList() else value.split(',')
                        require(aspects.all { it.matches(Regex("[a-z0-9_.=-]+")) }) { "Aspectos inválidos" }
                        npc.appliedAspects.clear(); npc.appliedAspects.addAll(aspects); npc.updateAspects()
                    }
                    "stationary" -> {
                        val stopped = boolean(value); npc.setNoAi(stopped); npc.isMovable = !stopped
                        npc.setNoGravity(stopped); npc.navigation.stop(); npc.deltaMovement = net.minecraft.world.phys.Vec3.ZERO
                    }
                    "rotate" -> {
                        val rotation = value.split(Regex("\\s+")); require(rotation.size in 1..2)
                        val yaw = rotation[0].toFloat(); val pitch = rotation.getOrNull(1)?.toFloat() ?: 0f
                        require(yaw.isFinite() && pitch.isFinite() && pitch in -90f..90f)
                        npc.moveTo(npc.x, npc.y, npc.z, yaw, pitch); npc.yHeadRot = yaw; npc.yBodyRot = yaw
                    }
                    "move" -> {
                        val p = source.playerOrException
                        require(value.isEmpty()) { "move usa a posição e dimensão do administrador" }
                        check(npc.teleportTo(p.serverLevel(), p.x, p.y, p.z, emptySet(), p.yRot, p.xRot)) { "Falha ao mover NPC" }
                    }
                }
                // Dimension transfer can replace an entity instance: resolve the UUID again before indexing.
                val current = mod.server.allLevels.firstNotNullOfOrNull { it.getEntity(r.entity) as? NPCEntity } ?: npc
                put(at(current, r))
            }
            else -> error("Ação NPC desconhecida. $HELP")
        }
        if (action !in setOf("", "help", "list", "show", "classes", "menu")) {
            mod.audit(source.textName, "npc $action $id")
            source.sendSystemMessage(Component.literal("§aOperação NPC concluída."))
        }
    }
    private fun boolean(value: String): Boolean = when (value) { "true" -> true; "false" -> false; else -> error("Use true ou false") }
    private fun applySkin(npc: NPCEntity, skin: SkinTexture) {
        val model = if (skin.slim) NPCPlayerModelType.SLIM else NPCPlayerModelType.DEFAULT
        npc.unloadTexture()
        npc.appliedAspects.add("model-${model.name.lowercase()}")
        npc.entityData.set(NPCEntity.NPC_PLAYER_TEXTURE, NPCPlayerTexture(skin.bytes, model))
        npc.updateAspects()
    }
    private fun skin(source: CommandSourceStack, record: TrainerNpc, value: String) {
        val npc = entity(record)
        val args = value.split(Regex("\\s+"))
        fun model(value: String): Boolean = when (value) {
            "default" -> false; "slim" -> true; else -> error("Modelo: default ou slim")
        }
        if (value == "clear") {
            skinRequests.remove(record.entity); npc.unloadTexture()
            mod.audit(source.textName, "npc skin clear ${record.id}")
            source.sendSystemMessage(Component.literal("§aSkin personalizada removida.")); return
        }
        val remote: (() -> SkinTexture)? = when (args.firstOrNull()) {
            "player", "nick" -> {
                require(args.size == 2 && args[1].matches(Regex("[A-Za-z0-9_]{1,16}"))) { "skin <npc> player <nick Minecraft>" }
                val load: () -> SkinTexture = { RemoteSkins().player(args[1]) }
                load
            }
            "url" -> {
                require(args.size in 2..3) { "skin <npc> url <https://imagem.png> [default|slim]" }
                val slim = model(args.getOrNull(2) ?: "default")
                RemoteSkins.validateUrl(java.net.URI(args[1]))
                val load: () -> SkinTexture = { RemoteSkins().url(args[1], slim) }
                load
            }
            else -> null
        }
        if (remote == null) {
            require(args.size == 2) { "skin <npc> <arquivo.png> default|slim; ou player <nick>; ou url <https://...> [default|slim]" }
            val slim = model(args[1])
            require(args[0].matches(Regex("[a-zA-Z0-9_-]+\\.png"))) { "Use nome PNG local, sem diretórios" }
            val root = mod.store.root.resolve("npc-skins"); Files.createDirectories(root)
            val file = root.resolve(args[0])
            require(!Files.isSymbolicLink(file) && Files.isRegularFile(file)) { "PNG ausente em $root" }
            require(Files.size(file) in 1..RemoteSkins.MAX_BYTES) { "PNG deve ter até 1 MiB" }
            val texture = SkinTexture(RemoteSkins.validatePng(Files.readAllBytes(file)), slim)
            skinRequests.remove(record.entity); applySkin(npc, texture)
            mod.audit(source.textName, "npc skin local ${record.id}")
            source.sendSystemMessage(Component.literal("§aSkin local aplicada.")); return
        }
        require(!skinsClosed) { "Servidor encerrando" }
        val request = UUID.randomUUID()
        skinRequests[record.entity] = request
        try {
            skinDownloads.execute {
                val result = runCatching { remote() }
                if (!skinsClosed) runCatching { mod.server.execute apply@ {
                    if (skinsClosed || skinRequests[record.entity] != request) return@apply
                    skinRequests.remove(record.entity)
                    if (source.player != null && mod.server.playerList.getPlayer(source.player!!.uuid) !== source.player) return@apply
                    try {
                        require(mod.admin(source)) { "Permissão administrativa revogada" }
                        val current = records[record.id]
                        require(current != null && !current.removed && current.entity == record.entity) { "NPC removido ou desvinculado durante o download" }
                        val texture = result.getOrThrow()
                        val loaded = mod.server.allLevels.firstNotNullOfOrNull { it.getEntity(record.entity) as? NPCEntity }
                            ?: error("NPC descarregado; carregue o local e tente novamente")
                        applySkin(loaded, texture)
                        mod.audit(source.textName, "npc skin remote ${record.id}")
                        source.sendSystemMessage(Component.literal("§aSkin aplicada ao NPC ${record.id}."))
                    } catch (e: Exception) {
                        source.sendFailure(Component.literal("Skin não alterada: ${e.message ?: e.javaClass.simpleName}"))
                    }
                } }
            }
        } catch (e: java.util.concurrent.RejectedExecutionException) {
            if (skinRequests[record.entity] == request) skinRequests.remove(record.entity)
            error("Fila de skins cheia; aguarde os downloads atuais")
        }
        source.sendSystemMessage(Component.literal("§eCarregando skin para ${record.id}; aguarde a confirmação."))
    }
    companion object {
        val HELP = """
            /traineradmin npc menu|list|classes|help
            /traineradmin npc create <npc> <treinador> | select <npc> <treinador>
            /traineradmin npc unselect|cancel
            /traineradmin npc show|unlink|remove|move <npc>
            /traineradmin npc link <npc> <treinador>
            /traineradmin npc name|class|resource|aspects|message|confirmation <npc> <valor>
            /traineradmin npc confirm|stationary <npc> true|false
            /traineradmin npc rotate <npc> <yaw> [pitch]
            /traineradmin npc skin <npc> <arquivo.png> default|slim (ou clear)
            /traineradmin npc skin <npc> player <nick> (ou nick <nick>)
            /traineradmin npc skin <npc> url <https://imagem.png> [default|slim]
        """.trimIndent()
    }
}
