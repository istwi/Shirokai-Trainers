package dev.shirokai.core

import java.net.HttpURLConnection
import java.net.InetAddress
import java.net.URI
import java.util.Base64
import javax.imageio.ImageIO

data class SkinTexture(val bytes: ByteArray, val slim: Boolean)

/** Downloads data only; entity mutation must happen on the Minecraft server thread. */
class RemoteSkins(private val read: (URI, Int) -> ByteArray = ::download) {
    fun player(name: String): SkinTexture {
        require(name.matches(Regex("[A-Za-z0-9_]{1,16}"))) { "Nick Minecraft inválido" }
        val profile = StrictJson.parse(String(read(URI("https://api.mojang.com/users/profiles/minecraft/$name"), 65536), Charsets.UTF_8)).asJsonObject
        val id = profile.get("id")?.asString ?: error("Jogador não encontrado na Mojang")
        require(id.matches(Regex("[a-fA-F0-9]{32}"))) { "UUID inválido na resposta da Mojang" }
        val session = StrictJson.parse(String(read(URI("https://sessionserver.mojang.com/session/minecraft/profile/$id"), 65536), Charsets.UTF_8)).asJsonObject
        val encoded = session.getAsJsonArray("properties")?.firstOrNull {
            it.asJsonObject.get("name")?.asString == "textures"
        }?.asJsonObject?.get("value")?.asString ?: error("Jogador sem textura de skin na Mojang")
        val texture = StrictJson.parse(String(Base64.getDecoder().decode(encoded), Charsets.UTF_8)).asJsonObject
            .getAsJsonObject("textures")?.getAsJsonObject("SKIN") ?: error("Jogador sem skin personalizada na Mojang")
        val raw = URI(texture.get("url")?.asString ?: error("Mojang não retornou URL da skin"))
        require(raw.host.equals("textures.minecraft.net", true) && raw.userInfo == null && raw.port == -1 && raw.scheme in setOf("http", "https")) {
            "Host de textura inesperado na resposta da Mojang"
        }
        val secure = URI("https", null, "textures.minecraft.net", -1, raw.path, null, null)
        return url(secure.toASCIIString(), texture.getAsJsonObject("metadata")?.get("model")?.asString == "slim")
    }

    fun url(value: String, slim: Boolean): SkinTexture {
        val uri = URI(value); validateUrl(uri)
        return SkinTexture(validatePng(read(uri, MAX_BYTES)), slim)
    }

    companion object {
        const val MAX_BYTES = 1_048_576
        fun validatePng(bytes: ByteArray): ByteArray {
            require(bytes.size in 1..MAX_BYTES) { "Skin deve ter até 1 MiB" }
            val signature = byteArrayOf(0x89.toByte(), 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)
            require(bytes.size >= 8 && bytes.copyOfRange(0, 8).contentEquals(signature)) { "Resposta não é uma skin PNG (use URL direta da imagem)" }
            ImageIO.createImageInputStream(bytes.inputStream()).use { input ->
                val readers = ImageIO.getImageReaders(input); require(readers.hasNext()) { "PNG inválido" }
                val reader = readers.next()
                try {
                    reader.input = input
                    require(reader.formatName.equals("png", true) && reader.getWidth(0) == 64 && reader.getHeight(0) in setOf(32, 64)) {
                        "Skin deve ser PNG 64x32 ou 64x64"
                    }
                    reader.read(0)
                } finally { reader.dispose() }
            }
            return bytes
        }
        fun validateUrl(uri: URI) {
            require(uri.toASCIIString().length <= 2048 && uri.scheme == "https" && !uri.host.isNullOrBlank() &&
                uri.userInfo == null && uri.fragment == null && uri.port in setOf(-1, 443)) { "Use URL HTTPS direta, sem credenciais, na porta padrão" }
        }
        internal fun isPublic(address: InetAddress): Boolean {
            val bytes = address.address
            val sharedIpv4 = bytes.size == 4 && (bytes[0].toInt() and 255) == 100 && (bytes[1].toInt() and 255) in 64..127
            val uniqueLocalIpv6 = bytes.size == 16 && (bytes[0].toInt() and 0xfe) == 0xfc
            return !address.isAnyLocalAddress && !address.isLoopbackAddress && !address.isLinkLocalAddress &&
                !address.isSiteLocalAddress && !address.isMulticastAddress && !sharedIpv4 && !uniqueLocalIpv6
        }
        private fun download(initial: URI, limit: Int): ByteArray {
            var uri = initial
            repeat(4) { hop ->
                validateUrl(uri)
                require(InetAddress.getAllByName(uri.host).all(::isPublic)) { "URL deve apontar para servidor público" }
                val connection = uri.toURL().openConnection() as HttpURLConnection
                connection.connectTimeout = 10000; connection.readTimeout = 10000
                connection.instanceFollowRedirects = false
                connection.setRequestProperty("User-Agent", "Shirokai-Trainers-Skins")
                try {
                    val status = connection.responseCode
                    if (status in setOf(301, 302, 303, 307, 308)) {
                        require(hop < 3) { "Redirecionamentos demais na URL" }
                        uri = uri.resolve(connection.getHeaderField("Location") ?: error("Redirecionamento sem destino"))
                    } else {
                        require(status == 200) { when (status) {
                            204, 404 -> "Skin ou jogador não encontrado (HTTP $status)"
                            429 -> "Serviço de skins limitou as consultas; tente mais tarde"
                            else -> "Falha ao obter skin/perfil (HTTP $status)"
                        } }
                        require(connection.contentLengthLong <= limit) { "Resposta de skin/perfil excede o limite" }
                        val data = connection.inputStream.use { it.readNBytes(limit + 1) }
                        require(data.size <= limit) { "Resposta de skin/perfil excede o limite" }
                        return data
                    }
                } finally { connection.disconnect() }
            }
            error("Redirecionamentos demais na URL")
        }
    }
}
