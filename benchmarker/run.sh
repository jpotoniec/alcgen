#!/bin/bash

prefix=$1
shift

ulimit -t 600
ulimit -m $((32*1024*1024))
JAVAOPS=-Xmx16G

java $JAVAOPS --add-opens=java.base/java.lang=ALL-UNNAMED -jar JFactBenchmarker/target/JFactBenchmarker-1.0-SNAPSHOT.jar "$@" |tee "$prefix"jfact.jsonl
java $JAVAOPS -jar PelletBenchmarker/target/PelletBenchmarker-1.0-SNAPSHOT.jar "$@" |tee "$prefix"pellet.jsonl
java $JAVAOPS -jar HermiTBenchmarker/target/HermiTBenchmarker-1.0-SNAPSHOT.jar "$@" |tee "$prefix"hermit.jsonl
java $JAVAOPS -jar ELKBenchmarker/target/ELKBenchmarker-1.0-SNAPSHOT.jar "$@" |tee "$prefix"elk.jsonl