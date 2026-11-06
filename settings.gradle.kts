pluginManagement {
    repositories {
        maven("https://maven.fabricmc.net/")
        gradlePluginPortal()
        mavenCentral()
    }
}
rootProject.name = "Shirokai-Trainers"
include("core")
if (!providers.gradleProperty("coreOnly").isPresent) include("fabric")
