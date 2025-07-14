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