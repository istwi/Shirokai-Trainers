package dev.shirokai.core

/** Formats cooldown seconds without losing the remaining partial minute or hour. */
fun formatDuration(seconds: Long): String {
    val total = seconds.coerceAtLeast(0)
    return buildList {
        if (total >= 3600) add("${total / 3600}h")
        if (total % 3600 / 60 > 0) add("${total % 3600 / 60}min")
        if (total % 60 > 0 || total == 0L) add("${total % 60}s")
    }.joinToString(" ")
}
