# ODIN API

OdinAPI was rewritten 2023 to run in AWS
## Cloning the repo

    git clone git@github.com:Odin-SMR/odin-api.git

## Preparing the development environment

Install the system requirements in the `./requirement_ubuntu20.04.apt` file.
Create a virtual enviroment and install the python requirements in the file
 `./requirements-dev.txt`.

## Running tests locally

Run all tests:

    pytest

There are some markers defined in the test suite, to run test not marked as
slow or marked as system test

    pytest -m "not slow and not system"

## Tests in github actions

Github runs all test on a commit with tox.

    tox

## Running the webapi on your local system

Bring up a the system browse the Odin/SMR site and try out the api. This test system 
includes some level1 data (no level2 data).

    docker compose up -d
    ./start --local