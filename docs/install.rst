.. note::

   We recommend using a virtual environment management system such as
   `astroconda <https://astroconda.readthedocs.io/en/latest/>`_

.. _`Installing with PIP`:

Install Using PYPI
##################

Create a virtual environment using `conda` and specify python version `3.6`.

  ``conda create -n goodman_focus python=3.6``

Install using `pip`

  ``pip install goodman-focus``

Install Using GitHub
####################

Clone the latest version using:

  ``git clone https://github.com/soar-telescope/goodman_focus.git``


Move into the new directory

  ``cd goodman_focus``

Create a virtual environment using the `environment.yml` file and activate it.

  ``conda env create python=3.6 -f environment.yml``

This will create a virtual environment named ``goodman_focus`` with all the
important parts on it.

  ``conda activate goodman_focus``

Install using `pip`

  ``pip install .``
