#!/bin/sh

java --add-opens=java.base/java.lang=ALL-UNNAMED -jar JFactBenchmarker/target/JFactBenchmarker-1.0-SNAPSHOT.jar "$@" |tee jfact.jsonl
java -jar PelletBenchmarker/target/PelletBenchmarker-1.0-SNAPSHOT.jar "$@" |tee pellet.jsonl
java -jar HermiTBenchmarker/target/HermiTBenchmarker-1.0-SNAPSHOT.jar "$@" |tee hermit.jsonl
java -jar ELKBenchmarker/target/ELKBenchmarker-1.0-SNAPSHOT.jar "$@" |tee elk.jsonl