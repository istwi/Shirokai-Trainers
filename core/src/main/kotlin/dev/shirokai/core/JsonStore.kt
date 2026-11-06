package dev.shirokai.core

import com.google.gson.GsonBuilder
import com.google.gson.JsonElement
import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.google.gson.JsonPrimitive
import com.google.gson.JsonNull
import com.google.gson.stream.JsonReader
import com.google.gson.stream.JsonToken
import java.nio.channels.FileChannel
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption.*
import java.nio.file.StandardOpenOption.*
import java.time.Instant
import java.util.UUID

/** Invalid files remain untouched; a previous valid backup can be read without overwriting them. */
class JsonStore(val root: Path, private val recovered: (Path, Exception) -> Unit = { _, _ -> }) {
    private val gson = GsonBuilder().setPrettyPrinting().create()
    init { Files.createDirectories(root) }

    @Synchronized fun <T> read(path: Path, type: Class<T>, validate: (T) -> Unit = {}): T? {
        if (!Files.exists(path)) return null
        fun load(p: Path): T {
            val text = Files.readString(p)
            val json = StrictJson.parse(text)
            require(json.isJsonObject) { "Objeto esperado em $p" }
            val value = gson.fromJson(json, type) ?: error("JSON vazio: $p")
            validate(value)
            return value
        }
        try { return load(path) } catch (original: Exception) {
            val backup = path.resolveSibling(path.fileName.toString() + ".bak")
            if (Files.exists(backup)) {
                try { val value = load(backup); recovered(path, original); return value } catch (fallback: Exception) { original.addSuppressed(fallback) }
            }
            throw IllegalStateException("JSON inválido preservado: $path", original)
        }
    }

    @Synchronized fun write(path: Path, value: Any) {
        Files.createDirectories(path.parent)
        val bytes = gson.toJson(value).toByteArray(Charsets.UTF_8)
        val temporary = Files.createTempFile(path.parent, ".shirokai-", ".tmp")
        try {
            FileChannel.open(temporary, WRITE, TRUNCATE_EXISTING).use { c ->
                val buffer = java.nio.ByteBuffer.wrap(bytes)
                while (buffer.hasRemaining()) c.write(buffer)
                c.force(true)
            }
            if (Files.exists(path)) {
                // Preserve every old version, including invalid files, rather than rotating it away.
                val archive = path.parent.resolve("backups")
                Files.createDirectories(archive)
                Files.copy(path, archive.resolve("${path.fileName}.${Instant.now().toEpochMilli()}.${UUID.randomUUID()}.json"))
                // Only a valid JSON object may replace the recovery backup.
                runCatching {
                    val previous = Files.readString(path)
                    require(StrictJson.parse(previous).isJsonObject)
                    when (value) {
                        is Trainer -> gson.fromJson(previous, Trainer::class.java).validate()
                        is PlayerProgress -> require(gson.fromJson(previous, PlayerProgress::class.java).let { it.uuid == value.uuid && it.schemaVersion == 1 })
                    }
                    Files.copy(path, path.resolveSibling(path.fileName.toString() + ".bak"), REPLACE_EXISTING)
                }
            }
            Files.move(temporary, path, ATOMIC_MOVE, REPLACE_EXISTING)
        } finally { Files.deleteIfExists(temporary) }
    }

    fun trainerPath(id: String): Path { require(validId(id)); return root.resolve("trainers/$id.json") }
    fun playerPath(id: UUID): Path = root.resolve("players/$id.json")
    fun saveTrainer(t: Trainer) { t.validate(); write(trainerPath(t.id), t) }
    fun savePlayer(p: PlayerProgress) = write(playerPath(p.uuid), p)
    fun copyPlayer(p: PlayerProgress): PlayerProgress = gson.fromJson(gson.toJson(p), PlayerProgress::class.java)
    fun loadPlayer(id: UUID): PlayerProgress = read(playerPath(id), PlayerProgress::class.java) {
        require(it.uuid == id && it.schemaVersion == 1)
    } ?: PlayerProgress(id)
    fun loadTrainers(validate: (Trainer) -> Unit = {}): Map<String, Trainer> {
        val directory = root.resolve("trainers")
        if (!Files.isDirectory(directory)) return emptyMap()
        return Files.list(directory).use { paths -> paths.filter { it.fileName.toString().endsWith(".json") }.toList() }
            .associate { path ->
                val t = read(path, Trainer::class.java) { it.validate(); validate(it); require(path.fileName.toString() == "${it.id}.json") }!!
                t.id to t
            }
    }
    fun resetPlayer(id: UUID) { savePlayer(PlayerProgress(id)) }
    fun sessionPath(id: UUID) = root.resolve("battles/$id.json")
    fun resolutionPath(id: UUID) = root.resolve("results/$id.json")
    fun loadSessions(): List<BattleSession> = loadDirectory(root.resolve("battles"), BattleSession::class.java)
    fun loadResolutions(): List<BattleResolution> = loadDirectory(root.resolve("results"), BattleResolution::class.java)
    private fun <T> loadDirectory(directory: Path, type: Class<T>): List<T> {
        if (!Files.isDirectory(directory)) return emptyList()
        return Files.list(directory).use { paths -> paths.filter { it.fileName.toString().endsWith(".json") }.toList() }
            .map { read(it, type)!! }
    }
}

/** Gson's default parser accepts comments; consume tokens ourselves with leniency disabled. */
object StrictJson {
    fun parse(text: String): JsonElement {
        require(text.length <= 4_000_000) { "JSON muito grande" }
        JsonReader(text.reader()).use { reader ->
            reader.isLenient = false
            fun value(depth: Int): JsonElement {
                require(depth < 64) { "JSON muito profundo" }
                return when (reader.peek()) {
                    JsonToken.BEGIN_OBJECT -> JsonObject().also { obj ->
                        reader.beginObject()
                        while (reader.hasNext()) {
                            val name = reader.nextName()
                            require(!obj.has(name)) { "Chave JSON duplicada: $name" }
                            obj.add(name, value(depth + 1))
                        }
                        reader.endObject()
                    }
                    JsonToken.BEGIN_ARRAY -> JsonArray().also { arr ->
                        reader.beginArray(); while (reader.hasNext()) arr.add(value(depth + 1)); reader.endArray()
                    }
                    JsonToken.STRING -> JsonPrimitive(reader.nextString())
                    JsonToken.NUMBER -> JsonPrimitive(reader.nextString().toBigDecimal())
                    JsonToken.BOOLEAN -> JsonPrimitive(reader.nextBoolean())
                    JsonToken.NULL -> { reader.nextNull(); JsonNull.INSTANCE }
                    else -> error("Token JSON inesperado")
                }
            }
            val result = value(0)
            require(reader.peek() == JsonToken.END_DOCUMENT) { "Conteúdo após JSON" }
            return result
        }
    }
}
