import numpy as np
import logging

from astropy.io import fits
from astropy.modeling import models
from unittest import TestCase, skip
from ccdproc import CCDData

from ..goodman_focus import GoodmanFocus
from ..goodman_focus import get_peaks, get_fwhm

import matplotlib.pyplot as plt

logging.disable(logging.CRITICAL)

class GetPeaksTest(TestCase):

    def setUp(self):
        self.ccd = CCDData(data=np.ones((100, 1000)),
                           meta=fits.Header(),
                           unit='adu')

    def test_single_peak(self):
        peak_location = 500
        peak_value = 500
        gaussian = models.Gaussian1D(mean=peak_location,
                                     amplitude=peak_value,
                                     stddev=5)

        for i in range(100):
            self.ccd.data[i] = gaussian(range(1000))

        peaks, values, x_axis, profile = get_peaks(ccd=self.ccd)

        gaussian2 = models.Gaussian1D(mean=peaks[0],
                                      amplitude=values[0],
                                      stddev=3)
        fwhm = get_fwhm(peaks=peaks,
                        values=values,
                        x_axis=x_axis,
                        profile=profile,
                        model=gaussian2)

        self.assertEqual(len(peaks), 1)
        self.assertEqual(len(values), 1)
        self.assertEqual(peaks[0], peak_location)
        self.assertAlmostEqual(values[0], peak_value, delta=0.01)
        self.assertAlmostEqual(fwhm, gaussian.fwhm, delta=0.001)

    def test_multiple_peaks(self):
        number_of_peaks = 20
        set_fwhms = []

        # we use equally spaced peaks since we are only concerned with finding
        # a final fwhm value
        set_peaks = np.linspace(30, 970, num=number_of_peaks)
        # set_peaks = sorted(np.random.randint(30, 970, size=number_of_peaks))
        set_values = np.random.randint(200, 2000, size=number_of_peaks)
        signal_model = None

        for i in range(number_of_peaks):
            gaussian = models.Gaussian1D(mean=set_peaks[i], amplitude=set_values[i], stddev=5)
            set_fwhms.append(gaussian.fwhm)
            if signal_model is None:
                signal_model = gaussian
            else:
                signal_model += gaussian
        for e in range(100):
            self.ccd.data[e] = signal_model(range(1000))

        peaks, values, x_axis, profile = get_peaks(ccd=self.ccd)
        gaussian2 = models.Gaussian1D()
        mean_fwhm = get_fwhm(peaks=peaks,
                             values=values,
                             x_axis=x_axis,
                             profile=profile,
                             model=gaussian2)
        # we allow some peaks to be missed since we are not concerned about all
        # of them
        self.assertLessEqual(len(peaks), number_of_peaks)
        self.assertAlmostEqual(mean_fwhm, np.mean(set_fwhms), delta=0.01)
