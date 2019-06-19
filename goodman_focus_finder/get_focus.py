import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas
import sys

from astropy.stats import sigma_clip
from astropy.modeling import models, fitting, Model
from ccdproc import CCDData
from ccdproc import ImageFileCollection
from scipy import signal

import logging
import logging.config

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s][%(levelname)s]: %(message)s',
            'datefmt': '%H:%M:%S',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
        'rotate_file': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'focus_finder.log',
            'encoding': 'utf8',
            'maxBytes': 100000,
            'backupCount': 1,
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'rotate_file'],
            'level': 'DEBUG',
        },
}
}

LOG_FORMAT = '[%(asctime)s][%(levelname)s]: %(message)s'
LOG_LEVEL = logging.INFO

DATE_FORMAT = '%H:%M:%S'

formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

logging.config.dictConfig(LOGGING)


def get_args(arguments=None):
    parser = argparse.ArgumentParser(
        description="Get best focus value using a sequence of images with "
                    "different focus value"
    )

    parser.add_argument()




class GetFocus(object):

    keywords = ['INSTCONF',
                'FOCUS',
                'CAM_TARG',
                'GRT_TARG',
                'CAM_FOC',
                'COLL_FOC',
                'FILTER',
                'FILTER2',
                'GRATING',
                'SLIT',
                'WAVMODE',
                'EXPTIME',
                'RDNOISE',
                'GAIN',
                'OBSTYPE',
                'ROI']

    def __init__(self, full_path):
        self.log = logging.getLogger(__name__)

        self.gaussian = models.Gaussian1D()
        self.moffat = models.Moffat1D()
        self.polynomial = models.Polynomial1D(degree=5)
        self.fitter = fitting.LevMarLSQFitter()
        self.linear_fitter = fitting.LinearLSQFitter()
        self.fitted_model = None

        self._best_focus = None

        if os.path.isdir(full_path):
            self.full_path = full_path
        else:
            sys.exit("No such directory")

        _ifc = ImageFileCollection(full_path, keywords=self.keywords)

        self.ifc = _ifc.summary.to_pandas()
        self.ifc = self.ifc[(self.ifc['OBSTYPE'] == 'FOCUS')]
        self.focus_groups = []
        configs = self.ifc.groupby(['CAM_TARG',
                                    'GRT_TARG',
                                    'FILTER',
                                    'FILTER2',
                                    'GRATING',
                                    'SLIT',
                                    'WAVMODE',
                                    'RDNOISE',
                                    'GAIN',
                                    'ROI']).size().reset_index().rename(
            columns={0: 'count'})
        print(configs.to_string())
        for i in configs.index:
            focus_group = self.ifc[((self.ifc['CAM_TARG'] == configs.iloc[i]['CAM_TARG']) &
                                    (self.ifc['GRT_TARG'] == configs.iloc[i]['GRT_TARG']) &
                                    (self.ifc['FILTER'] == configs.iloc[i]['FILTER']) &
                                    (self.ifc['FILTER2'] == configs.iloc[i]['FILTER2']) &
                                    (self.ifc['GRATING'] == configs.iloc[i]['GRATING']) &
                                    (self.ifc['SLIT'] == configs.iloc[i]['SLIT']) &
                                    (self.ifc['WAVMODE'] == configs.iloc[i]['WAVMODE']) &
                                    (self.ifc['RDNOISE'] == configs.iloc[i]['RDNOISE']) &
                                    (self.ifc['GAIN'] == configs.iloc[i]['GAIN']) &
                                    (self.ifc['ROI'] == configs.iloc[i]['ROI']))]
            self.focus_groups.append(focus_group)

    # @property
    # def focus(self):
    #     return self._best_focus
    #
    # @property.setter
    # def focus(self):
    #     pass


    def __call__(self, *args, **kwargs):
        for focus_group in self.focus_groups:
            # print(focus_group)
            self.find_best_focus(group=focus_group, plots=True)

        # print(self.ifc.to_string())


    def _fit(self, df):
        focus = df['focus'].tolist()
        fwhm = df['fwhm'].tolist()

        max_focus = np.max(focus)
        min_focus = np.min(focus)
        self.polynomial = self.fitter(self.polynomial, focus, fwhm)
        self._get_local_minimum(x1=min_focus, x2=max_focus)
        print(self.polynomial)
        return self.polynomial

    def _get_local_minimum(self, x1, x2):
        x_axis = np.linspace(x1, x2, 2000)
        modeled_data = self.polynomial(x_axis)
        derivative = []
        for i in range(len(modeled_data) - 1):
            derivative.append(modeled_data[i+1] - modeled_data[i]/(1))

        self._best_focus = x_axis[np.argmin(np.abs(derivative))]

        return self._best_focus

    def find_best_focus(self, group, plots=False):

        focus_data = []
        for _file in group.file.tolist():
            self.log.debug("Processing file: {}".format(_file))
            ccd = CCDData.read(os.path.join(self.full_path, _file), unit='adu')
            fwhm = self.get_fwhm(ccd=ccd)
            self.log.info("File: {} Focus: {} FWHM: {}"
                          "".format(_file,
                                    ccd.header['CAM_FOC'],
                                    fwhm))
            if fwhm:
                focus_data.append([_file, fwhm, ccd.header['CAM_FOC']])
            else:
                self.log.warning("File: {} FWHM is: {} FOCUS: {}"
                                 "".format(_file,
                                           fwhm,
                                           ccd.header['CAM_FOC']))

        fdf = pandas.DataFrame(focus_data, columns=['file', 'fwhm', 'focus'])
        sorted = fdf.sort_values(by='focus')
        averaged = sorted.copy()
        averaged.pop('file')
        average = averaged

        print(average)
        self._fit(df=average)
        if plots:
            # TODO (simon): Do properly using matplotlib or pandas alone
            # fig = plt.subplots()
            average.plot(x='focus', y='fwhm', marker='x')
            plt.axvline(self._best_focus)
            plt.title("Best Focus: {}".format(self._best_focus))
            focus_list = average['focus'].tolist()
            new_x_axis = np.linspace(focus_list[0], focus_list[-1], 1000)
            plt.plot(new_x_axis,
                     self.polynomial(new_x_axis), label='Model')
            plt.show()

    def get_fwhm(self, ccd, plots=False):

        width, length = ccd.data.shape

        low_limit = int(width/2 - 50)
        high_limit = int(width/2 + 50)

        raw_profile = np.median(ccd.data[low_limit:high_limit, :], axis=0)
        x_axis = range(len(raw_profile))

        clipped_profile = sigma_clip(raw_profile, sigma=2, iters=5)

        background_model = models.Linear1D(slope=0, intercept=np.mean(clipped_profile))

        fitted_background = self.linear_fitter(background_model, x_axis, clipped_profile)

        profile = raw_profile - np.array(fitted_background(x_axis))

        filtered_data = np.where(np.abs(profile > profile.min() + 0.03 * profile.max()), profile, None)
        filtered_data = np.array([0 if it is None else it for it in filtered_data])

        peaks = signal.argrelmax(filtered_data, axis=0, order=5)[0]

        if len(peaks) == 1:
            self.log.debug("Found {} peak in file".format(len(peaks)))
        else:
            self.log.debug("Found {} peaks in file".format(len(peaks)))

        values = [profile[int(index)] for index in peaks]

        all_fwhm = []

        for i in range(len(peaks)):
            self.gaussian.amplitude.value = values[i]
            self.gaussian.mean.value = peaks[i]
            self.gaussian.stddev.value = 5

            self.log.debug(
                "Fitting {} with amplitude={}, mean={}, stddev={}".format(
                    self.gaussian.__class__.name,
                    self.gaussian.amplitude.value,
                    self.gaussian.mean.value,
                    self.gaussian.stddev.value
                ))

            if len(peaks) == 1:
                self.fitted_model = self.fitter(self.gaussian,
                                                x_axis,
                                                profile)
                if plots:
                    plt.plot(x_axis, self.fitted_model(x_axis), color='r')
                    plt.plot(x_axis, profile, color='b')
                    plt.title(self.fitted_model.fwhm)
                    plt.xlim(2050, 2090)
                    plt.show()

                return self.fitted_model.fwhm
            else:
                self.fitted_model = self.fitter(self.gaussian,
                                                range(len(profile)),
                                                profile)
                if not np.isnan(self.fitted_model.fwhm):
                    all_fwhm.append(self.fitted_model.fwhm)

        self.log.info("Applying sigma clipping to collected FWHM values."
                      " SIGMA: 3, ITERATIONS: 1")
        clipped_fwhm = sigma_clip(all_fwhm, sigma=3, iters=1)

        if np.ma.is_masked(clipped_fwhm):
            cleaned_fwhm = clipped_fwhm[~clipped_fwhm.mask]
            removed_fwhm = clipped_fwhm[clipped_fwhm.mask]
            self.log.info("Discarded {} FWHM values".format(len(removed_fwhm)))
            for _value in removed_fwhm.data:
                self.log.debug("FWHM {} discarded".format(_value))
        else:
            self.log.debug("No FWHM value was discarded.")
            cleaned_fwhm = clipped_fwhm

        if len(cleaned_fwhm) > 0:
            self.log.debug("Remaining FWHM values: {}".format(len(cleaned_fwhm)))
            for _value in cleaned_fwhm:
                self.log.debug("FWHM value: {}".format(_value))
            self.log.debug("Mean FWHM value {}".format(np.mean(cleaned_fwhm)))
            return np.mean(cleaned_fwhm)
        else:
            self.log.error("Unable to obtain usable FWHM value")
            self.log.debug("Returning FWHM None")
            return None


if __name__ == '__main__':

    get_focus = GetFocus(full_path='/user/simon/data/soar/work/focus2')
    get_focus()

