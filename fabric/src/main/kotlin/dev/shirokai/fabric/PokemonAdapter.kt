package dev.shirokai.fabric

import com.cobblemon.mod.common.api.abilities.Abilities
import com.cobblemon.mod.common.api.moves.Moves
import com.cobblemon.mod.common.api.pokemon.Natures
import com.cobblemon.mod.common.api.pokemon.PokemonProperties
import com.cobblemon.mod.common.api.pokemon.PokemonSpecies
import com.cobblemon.mod.common.api.pokemon.stats.Stats
import com.cobblemon.mod.common.pokemon.EVs
import com.cobblemon.mod.common.pokemon.IVs
import com.cobblemon.mod.common.pokemon.Pokemon
import dev.shirokai.core.PokemonSpec
import dev.shirokai.core.Showdown
import net.minecraft.core.registries.BuiltInRegistries
import net.minecraft.resources.ResourceLocation
import net.minecraft.world.item.Items

object PokemonAdapter {
    fun species(spec: PokemonSpec) = PokemonSpecies.getByIdentifier(
        ResourceLocation.parse(if (':' in spec.species) spec.species else "cobblemon:${spec.species}"))
        ?: error("Espécie inválida: ${spec.species}")

    fun resolveSpecies(label: String): Pair<String, String?> {
        val token = Showdown.id(label)
        PokemonSpecies.species.forEach { species ->
            if (Showdown.id(species.name) == token || Showdown.id(species.resourceIdentifier.toString()) == token)
                return species.resourceIdentifier.toString() to null
            species.forms.forEach { form ->
                if (Showdown.id("${species.name}-${form.name}") == token || form.showdownId() == token)
                    return species.resourceIdentifier.toString() to form.name
            }
        }
        error("Espécie/forma Showdown desconhecida: $label")
    }

    fun resolveItem(label: String): String {
        if (':' in label) {
            val id = ResourceLocation.parse(label)
            require(BuiltInRegistries.ITEM.containsKey(id) && BuiltInRegistries.ITEM.get(id) != Items.AIR) { "Item inválido: $label" }
            return id.toString()
        }
        val matches = BuiltInRegistries.ITEM.keySet().filter { Showdown.id(it.path) == Showdown.id(label) }
        require(matches.size == 1) { "Item desconhecido ou ambíguo: $label; use namespace:id" }
        return matches.single().toString()
    }

    fun normalize(spec: PokemonSpec): PokemonSpec = spec.copy(heldItem = spec.heldItem?.let(::resolveItem))

    fun validate(spec: PokemonSpec) {
        spec.validate()
        val s = species(spec)
        require(s.implemented) { "Espécie não implementada: ${spec.species}" }
        require(spec.form == null || (s.forms + s.standardForm).any { it.name.equals(spec.form, true) }) { "Forma inválida: ${spec.form}" }
        require(Natures.getNature(spec.nature) != null) { "Nature inválida: ${spec.nature}" }
        spec.ability?.let { require(Abilities.get(it) != null) { "Ability inválida: $it" } }
        spec.moves.forEach { require(Moves.getByName(it) != null) { "Movimento inválido: $it" } }
        spec.heldItem?.let(::resolveItem)
    }

    fun create(spec: PokemonSpec): Pokemon {
        validate(spec)
        return PokemonProperties().apply {
            species = spec.species
            form = spec.form
            level = spec.level
            shiny = spec.shiny
            nature = spec.nature
            ability = spec.ability
            moves = spec.moves
            heldItem = spec.heldItem?.let(::resolveItem)
            ivs = IVs().also { values -> PokemonSpec.STATS.forEach { values[Stats.valueOf(it.uppercase())] = spec.ivs[it] ?: 31 } }
            evs = EVs().also { values -> PokemonSpec.STATS.forEach { values[Stats.valueOf(it.uppercase())] = spec.evs[it] ?: 0 } }
        }.create().also { pokemon ->
            require(pokemon.species.resourceIdentifier == species(spec).resourceIdentifier)
            require(spec.form == null || pokemon.form.name.equals(spec.form, true)) { "A forma não foi aplicada" }
            require(spec.ability == null || pokemon.ability.name == spec.ability) { "Ability não aplicada à espécie/forma" }
            pokemon.heal()
        }
    }
}
