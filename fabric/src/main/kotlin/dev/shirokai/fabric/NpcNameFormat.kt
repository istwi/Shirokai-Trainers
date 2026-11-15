package dev.shirokai.fabric

import net.minecraft.ChatFormatting
import net.minecraft.network.chat.Component
import net.minecraft.network.chat.Style

/** Store actual component styles so nameplates retain formatting in entity NBT. */
internal fun formattedNpcName(text: String): Component {
    val result = Component.empty()
    var style = Style.EMPTY
    var start = 0
    for (match in Regex("[&§]([0-9a-fk-or])", RegexOption.IGNORE_CASE).findAll(text)) {
        if (match.range.first > start) {
            result.append(Component.literal(text.substring(start, match.range.first)).setStyle(style))
        }
        val format = requireNotNull(ChatFormatting.getByCode(match.groupValues[1].lowercase()[0]))
        style = (if (format.isColor || format == ChatFormatting.RESET) Style.EMPTY else style).applyFormat(format)
        start = match.range.last + 1
    }
    if (start < text.length) result.append(Component.literal(text.substring(start)).setStyle(style))
    return result
}
