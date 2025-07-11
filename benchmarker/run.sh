#!/bin/sh

java --add-opens=java.base/java.lang=ALL-UNNAMED -jar JFactBenchmarker/target/JFactBenchmarker-1.0-SNAPSHOT.jar "$@" |tee jfact.json
java -jar PelletBenchmarker/target/PelletBenchmarker-1.0-SNAPSHOT.jar "$@" |tee pellet.json
java -jar HermiTBenchmarker/target/HermiTBenchmarker-1.0-SNAPSHOT.jar "$@" |tee hermit.json