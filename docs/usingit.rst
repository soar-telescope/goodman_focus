Running from terminal
#####################

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


Using it as a library
#####################

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


However since version :ref:`v0.3.0` you can pass a list of files and all will only check that all files exists


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


It is also possible to obtain a plot, from terminal, use ``--plot-results``.
Below is a repreduction of results obtained  with test data.

.. plot::

  from astropy.modeling import models
  import numpy
  import matplotlib.pyplot as plt

  best_focus = -571.483741871
  mode_name = 'IM_Red_g-SDSS'

  data = {'file': ['0186_focus_gp.fits',
                   '0187_focus_gp.fits',
                   '0188_focus_gp.fits',
                   '0189_focus_gp.fits',
                   '0190_focus_gp.fits',
                   '0191_focus_gp.fits',
                   '0192_focus_gp.fits',
                   '0193_focus_gp.fits',
                   '0194_focus_gp.fits',
                   '0195_focus_gp.fits'],
          'fwhm': [5.291526,
                   4.712950,
                   4.112902,
                   3.449884,
                   2.930342,
                   2.665300,
                   2.579470,
                   2.611492,
                   2.815271,
                   3.246117],
          'focus': [-1496,
                    -1344,
                    -1197,
                    -1045,
                    -896,
                    -745,
                    -598,
                    -447,
                    -299,
                    -148]
          }

  polynomial = models.Polynomial1D(degree=5)
  polynomial.c0.value = 3.93919764664
  polynomial.c1.value = 0.00602356641338
  polynomial.c2.value = 1.04158253e-05
  polynomial.c3.value = 1.16769514e-08
  polynomial.c4.value = 9.45592111846e-12
  polynomial.c5.value = 2.8321431518e-15

  fig, ax = plt.subplots(figsize=(10,7))

  ax.plot(data['focus'], data['fwhm'], marker='x', label='Measured FWHM')
  ax.axvline(best_focus, color='k', label='Best Focus')
  ax.set_title("Best Focus:\n{} {:.3f}".format(mode_name, best_focus))
  ax.set_xlabel("Focus Value")
  ax.set_ylabel("FWHM or Mean FWHM")

  poly_x_axis = numpy.linspace(data['focus'][0], data['focus'][-1], 1000)

  ax.plot(poly_x_axis, polynomial(poly_x_axis), label='Model')

  ax.legend(loc='best')


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