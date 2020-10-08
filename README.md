# Prerequisites

For the script to run, the following is required

## Python version 3.8

## Pipenv

This script use `pipenv` to manage the python virtual environment. Install `pipenv` with:

``` sh
pip install pipenv
```

Then install packages dependencies from the project root with:

``` sh
pipenv install
```

## Firefox and `geckodriver`

Download a recent version of Firefox. `geckodriver` binaries come within the /bin folder of this repositories.

# Run
From the project root:

``` sh
pipenv shell
python ./scrap-macro-data.py
```

then follow instructions (if any).
