package dev.shirokai.core

import com.google.gson.JsonArray
import com.google.gson.JsonObject
import java.awt.image.BufferedImage
import java.io.ByteArrayOutputStream
import java.net.InetAddress
import java.util.Base64
import javax.imageio.ImageIO
import org.junit.jupiter.api.Test
import kotlin.test.*

class RemoteSkinsTest {
    private fun png(width: Int = 64, height: Int = 64) = ByteArrayOutputStream().also {
        ImageIO.write(BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB), "png", it)
    }.toByteArray()
    private fun session(slim: Boolean): ByteArray {
        val skin = JsonObject().apply {
            addProperty("url", "http://textures.minecraft.net/texture/test")
            if (slim) add("metadata", JsonObject().apply { addProperty("model", "slim") })
        }
        val data = JsonObject().apply { add("textures", JsonObject().apply { add("SKIN", skin) }) }
        val property = JsonObject().apply {
            addProperty("name", "textures")
            addProperty("value", Base64.getEncoder().encodeToString(data.toString().toByteArray()))
        }
        return JsonObject().apply { add("properties", JsonArray().apply { add(property) }) }.toString().toByteArray()
    }
    @Test fun `nickname resolves official APIs and upgrades skin URL to HTTPS with correct arm model`() {
        listOf(false, true).forEach { slim ->
            val calls = mutableListOf<String>()
            val image = png()
            val loader = RemoteSkins { uri, _ ->
                calls += uri.toString()
                when (uri.host) {
                    "api.mojang.com" -> "{\"id\":\"0123456789abcdef0123456789abcdef\"}".toByteArray()
                    "sessionserver.mojang.com" -> session(slim)
                    "textures.minecraft.net" -> image
                    else -> error("Unexpected host")
                }
            }
            val result = loader.player("Notch")
            assertEquals(slim, result.slim); assertContentEquals(image, result.bytes)
            assertEquals(listOf(
                "https://api.mojang.com/users/profiles/minecraft/Notch",
                "https://sessionserver.mojang.com/session/minecraft/profile/0123456789abcdef0123456789abcdef",
                "https://textures.minecraft.net/texture/test"
            ), calls)
        }
    }
    @Test fun `direct URL validates skin content and preserves selected model`() {
        val result = RemoteSkins { _, limit -> assertEquals(RemoteSkins.MAX_BYTES, limit); png(64, 32) }
            .url("https://example.com/skin.png", true)
        assertTrue(result.slim)
        assertFailsWith<IllegalArgumentException> { RemoteSkins { _, _ -> "<html>Error</html>".toByteArray() }.url("https://example.com/page", false) }
        assertFailsWith<IllegalArgumentException> { RemoteSkins.validatePng(png(128, 128)) }
        assertFailsWith<IllegalArgumentException> { RemoteSkins.validatePng(ByteArray(RemoteSkins.MAX_BYTES + 1)) }
    }
    @Test fun `invalid nick and URL fail without starting network requests`() {
        val loader = RemoteSkins { _, _ -> error("Must not download") }
        assertFailsWith<IllegalArgumentException> { loader.player("bad/name") }
        assertFailsWith<IllegalArgumentException> { loader.player("a".repeat(17)) }
        listOf("file:///etc/passwd", "http://example.com/a", "https://user:pass@example.com/a", "https://example.com:8443/a").forEach {
            assertFailsWith<IllegalArgumentException> { loader.url(it, false) }
        }
    }
    @Test fun `missing profile skin or invalid profile response fails cleanly`() {
        assertFailsWith<IllegalStateException> { RemoteSkins { _, _ -> "{}".toByteArray() }.player("Notch") }
        assertFailsWith<IllegalArgumentException> { RemoteSkins { _, _ -> "{\"id\":\"../bad\"}".toByteArray() }.player("Notch") }
        val loader = RemoteSkins { uri, _ -> if (uri.host == "api.mojang.com")
            "{\"id\":\"0123456789abcdef0123456789abcdef\"}".toByteArray() else "{\"properties\":[]}".toByteArray() }
        assertFailsWith<IllegalStateException> { loader.player("Notch") }
    }
    @Test fun `private loopback and metadata addresses are excluded from URL downloads`() {
        listOf("127.0.0.1", "10.0.0.1", "192.168.1.1", "169.254.169.254", "100.64.0.1", "::1", "fc00::1", "fe80::1").forEach {
            assertFalse(RemoteSkins.isPublic(InetAddress.getByName(it)), it)
        }
        assertTrue(RemoteSkins.isPublic(InetAddress.getByName("1.1.1.1")))
    }
}
