import argparse
import glob
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

    parser.add_argument('--data-path',
                        action='store',
                        dest='data_path',
                        default=os.getcwd(),
                        help='Folder where data is located')

    parser.add_argument('--file-pattern',
                        action='store',
                        dest='file_pattern',
                        default='*.fits',
                        help='Pattern for filtering files.')

    parser.add_argument('--obstype',
                        action='store',
                        dest='obstype',
                        default='FOCUS',
                        help='Only the files whose OBSTYPE matches what you '
                             'enter here will be used. The default should '
                             'always work.')

    parser.add_argument('--features-model',
                        action='store',
                        dest='features_model',
                        choices=['gaussian', 'moffat'],
                        default='gaussian',
                        help='Model to use in fitting the features in order to'
                             'obtain the FWHM for each of them')

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        help='Activate debug mode')

    args = parser.parse_args(args=arguments)

    if not os.path.isdir(args.data_path):
        parser.error("Data location {} does not exist".format(args.data_path))
    elif len(glob.glob(os.path.join(args.data_path, args.file_pattern))) == 0:
        parser.error("There are no files matching \"{}\" in the folder \"{}\"".format(args.file_pattern, args.data_path))

    return args


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

    def __init__(self, arguments=None):
        self.args = get_args(arguments=arguments)
        self.log = logging.getLogger(__name__)
        if self.args.debug:
            self.log.setLevel(level=logging.DEBUG)

        if self.args.features_model == 'gaussian':
            self.feature_model = models.Gaussian1D()
        elif self.args.features_model == 'moffat':
            self.feature_model = models.Moffat1D()

        self.__ccd = None
        self.file_name = None
        self.__best_focus = None
        self.__x_axis = None
        self.__mean_fwhm = None

        self.polynomial = models.Polynomial1D(degree=5)
        self.fitter = fitting.LevMarLSQFitter()
        self.linear_fitter = fitting.LinearLSQFitter()

        if os.path.isdir(self.args.data_path):
            self.full_path = self.args.data_path
        else:
            sys.exit("No such directory")

        _ifc = ImageFileCollection(self.full_path, keywords=self.keywords)

        self.ifc = _ifc.summary.to_pandas()
        self.ifc = self.ifc[(self.ifc['OBSTYPE'] == self.args.obstype)]
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
        # print(configs.to_string())
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

    @property
    def fwhm(self):
        if self.__mean_fwhm is None:
            return self.feature_model.fwhm
        else:
            return self.__mean_fwhm

    # @property
    # def focus(self):
    #     return self.__best_focus
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
        # print(self.polynomial)
        return self.polynomial

    def _get_local_minimum(self, x1, x2):
        x_axis = np.linspace(x1, x2, 2000)
        modeled_data = self.polynomial(x_axis)
        derivative = []
        for i in range(len(modeled_data) - 1):
            derivative.append(modeled_data[i+1] - modeled_data[i]/(x_axis[i+1]-x_axis[i]))

        self.__best_focus = x_axis[np.argmin(np.abs(derivative))]

        return self.__best_focus

    def find_best_focus(self, group, plots=False):

        focus_data = []
        for self.file_name in group.file.tolist():
            self.log.debug("Processing file: {}".format(self.file_name))
            self.__ccd = CCDData.read(os.path.join(self.full_path, self.file_name), unit='adu')

            self._get_peaks()
            self._get_fwhm()

            self.log.info("File: {} Focus: {} FWHM: {}"
                          "".format(self.file_name,
                                    self.__ccd.header['CAM_FOC'],
                                    self.fwhm))
            if self.fwhm:
                focus_data.append([self.file_name, self.fwhm, self.__ccd.header['CAM_FOC']])
            else:
                self.log.warning("File: {} FWHM is: {} FOCUS: {}"
                                 "".format(self.file_name,
                                           self.fwhm,
                                           self.__ccd.header['CAM_FOC']))

        fdf = pandas.DataFrame(focus_data, columns=['file', 'fwhm', 'focus'])
        sorted = fdf.sort_values(by='focus')
        averaged = sorted.copy()
        averaged.pop('file')
        average = averaged

        # print(average)
        self._fit(df=average)
        self.log.info("Best Focus for {} is {}".format(self.file_name, self.__best_focus))
        if plots:
            # TODO (simon): Do properly using matplotlib or pandas alone
            # fig = plt.subplots()
            average.plot(x='focus', y='fwhm', marker='x')
            plt.axvline(self.__best_focus)
            plt.title("Best Focus: {}".format(self.__best_focus))
            focus_list = average['focus'].tolist()
            new_x_axis = np.linspace(focus_list[0], focus_list[-1], 1000)
            plt.plot(new_x_axis,
                     self.polynomial(new_x_axis), label='Model')
            plt.show()

    def _get_peaks(self):
        width, length = self.__ccd.data.shape

        low_limit = int(width / 2 - 50)
        high_limit = int(width / 2 + 50)

        raw_profile = np.median(self.__ccd.data[low_limit:high_limit, :], axis=0)
        self.__x_axis = np.array(range(len(raw_profile)))

        clipped_profile = sigma_clip(raw_profile, sigma=1, iters=5)

        _mean = np.mean(clipped_profile)

        clipped_x_axis = [i for i in range(len(clipped_profile)) if not clipped_profile.mask[i]]
        cleaned_profile = clipped_profile[~clipped_profile.mask]

        background_model = models.Linear1D(slope=0,
                                           intercept=np.mean(clipped_profile))

        fitted_background = self.linear_fitter(background_model,
                                               clipped_x_axis,
                                               cleaned_profile)

        self.__profile = raw_profile - np.array(fitted_background(self.__x_axis))

        filtered_data = np.where(
            np.abs(self.__profile > self.__profile.min() + 0.03 * self.__profile.max()), self.__profile,
            None)
        filtered_data = np.array(
            [0 if it is None else it for it in filtered_data])

        self.peaks = signal.argrelmax(filtered_data, axis=0, order=5)[0]


        if len(self.peaks) == 1:
            self.log.debug("Found {} peak in file".format(len(self.peaks)))
        else:
            self.log.debug("Found {} peaks in file".format(len(self.peaks)))

        self.values = [self.__profile[int(index)] for index in self.peaks]

        if False:
            plt.title("{} {}".format(self.file_name, np.mean(clipped_profile)))
            plt.axhline(0, color='k')
            plt.plot(self.__x_axis, raw_profile, label='Raw Profile')
            plt.plot(self.__x_axis, clipped_profile)
            plt.plot(self.__x_axis, background_model(self.__x_axis),
                     label='Background Level')
            plt.plot(self.__x_axis, fitted_background(self.__x_axis), label='Background Level')
            # plt.plot(self.__x_axis, self.__profile, label='Background Subtracted Profile')
            # plt.plot(self.__x_axis, filtered_data, label="Filtered Data")
            # for _peak in self.peaks:
            #     plt.axvline(_peak, color='k', alpha=0.6)
            plt.legend(loc='best')
            plt.show()

    def _set_model(self, peak_index):
        if self.feature_model.__class__.name == 'Gaussian1D':
            self.feature_model.amplitude.value = self.values[peak_index]
            self.feature_model.mean.value = self.peaks[peak_index]
            # TODO (simon): stddev should be calculated based on binning and slit size
            self.feature_model.stddev.value = 5

            self.log.debug(
                "Fitting {} with amplitude={}, mean={}, stddev={}".format(
                    self.feature_model.__class__.name,
                    self.feature_model.amplitude.value,
                    self.feature_model.mean.value,
                    self.feature_model.stddev.value))

        elif self.feature_model.__class__.name == 'Moffat1D':
            self.feature_model.amplitude.value = self.values[peak_index]
            self.feature_model.x_0.value = self.peaks[peak_index]
            self.log.debug(
                "Fitting {} with amplitude={}, x_0={}".format(
                    self.feature_model.__class__.name,
                    self.feature_model.amplitude.value,
                    self.feature_model.x_0.value))

    def _get_fwhm(self):

        if len(self.peaks) == 1:
            self._set_model(peak_index=0)
            self.feature_model = self.fitter(self.feature_model,
                                             self.__x_axis,
                                             self.__profile)
            if False:
                plt.plot(self.__x_axis, self.feature_model(self.__x_axis), color='r')
                plt.plot(self.__x_axis, self.__profile, color='b')
                plt.title(self.feature_model.fwhm)
                plt.xlim(2050, 2090)
                plt.show()

            return self.feature_model.fwhm

        else:
            all_fwhm = []
            self.__mean_fwhm = None
            for i in range(len(self.peaks)):
                self._set_model(peak_index=i)

                self.feature_model = self.fitter(self.feature_model,
                                                 self.__x_axis,
                                                 self.__profile)
                if False:
                    plt.plot(self.__x_axis, self.feature_model(self.__x_axis),
                             color='r')
                    plt.plot(self.__x_axis, self.__profile, color='b')
                    plt.title("FWHM: {}".format(self.feature_model.fwhm))
                    plt.xlim(self.peaks[i]-30, self.peaks[i] + 30)
                    plt.axvline(self.peaks[i], color='k')
                    plt.show()
                if not np.isnan(self.feature_model.fwhm):
                    all_fwhm.append(self.feature_model.fwhm)

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
                self.__mean_fwhm = np.mean(cleaned_fwhm)
                self.log.debug("Mean FWHM value {}".format(self.__mean_fwhm))
                return
            else:
                self.log.error("Unable to obtain usable FWHM value")
                self.log.debug("Returning FWHM None")
                return None


if __name__ == '__main__':
    # full_path = '/user/simon/data/soar/work/focus2'
    get_focus = GetFocus()
    get_focus()

