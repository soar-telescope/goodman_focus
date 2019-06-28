


# Goodman Focus Finder

[![Build Status](https://travis-ci.org/soar-telescope/goodman_focus.svg?branch=master)](https://travis-ci.org/soar-telescope/goodman_focus)
[![Coverage Status](https://coveralls.io/repos/github/soar-telescope/goodman_focus/badge.svg?branch=master)](https://coveralls.io/github/soar-telescope/goodman_focus?branch=master)
[![Documentation Status](https://readthedocs.org/projects/goodman-focus/badge/?version=latest)](https://goodman-focus.readthedocs.io/en/latest/?badge=latest)
[![pypi](https://img.shields.io/pypi/v/goodman_focus.svg?style=flat)](https://pypi.org/project/goodman-focus/)

Finds the best focus for one or more focus sequences.

## How to Install

This tool requires python `3.6` at least to work. It will not install with `3.5`.

We recommend using [astroconda](https://astroconda.readthedocs.io/en/latest/) since it is easier.

### Using PYPI

Create a virtual environment using `conda` and specify python version `3.6`.
```bash
conda create -n goodman_focus python=3.6
```

Install using `pip`
```bash
pip install goodman-focus
```

### Using github

Clone the latest version using:

```bash
git clone https://github.com/soar-telescope/goodman_focus.git
```

Move into the new directory
```bash
cd goodman_focus
```

Create a virtual environment using the `environment.yml` file and activate it.
```bash
conda env create python=3.6 -f environment.yml

conda activate goodman_focus

```

Install using `pip`
```bash
pip install .
```
## How to use it

### From terminal

There is an automatic script that will obtain focus from a folder containing
a focus sequence.

If you have `fits` files you can simply run.

```bash
goodman-focus
```

It will run with the following defaults:

```text
--data-path: (Current Working Directory)
--file-pattern: *fits
--obstype: FOCUS
--features-model: gaussian
--debug: (not activated)

```

To get some help and a full list of options use:

```bash
goodman-focus -h
```

### In other code

After installing using pip you can also import the class and instatiate it
providing a list of arguments and values.

```python
from goodman_focus.goodman_focus import GoodmanFocus
```

If no argument is provided it will run with the default values.

The list of arguments can be defined as follow:

```python
arguments = ['--data-path', '/provide/some/path',
             '--file-pattern', '*.fits',
             '--obstype', 'FOCUS',
             '--features-model', 'gaussian',
             '--debug']
```


``--features-model`` is the function/model to fit to each detected line. 
``gaussian`` will use a ```Gaussian1D``` which provide more consistent results.
and ``moffat`` will use a ```Moffat1D``` model which fits the profile better but 
is harder to control and results are less consistent than when using a gaussian.

# Found a problem?

Please [Open an Issue](https://github.com/soar-telescope/goodman_focus/issues) on
GitHub.