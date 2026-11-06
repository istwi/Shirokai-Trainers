package dev.shirokai.fabric

import dev.shirokai.core.*
import net.minecraft.core.component.DataComponents
import net.minecraft.network.chat.Component
import net.minecraft.server.level.ServerPlayer
import net.minecraft.world.SimpleContainer
import net.minecraft.world.SimpleMenuProvider
import net.minecraft.world.entity.player.Inventory
import net.minecraft.world.entity.player.Player
import net.minecraft.world.inventory.ChestMenu
import net.minecraft.world.inventory.ClickType
import net.minecraft.world.inventory.MenuType
import net.minecraft.world.item.Item
import net.minecraft.world.item.ItemStack
import net.minecraft.world.item.Items

/** Vanilla chest screens; no client code or custom packets. All clicks are consumed. */
class TrainerMenus(private val mod: ShirokaiTrainers) {
    private data class Button(val item: Item, val title: String, val click: (Int) -> Unit)
    private fun open(player: ServerPlayer, title: String, buttons: Map<Int, Button>, administrative: Boolean) {
        val inventory = SimpleContainer(54)
        buttons.forEach { (slot, button) -> inventory.setItem(slot, ItemStack(button.item).also {
            it.set(DataComponents.CUSTOM_NAME, Component.literal(button.title))
        }) }
        player.openMenu(SimpleMenuProvider({ id, inv, _ -> object : ChestMenu(MenuType.GENERIC_9x6, id, inv, inventory, 6) {
            override fun stillValid(p: Player) = !administrative || mod.admin(player.createCommandSourceStack())
            override fun quickMoveStack(p: Player, slot: Int): ItemStack = ItemStack.EMPTY
            override fun clicked(slot: Int, button: Int, type: ClickType, p: Player) {
                if (p.uuid != player.uuid || (administrative && !mod.admin(player.createCommandSourceStack()))) { player.closeContainer(); return }
                if (type != ClickType.PICKUP || button !in 0..1) return
                try { buttons[slot]?.click?.invoke(button) } catch (e: Exception) {
                    player.sendSystemMessage(Component.literal("§c${e.message}"))
                    if (mod.debug) mod.log.error("Falha em menu", e)
                }
                broadcastChanges()
            }
        } }, Component.literal(title)))
    }
    fun list(player: ServerPlayer, admin: Boolean = false, page: Int = 0) {
        val trainers = mod.trainers.values.sortedBy { it.id }
        val buttons = mutableMapOf<Int, Button>()
        trainers.drop(page * 45).take(45).forEachIndexed { i, t ->
            buttons[i] = Button(Items.PLAYER_HEAD, t.name) { if (admin) trainer(player, t) else difficulties(player, t) }
        }
        if (page > 0) buttons[45] = Button(Items.ARROW, "Anterior") { list(player, admin, page - 1) }
        if (trainers.size > (page + 1) * 45) buttons[53] = Button(Items.ARROW, "Próxima") { list(player, admin, page + 1) }
        if (admin) buttons[49] = Button(Items.WRITABLE_BOOK, "Criar: /traineradmin create <id>") {
            player.closeContainer(); player.sendSystemMessage(Component.literal("/traineradmin create <id>"))
        }
        open(player, if (admin) "Administrar treinadores" else "Desafiar treinador", buttons, admin)
    }
    private fun difficulties(player: ServerPlayer, trainer: Trainer, page: Int = 0) {
        val buttons = trainer.difficulties.drop(page * 45).take(45).mapIndexed { i, d -> i to Button(Items.IRON_SWORD, d.id) {
            player.closeContainer(); mod.challenge(player, trainer.id, d.id)
        } }.toMap().toMutableMap()
        if (page > 0) buttons[45] = Button(Items.ARROW, "Anterior") { difficulties(player, trainer, page - 1) }
        if (trainer.difficulties.size > (page + 1) * 45) buttons[53] = Button(Items.ARROW, "Próxima") { difficulties(player, trainer, page + 1) }
        buttons[49] = Button(Items.BARRIER, "Voltar") { list(player) }
        open(player, trainer.name, buttons, false)
    }
    fun trainer(player: ServerPlayer, old: Trainer, difficulty: String = old.difficulties.first().id) {
        val t = mod.trainers[old.id] ?: error("Treinador removido")
        val d = t.difficulties.first { it.id == difficulty }
        val buttons = mutableMapOf<Int, Button>()
        d.team.forEachIndexed { i, p -> buttons[10 + i] = Button(Items.EGG, "${i + 1}. ${p.species} Nv.${p.level}") { pokemon(player, t, d, i) } }
        fun save(updated: Trainer) {
            require(mod.trainers[t.id] == t) { "Treinador alterado por outro administrador; reabra o menu" }
            mod.save(updated, player.scoreboardName); trainer(player, updated, difficulty)
        }
        if (d.team.size < 6) buttons[16] = Button(Items.EMERALD, "Adicionar Pokémon") {
            save(t.copy(difficulties = t.difficulties.map { if (it.id == d.id) it.copy(team = it.team + PokemonSpec()) else it }))
        }
        buttons[28] = Button(Items.CLOCK, "Cooldown: ${d.cooldownSeconds}s (±30)") { button ->
            save(t.copy(difficulties = t.difficulties.map { if (it.id == d.id) it.copy(cooldownSeconds = (d.cooldownSeconds + if (button == 0) 30 else -30).coerceIn(0, 315360000)) else it }))
        }
        buttons[29] = Button(Items.COMPARATOR, "Simultâneas: ${t.simultaneous}") { save(t.copy(simultaneous = !t.simultaneous)) }
        buttons[30] = Button(Items.REDSTONE_TORCH, "Ativo: ${t.enabled}") { save(t.copy(enabled = !t.enabled)) }
        buttons[31] = Button(Items.GOLD_INGOT, "Ginásio: ${t.gym}") { save(t.copy(gym = !t.gym)) }
        buttons[32] = Button(Items.REPEATER, "Dificuldade automática: ${t.automaticDifficulty}") { save(t.copy(automaticDifficulty = !t.automaticDifficulty)) }
        buttons[33] = Button(Items.BOOK, "Dificuldade: ${d.id} (clicar para alternar)") {
            trainer(player, t, t.difficulties[(t.difficulties.indexOf(d) + 1) % t.difficulties.size].id)
        }
        buttons[34] = Button(Items.ENDER_EYE, "IA: ${d.skill} (±1)") { button ->
            save(t.copy(difficulties = t.difficulties.map { if (it.id == d.id) it.copy(skill = (d.skill + if (button == 0) 1 else -1).coerceIn(0, 5)) else it }))
        }
        buttons[40] = Button(Items.WRITABLE_BOOK, "Texto, recompensas, requisitos: comandos administrativos") {
            player.closeContainer(); player.sendSystemMessage(Component.literal(TrainerCommands.HELP))
        }
        buttons[49] = Button(Items.BARRIER, "Voltar") { list(player, true) }
        open(player, "${t.name} / ${d.id}", buttons, true)
    }
    private fun pokemon(player: ServerPlayer, old: Trainer, previous: Difficulty, index: Int) {
        val t = mod.trainers.getValue(old.id)
        val d = t.difficulties.first { it.id == previous.id }
        val p = d.team.getOrNull(index) ?: error("Pokémon removido")
        val buttons = mutableMapOf<Int, Button>()
        fun save(spec: PokemonSpec?) {
            require(mod.trainers[t.id] == t) { "Treinador alterado por outro administrador; reabra o menu" }
            val team = d.team.toMutableList()
            if (spec == null) team.removeAt(index) else team[index] = spec
            val updated = t.copy(difficulties = t.difficulties.map { if (it.id == d.id) it.copy(team = team) else it })
            mod.save(updated, player.scoreboardName)
            if (spec == null) trainer(player, updated, d.id) else pokemon(player, updated, d, index)
        }
        buttons[4] = Button(Items.EGG, "${p.species} / ${p.form ?: "padrão"}") {
            player.closeContainer(); player.sendSystemMessage(Component.literal("/traineradmin pokemon ${t.id} ${d.id} ${index + 1} <JSON completo ou buffer>\n" + mod.gson.toJson(p)))
        }
        buttons[10] = Button(Items.EXPERIENCE_BOTTLE, "Nível ${p.level} (±1)") { save(p.copy(level = (p.level + if (it == 0) 1 else -1).coerceIn(1, 100))) }
        buttons[11] = Button(Items.NETHER_STAR, "Shiny: ${p.shiny}") { save(p.copy(shiny = !p.shiny)) }
        PokemonSpec.STATS.forEachIndexed { i, stat ->
            buttons[19 + i] = Button(Items.IRON_INGOT, "IV $stat: ${p.ivs[stat] ?: 31} (±1)") { button ->
                save(p.copy(ivs = p.ivs + (stat to ((p.ivs[stat] ?: 31) + if (button == 0) 1 else -1).coerceIn(0, 31))))
            }
            buttons[28 + i] = Button(Items.GOLD_INGOT, "EV $stat: ${p.evs[stat] ?: 0} (±1)") { button ->
                save(p.copy(evs = p.evs + (stat to ((p.evs[stat] ?: 0) + if (button == 0) 1 else -1).coerceIn(0, 252))))
            }
        }
        buttons[37] = Button(Items.WRITABLE_BOOK, "Nature: ${p.nature}; Ability: ${p.ability ?: "auto"}; movimentos/item: editar JSON") {
            player.closeContainer(); player.sendSystemMessage(Component.literal("/traineradmin pokemon ${t.id} ${d.id} ${index + 1} <JSON completo ou buffer>\n" + mod.gson.toJson(p)))
        }
        buttons[43] = Button(Items.BARRIER, "Remover Pokémon") { save(null) }
        buttons[49] = Button(Items.ARROW, "Voltar") { trainer(player, t, d.id) }
        open(player, "Pokémon ${index + 1} — ${d.id}", buttons, true)
    }
}
