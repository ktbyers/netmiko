This explains how to run Nokia SR Linux tests with containerlab

## Install containerlab and Docker
See [containerlab](https://containerlab.dev/install/)

## Deploy containerlab Node Running SR Linux
To deploy the containerlab node defined in containerlabTest.yml run:

```
sudo clab deploy --topo containerlabTest.yml
```

The containerlab node hostname is clab-srltest-srl1.

## Run the test

```
sudo sh test_srl.sh 
```

## Destroy containerlab Node
To destroy the containerlab node defined in containerlabTest.yml run:

```
sudo clab destroy --topo containerlabTest.yml
```
