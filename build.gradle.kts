plugins {
    kotlin("jvm") version "2.2.20" apply false
    id("fabric-loom") version "1.11.8" apply false
}
allprojects {
    group = "dev.shirokai"
    version = "0.3.1"
    repositories { mavenCentral() }
}
