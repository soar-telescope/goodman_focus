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

  ``Mode: IM__Red__VR Best Focus: -682.2891445722862 at FWHM: 2.610853168299203``
  ``Best image: 0019_IM_FOCUS_VR-02-11-2019.fits with focus: -601 and FWHM: 2.618208314784383``


Using it as a library will return a dictionary with the following values.
Combination of settings for which the code is the same is called a `mode`, so
the keys of the dictionary are the `mode name`, how the name is constructed is
explained in :ref:`decoding-mode-name`

.. code-block:: python

  {
    "IM__Red__VR": {
        "focus": -682.2891445722862,
        "fwhm": 2.610853168299203,
        "best_image": {
            "file_name": "0019_IM_FOCUS_VR-02-11-2019.fits",
            "focus": -601,
            "fwhm": 2.618208314784383
        },
        "data": {
            "focus": [
                -1994,
                -1800,
                -1596,
                -1400,
                -1196,
                -1001,
                -801,
                -601,
                -400,
                -200,
                0
            ],
            "fwhm": [
                6.563725199766027,
                6.06385739315605,
                5.247499967673857,
                4.1285040906260795,
                3.4365641352223735,
                2.8936984023341568,
                2.668879483788302,
                2.618208314784383,
                2.775636169723414,
                3.17285749377152,
                3.801357666832794
            ]
        }
    },
    "IM__Red__g-SDSS": {
        "focus": -610.1660830415208,
        "fwhm": 1311.116741905355,
        "best_image": {
            "file_name": "0052_IM_FOCUS_g-SDSS-02-11-2019.fits",
            "focus": -598,
            "fwhm": 2.649933307696907
        },
        "data": {
            "focus": [
                -1994,
                -1797,
                -1596,
                -1400,
                -1200,
                -1001,
                -797,
                -598,
                -400,
                -200,
                -1
            ],
            "fwhm": [
                10078.568462134408,
                14587.248215453463,
                6.974615754441357,
                4.428741442419154,
                3.6944352732876298,
                3.092146915821145,
                2.7623838554169677,
                2.649933307696907,
                2.6830053487148295,
                3.0344538985884117,
                3.553276899775066
            ]
        }
    },
    "IM__Red__i-SDSS": {
        "focus": -872.8114057028515,
        "fwhm": 2.5457563308537052,
        "best_image": {
            "file_name": "0073_IM_FOCUS_i-SDSS-02-11-2019.fits",
            "focus": -800,
            "fwhm": 2.596132528556466
        },
        "data": {
            "focus": [
                -1994,
                -1800,
                -1596,
                -1401,
                -1199,
                -1002,
                -800,
                -598,
                -401,
                -201,
                0
            ],
            "fwhm": [
                5.560966902190007,
                5.065376071655364,
                4.2934521685265805,
                3.3798003916603085,
                2.9000458070451853,
                2.6576241265555054,
                2.596132528556466,
                2.7013565671983684,
                3.0816052837728094,
                3.7515817806764415,
                4.482803504246921
            ]
        }
    },
    "IM__Red__r-SDSS": {
        "focus": -700.8929464732366,
        "fwhm": 2.6124472728412464,
        "best_image": {
            "file_name": "0063_IM_FOCUS_r-SDSS-02-11-2019.fits",
            "focus": -601,
            "fwhm": 2.619190100387657
        },
        "data": {
            "focus": [
                -1994,
                -1800,
                -1600,
                -1400,
                -1201,
                -1000,
                -801,
                -601,
                -398,
                -201,
                -1
            ],
            "fwhm": [
                6.418236632070858,
                5.904228575760692,
                5.096126122303206,
                4.028043010850983,
                3.3633679109213865,
                2.8831227979791145,
                2.6663294197543594,
                2.619190100387657,
                2.7851502401449557,
                3.242542204364083,
                3.854389127313035
            ]
        }
    },
    "SP__Red__400_M1__NO_FILTER": {
        "focus": -486.02551275637825,
        "fwhm": 2.782866546867474,
        "best_image": {
            "file_name": "0009_SP_FOCUS_400_M1_NO_FILTER-02-11-2019.fits",
            "focus": -401,
            "fwhm": 2.8119415184081067
        },
        "data": {
            "focus": [
                -1995,
                -1800,
                -1600,
                -1401,
                -1201,
                -1001,
                -801,
                -598,
                -401,
                -200,
                0
            ],
            "fwhm": [
                8.391326305891555,
                7.730900155895203,
                6.806632962497317,
                5.4746963164198945,
                4.3902839723521785,
                3.6983380943571507,
                3.0500620739865028,
                2.816038012437021,
                2.8119415184081067,
                2.9933712434094644,
                3.419879429910512
            ]
        }
    },
    "SP__Red__400_M2__GG455": {
        "focus": -1044.8574287143572,
        "fwhm": 2.70924140386515,
        "best_image": {
            "file_name": "0028_SP_FOCUS_400_M2_GG455-02-11-2019.fits",
            "focus": -1001,
            "fwhm": 2.7868396931440125
        },
        "data": {
            "focus": [
                -1994,
                -1800,
                -1600,
                -1401,
                -1201,
                -1001,
                -800,
                -598,
                -401,
                -200,
                -1
            ],
            "fwhm": [
                4.879423755217414,
                4.490050876645501,
                3.7633687417096096,
                3.0940502796759786,
                2.83501045746222,
                2.7868396931440125,
                2.9319443117863937,
                3.3664741439041834,
                4.09694833758484,
                5.030560477812672,
                5.931045259840967
            ]
        }
    }
  }




It is also possible to obtain a plot, from terminal, use ``--plot-results``.
Below is a reproduction of results obtained  with test data.

.. plot::

  from astropy.modeling import models
  import numpy
  import matplotlib.pyplot as plt

  best_focus = -571.483741871
  mode_name = 'IM__Red__g-SDSS'

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
a keyword from the header.

.. warning::
  Be aware that the separator string is a ``double underscore``. This change
  was necessary to avoid confusion with single underscores used in certain
  keyword values.

For imaging:

  ``IM__(INSTCONF)__(FILTER)``

for example:

  ``IM__Red__g-SDSS``

For spectroscopy:

  ``SP__(INSTCONF)__(WAVMODE)__(FILTER2)``


for example:

  ``SP__Red__400m2__GG455``