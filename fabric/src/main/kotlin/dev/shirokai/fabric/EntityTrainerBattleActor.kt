package dev.shirokai.fabric

import com.cobblemon.mod.common.api.battles.model.actor.EntityBackedBattleActor
import com.cobblemon.mod.common.battles.actor.TrainerBattleActor
import com.cobblemon.mod.common.battles.ai.StrongBattleAI
import com.cobblemon.mod.common.battles.pokemon.BattlePokemon
import net.minecraft.nbt.CompoundTag
import net.minecraft.server.level.ServerLevel
import net.minecraft.world.entity.EntityType
import net.minecraft.world.entity.LivingEntity
import net.minecraft.world.entity.decoration.ArmorStand
import net.minecraft.world.phys.Vec3
import java.util.UUID

/** Cobblemon 1.8.3 requires an entity-backed actor for its initial SwitchInstruction. */
open class EntityTrainerBattleActor(
    name: String,
    pokemon: List<BattlePokemon>,
    skill: Int,
    override val entity: LivingEntity,
    private val ownsSource: Boolean = false
) : TrainerBattleActor(name, UUID.randomUUID(), pokemon, StrongBattleAI(skill)), EntityBackedBattleActor<LivingEntity> {
    override val initialPos: Vec3 = entity.position()

    fun cleanup() {
        // Only this session's independently created Pokémon, never the player's or NPC's party.
        try { pokemonList.forEach { it.effectedPokemon.recall() } }
        finally { if (ownsSource) entity.discard() }
    }

    companion object {
        fun anchor(level: ServerLevel, position: Vec3): LivingEntity {
            val anchor = object : ArmorStand(EntityType.ARMOR_STAND, level) {
                override fun shouldBeSaved() = false
            }
            anchor.load(CompoundTag().apply { putBoolean("Marker", true) })
            anchor.isInvisible = true
            anchor.isInvulnerable = true
            anchor.isNoGravity = true
            anchor.isSilent = true
            anchor.moveTo(position)
            check(level.addFreshEntity(anchor)) { "Não foi possível criar a origem temporária da batalha" }
            return anchor
        }
    }
}
