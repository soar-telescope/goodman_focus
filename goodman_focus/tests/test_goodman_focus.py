import numpy as np

from astropy.io import fits
from astropy.modeling import models
from unittest import TestCase, skip
from ccdproc import CCDData

from ..goodman_focus import get_peaks

import matplotlib.pyplot as plt


class GetPeaksTest(TestCase):

    def setUp(self):
        self.ccd = CCDData(data=np.ones((100, 100)),
                           meta=fits.Header(),
                           unit='adu')

    def test_single_peak(self):
        peak_location = 50
        peak_value = 500
        gaussian = models.Gaussian1D(mean=peak_location,
                                     amplitude=peak_value,
                                     stddev=5)

        for i in range(100):
            self.ccd.data[i] = gaussian(range(100))

        peaks, x_axis, values = get_peaks(ccd=self.ccd)

        self.assertEqual(len(peaks), 1)
        self.assertEqual(len(values), 1)
        self.assertEqual(peaks[0], peak_location)
        self.assertAlmostEqual(values[0], peak_value, delta=0.01)
