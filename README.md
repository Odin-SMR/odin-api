# ODIN API

## Using git submodules

The `data/` directory comes from a different repository added as a submodule.

To clone the odin-api repository with the submodule, you can use:

    git clone --recursive https://phabricator.molflow.com/source/odin-api.git

If you already cloned the odin repository without the submodule, or if you
want to update the submodule:

    git submodule update --init --recursive

## Running tests locally

The file `requirements_ubuntu18.04.apt` includes the minimum set of libraries
you need to run the unittests locally. (docker and docker-compose is also
needed).

To run the unittest only:

    tox -- src/test
