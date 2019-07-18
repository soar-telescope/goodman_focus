Getting Data
############

The goodman focus value ranges from :math:`-2000` to :math:`+2000` the best
practice (from experience) is to sample every :math:`200`. If you want to refine
you should not go below a :math:`100` step. If you already know the approximate
focus value for a given setup, you don't need to do the full range, just take
enough samples so it is possible to make a fit or see the trends.
At least five points.


.. note::

   Always use the narrowest slit available


Imaging
*******

For imaging, an image of the slit is obtained, illuminated by an
uniform light such as a quartz lamp. A special ROI is used for faster reading.
This does not affect the focus of course.

.. plot::

   import matplotlib.pyplot as plt
   from ccdproc import CCDData

   ccd = CCDData.read('_static/im_g_SDSS.fits', unit='adu')

   fig, ax = plt.subplots(figsize=(8, 2))

   ax.set_title("Imaging  - g-SDSS\nDome Lamp 40%")

   ax.imshow(ccd.data, cmap='gray', clim=(484, 513))

Spectroscopy
************

In spectroscopy a comparison lamp is observed and after every line is measured
and fitted, an average is obtained with sigma clip rejection.

.. plot::

   import matplotlib.pyplot as plt
   from ccdproc import CCDData

   ccd = CCDData.read('_static/sp_400m1.fits', unit='adu')

   fig, ax = plt.subplots(figsize=(8, 2))

   ax.set_title("Spectroscopy - 400m1\nHgArNe")

   ax.imshow(ccd.data, cmap='gray', clim=(490, 836))



.. plot::

   import matplotlib.pyplot as plt
   from ccdproc import CCDData

   ccd = CCDData.read('_static/sp_400m2.fits', unit='adu')

   fig, ax = plt.subplots(figsize=(8, 2))

   ax.set_title("Spectroscopy - 400m2\nHgArNe")

   ax.imshow(ccd.data, cmap='gray', clim=(487, 1157))