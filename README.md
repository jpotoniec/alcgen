# Building

All the command blocks assume you are in the top level directory of the repository

## Benchmarker

```shell
mvn -f benchmarker package
```

## Generator

```shell
pip3 install -r requirements.txt
```

## Datasets
```shell
for i in datasets/*.json; do python3 -m alcgen $i;done
```

## Docker CLI container
```shell
docker build -t alcgen -f Dockerfile.cli .
```

# Use

## Docker CLI container

```shell
docker run --mount type=bind,source=$PWD/target,destination=/target --rm alcgen /target/default.json
```