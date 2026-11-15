package dev.shirokai.core

import org.junit.jupiter.api.Test
import kotlin.test.assertEquals

class DurationFormatTest {
    @Test fun `cooldowns display hours minutes and remaining seconds`() {
        mapOf(0L to "0s", 59L to "59s", 60L to "1min", 300L to "5min",
            3599L to "59min 59s", 3600L to "1h", 3601L to "1h 1s",
            86000L to "23h 53min 20s", 86400L to "24h").forEach { (seconds, expected) ->
            assertEquals(expected, formatDuration(seconds))
        }
    }
}
