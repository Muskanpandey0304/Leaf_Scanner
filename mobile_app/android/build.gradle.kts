allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
// Some plugins (e.g. onnxruntime) still compile against android-33 but depend on libraries needing 34+.
subprojects {
    afterEvaluate {
        if (project.hasProperty("android")) {
            project.extensions.findByName("android")?.withGroovyBuilder {
                "compileSdkVersion"(36)
            }
        }
    }
}
// Android lint crashes on some plugin sources with this JDK (a lint bug); it is optional for building the APK.
subprojects {
    tasks.configureEach {
        if (name.startsWith("lintVital") || name.startsWith("lintAnalyze") || name.startsWith("lintReport")) {
            enabled = false
        }
    }
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
