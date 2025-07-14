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

## Docker WebUI container
```shell
docker build -t alcgen-web -f Dockerfile.web .
```

# Use

## Docker CLI container

```shell
docker run --mount type=bind,source=$PWD/target,destination=/target --rm alcgen /target/default.json
```

## Docker WebUI container

```shell
docker run -p 8501:8501 --rm alcgen-web
```