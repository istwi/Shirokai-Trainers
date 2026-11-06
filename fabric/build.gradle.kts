plugins {
    id("fabric-loom")
    kotlin("jvm")
}
kotlin { jvmToolchain(21) }
base { archivesName.set("shirokai-trainers") }
repositories {
    maven("https://maven.fabricmc.net/")
    maven("https://artefacts.cobblemon.com/releases")
}
dependencies {
    minecraft("com.mojang:minecraft:1.21.1")
    mappings(loom.officialMojangMappings())
    modImplementation("net.fabricmc:fabric-loader:0.17.2")
    modImplementation("net.fabricmc.fabric-api:fabric-api:0.116.6+1.21.1")
    modImplementation("net.fabricmc:fabric-language-kotlin:1.13.6+kotlin.2.2.20")
    modImplementation("com.cobblemon:fabric:1.8.3+1.21.1")
    // Match Cobblemon's own dedicated-server development setup (fabric/build.gradle.kts).
    minecraftServerLibraries("com.ibm.icu:icu4j:71.1")
    implementation(project(":core"))
    include(project(":core"))
    modImplementation("me.lucko:fabric-permissions-api:0.3.1")
    include("me.lucko:fabric-permissions-api:0.3.1")
}
tasks.processResources {
    inputs.property("version", project.version)
    filesMatching("fabric.mod.json") { expand("version" to project.version) }
}
