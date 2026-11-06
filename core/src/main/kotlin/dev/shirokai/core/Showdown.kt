package dev.shirokai.core

/** Text interchange for the fields supported by the editor; unknown fields fail explicitly. */
object Showdown {
    private val labels = linkedMapOf("HP" to "hp", "Atk" to "attack", "Def" to "defence",
        "SpA" to "special_attack", "SpD" to "special_defence", "Spe" to "speed")
    fun id(s: String) = s.lowercase().replace(Regex("[^a-z0-9]"), "")
    fun parse(text: String, resolveSpecies: (String) -> Pair<String, String?>): List<PokemonSpec> {
        require(text.length <= 24000) { "Equipe muito longa" }
        val normalized = text.replace("\r", "").trim()
        require(normalized.isNotEmpty())
        val blocks = normalized.split(Regex("\n\\s*\n"))
        require(blocks.size in 1..6) { "Equipe deve conter de 1 a 6 Pokémon" }
        return blocks.map { block ->
            val lines = block.lines().map { it.trim() }.filter { it.isNotEmpty() }
            val header = lines.first().split(" @ ", limit = 2)
            var speciesName = header[0].removeSuffix(" (M)").removeSuffix(" (F)")
            if (speciesName.endsWith(')') && " (" in speciesName) speciesName = speciesName.substringAfterLast(" (").dropLast(1)
            val species = resolveSpecies(speciesName)
            var p = PokemonSpec(species.first, species.second, level = 100,
                heldItem = header.getOrNull(1)?.let { if (':' in it) it.trim() else id(it) }, moves = emptyList())
            val seen = mutableSetOf<String>()
            lines.drop(1).forEach { line ->
                val key = when {
                    line.startsWith("- ") -> "move"
                    line.endsWith(" Nature") -> "Nature"
                    else -> line.substringBefore(":")
                }
                if (key != "move") require(seen.add(key)) { "Campo duplicado: $key" }
                p = when (key) {
                    "move" -> p.copy(moves = p.moves + id(line.removePrefix("- ")))
                    "Ability" -> p.copy(ability = id(line.substringAfter(":").trim()))
                    "Level" -> p.copy(level = line.substringAfter(":").trim().toInt())
                    "Shiny" -> {
                        require(line.substringAfter(":").trim() in listOf("Yes", "No"))
                        p.copy(shiny = line.substringAfter(":").trim() == "Yes")
                    }
                    "Nature" -> p.copy(nature = id(line.removeSuffix(" Nature")))
                    "EVs" -> p.copy(evs = stats(line.substringAfter(":"), 0))
                    "IVs" -> p.copy(ivs = stats(line.substringAfter(":"), 31))
                    else -> error("Campo Showdown não suportado: $line")
                }
            }
            p.validate()
            p
        }
    }
    private fun stats(text: String, default: Int): Map<String, Int> {
        val result = PokemonSpec.STATS.associateWith { default }.toMutableMap()
        val seen = mutableSetOf<String>()
        text.trim().split('/').forEach { entry ->
            val match = Regex("(\\d+)\\s+(HP|Atk|Def|SpA|SpD|Spe)").matchEntire(entry.trim())
                ?: error("Estatística inválida: $entry")
            val stat = labels.getValue(match.groupValues[2])
            require(seen.add(stat)) { "Estatística duplicada" }
            result[stat] = match.groupValues[1].toInt()
        }
        return result
    }
    fun export(team: List<PokemonSpec>, speciesLabel: (PokemonSpec) -> String = { it.species }): String = team.joinToString("\n\n") { p ->
        p.validate()
        buildString {
            append(speciesLabel(p)); p.heldItem?.let { append(" @ $it") }; append('\n')
            p.ability?.let { append("Ability: $it\n") }
            append("Level: ${p.level}\n")
            if (p.shiny) append("Shiny: Yes\n")
            append("${p.nature.replaceFirstChar { it.uppercase() }} Nature\n")
            append("EVs: " + labels.entries.joinToString(" / ") { "${p.evs[it.value] ?: 0} ${it.key}" } + "\n")
            append("IVs: " + labels.entries.joinToString(" / ") { "${p.ivs[it.value] ?: 31} ${it.key}" } + "\n")
            p.moves.forEach { append("- $it\n") }
        }.trimEnd()
    }
}
