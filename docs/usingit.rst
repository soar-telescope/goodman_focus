From terminal
#############

There is an automatic script that will obtain focus from a folder containing
a focus sequence.

If you have `fits` files you can simply run.

  ``goodman-focus``

It will run with the following defaults:

.. table:: Default values for arguments

  ============================== ============================ ===================
        Argument                      Default Value               Options
  ============================== ============================ ===================
   ``--data-path <input>``        Current Working Directory    Any valid path
   ``--file-pattern <input>``     *.fits                       Any
   ``--features-model <input>``   gaussian                     moffat
   ``--plot-results``             False                        True
   ``--debug``                    False                        True
  ============================== ============================ ===================

Where ``<input>`` is what you type.


To get some help and a full list of options use:

  ``goodman-focus -h``


As a Library
############

After installing :ref:`Installing with PIP` you can also import the class and instantiate it
providing a set of arguments and values or using default ones.

  ``from goodman_focus.goodman_focus import GoodmanFocus``

If no argument is provided it will instantiate with the default values.

The list of arguments can be defined as follow:

.. code-block:: python

   import os
   from goodman_focus.goodman_focus import GoodmanFocus

   goodman_focus = GoodmanFocus(data_path=os.getcwd(),
                                file_pattern='*.fits',
                                obstype='FOCUS',
                                features_model='gaussian',
                                plot_results=False,
                                debug=False)


Which is equivalent to:

.. code-block:: python

  from goodman_focus.goodman_focus import GoodmanFocus

  goodman_focus = GoodmanFocus()



``features_model`` is the function or model to fit to each detected line.
``gaussian`` will use a ``Gaussian1D`` which provide more consistent results.
and ``moffat`` will use a ``Moffat1D`` model which fits the profile better but
is harder to control and results are less consistent than when using a gaussian.


Finally you need to call the instance, here is a full example.

.. code-block:: python

  from goodman_focus.goodman_focus import GoodmanFocus

  goodman_focus = GoodmanFocus()

  results = goodman_focus()


Interpreting Results
####################

The terminal version will print a message like this

  ``[17:16:06][INFO]: Best Focus for mode SP_Red_400m2_GG455 is -1032.6413206603302``


Using it as a library will return a dictionary with the following values.
Combination of settings for which the code is the same is called a `mode`, so
the keys of the dictionary are the `mode name`, how the name is constructed is
explained in :ref:`decoding-mode-name`

.. code-block:: python

  {'IM_Red_g-SDSS': -571.4837418709354,
   'IM_Red_i-SDSS': -802.567783891946,
   'IM_Red_r-SDSS': -573.8694347173587,
   'IM_Red_z-SDSS': -1161.5072536268135,
   'SP_Red_400m1_NOFILTER': -492.0760380190095,
   'SP_Red_400m2_GG455': -1032.6413206603302}

.. _decoding-mode-name:
Decoding de mode name
*********************

The mode name is constructed using two letters to define the observing technique
(Imaging or Spectroscopy) and values obtained from the header. The characters
``<``, ``>`` and `blanks` are removed.

The mode name is different for Imaging and Spectroscopy, since for imaging
the important settings are the instrument and the filter and for spectroscopy
the important values come from the instrument, the grating and observing mode and
filter from second filter wheel. Below, the word inside the parenthesis represents
a kewyword from the header.

For imaging:

  ``IM_(INSTCONF)_(FILTER)``

for example:

  ``IM_Red_g-SDSS``

For spectroscopy:

  ``SP_(INSTCONF)_(WAVMODE)_(FILTER2)``


for example:

  ``SP_Red_400m2_GG455``