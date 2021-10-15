import argparse
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas
import re
import sys

from astropy.io import fits
from astropy.stats import sigma_clip
from astropy.modeling import models, fitting, Model
from ccdproc import CCDData
from ccdproc import ImageFileCollection
from scipy import signal

import logging
import logging.config


log = logging.getLogger(__name__)


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

    parser.add_argument('--plot-results',
                        action='store_true',
                        dest='plot_results',
                        help='Show a plot when it finishes the focus '
                             'calculation')

    parser.add_argument('--debug',
                        action='store_true',
                        dest='debug',
                        help='Activate debug mode')

    args = parser.parse_args(args=arguments)

    return args


def get_peaks(ccd, file_name='', plots=False):
    """Identify peaks in an image

    For Imaging and Spectroscopy the images obtained for focusing have lines
    that in the first case is an image of the slit and for the second is the
    spectrum of lamp, strategically selected for a good coverage of lines across
    the detector.

    Args:
        ccd (object): Image to get peaks from
        file_name (str): Name of the file used. This is optional and is used
        only for debugging purposes.
        plots (bool): Show plots of the profile, background and
        background-subtracted profile

    Returns:
        A list of peak values, peak intensities as well as the x-axis and the
        background subtracted spectral profile. For Imaging is the same axis as
        the spectral axis.

    """
    width, length = ccd.data.shape

    low_limit = int(width / 2 - 50)
    high_limit = int(width / 2 + 50)

    raw_profile = np.median(ccd.data[low_limit:high_limit, :], axis=0)
    x_axis = np.array(range(len(raw_profile)))

    clipped_profile = sigma_clip(raw_profile, sigma=1, maxiters=5)

    _mean = np.mean(clipped_profile)

    clipped_x_axis = [i for i in range(len(clipped_profile)) if not clipped_profile.mask[i]]
    cleaned_profile = clipped_profile[~clipped_profile.mask]

    background_model = models.Linear1D(slope=0,
                                       intercept=np.mean(clipped_profile))

    fitter = fitting.LinearLSQFitter()

    fitted_background = fitter(background_model,
                               clipped_x_axis,
                               cleaned_profile)

    profile = raw_profile - np.array(fitted_background(x_axis))

    filtered_data = np.where(
        np.abs(profile > profile.min() + 0.03 * profile.max()), profile,
        None)
    filtered_data = np.array(
        [0 if it is None else it for it in filtered_data])

    peaks = signal.argrelmax(filtered_data, axis=0, order=5)[0]


    if len(peaks) == 1:
        log.debug(f"Found {len(peaks)} peak in file")
    else:
        log.debug(f"Found {len(peaks)} peaks in file")

    values = np.array([profile[int(index)] for index in peaks])

    if plots:   # pragma: no cover
        plt.title(f"{file_name} {np.mean(clipped_profile)}")
        plt.axhline(0, color='k')
        plt.plot(x_axis, raw_profile, label='Raw Profile')
        plt.plot(x_axis, clipped_profile)
        plt.plot(x_axis, background_model(x_axis),
                 label='Background Level')
        plt.plot(x_axis, fitted_background(x_axis), label='Background Level')
        # plt.plot(x_axis, profile, label='Background Subtracted Profile')
        # plt.plot(x_axis, filtered_data, label="Filtered Data")
        # for _peak in peaks:
        #     plt.axvline(_peak, color='k', alpha=0.6)
        plt.legend(loc='best')
        plt.show()

    return peaks, values, x_axis, profile


def get_fwhm(peaks, values, x_axis, profile, model, sigma=3, maxiter=3):
    """Finds FWHM for an image by fitting a model

    For Imaging there is only one peak (the slit itself) but for spectroscopy
    there are many. In that case a 3-sigma clipping 1-iteration is applied to
    clean the values and then the mean is returned. In case that a FWHM can't be
    obtained a `None` value is returned.

    This function allows the use of `Gaussian1D` and `Moffat1D` models to be
    fitted to each line. `Gaussian1D` produces more consistent results though
    `Moffat1D` usually fits better the whole line profile.

    Args:
        peaks (numpy.ndarray): An array of peaks present in the profile.
        values (numpy.ndarray): An array of values at peak location.
        x_axis (numpy.ndarray): X-axis for the profile, usually is equivalent to
         `range(len(profile))`.
        profile (numpy.ndarray): 1-dimensional profile of the image being analyzed.
        model (Model): A model to fit to each peak location. `Gaussian1D` and
         `Moffat1D` are supported.
        sigma (int): Number sigmas to use on sigma-clipping
        maxiter (int): Maximum number of sigma-clipping iterations

    Returns:
        The FWHM, mean FWHM or `None`.

    """
    fitter = fitting.LevMarLSQFitter()
    all_fwhm = []
    for peak_index in range(len(peaks)):
        if model.__class__.name == 'Gaussian1D':
            model.amplitude.value = values[peak_index]
            model.mean.value = peaks[peak_index]
            # TODO (simon): stddev should be estimated based on binning and slit size
            model.stddev.value = 5
            log.debug(f"Fitting {model.__class__.name} with amplitude={model.amplitude.value}, "
                      f"mean={model.mean.value}, stddev={model.stddev.value}")

        elif model.__class__.name == 'Moffat1D':
            model.amplitude.value = values[peak_index]
            model.x_0.value = peaks[peak_index]
            log.debug(
                f"Fitting {model.__class__.name} with amplitude={model.amplitude.value}, x_0={model.x_0.value}")

        model = fitter(model,
                       x_axis,
                       profile)

        if not np.isnan(model.fwhm):
            all_fwhm.append(model.fwhm)

    if len(all_fwhm) == 1:
        log.info(f"Returning single FWHM value: {all_fwhm[0]}")
        return all_fwhm[0]
    else:
        log.info(f"Applying sigma clipping to collected FWHM values."
                 f" SIGMA: {sigma}, ITERATIONS: {maxiter}")
        clipped_fwhm = sigma_clip(all_fwhm, sigma=sigma, maxiters=maxiter)

        if np.ma.is_masked(clipped_fwhm):
            cleaned_fwhm = clipped_fwhm[~clipped_fwhm.mask]
            removed_fwhm = clipped_fwhm[clipped_fwhm.mask]
            log.info(f"Discarded {len(removed_fwhm)} FWHM values")
            for _value in removed_fwhm.data:
                log.debug(f"FWHM {_value} discarded")
        else:
            log.debug("No FWHM value was discarded.")
            cleaned_fwhm = clipped_fwhm

        if len(cleaned_fwhm) > 0:
            log.debug(f"Remaining FWHM values: {len(cleaned_fwhm)}")
            for _value in cleaned_fwhm:
                log.debug(f"FWHM value: {_value}")
            mean_fwhm = np.mean(cleaned_fwhm)
            log.debug(f"Mean FWHM value {mean_fwhm}")
            return mean_fwhm
        else:
            log.error("Unable to obtain usable FWHM value")
            log.debug("Returning FWHM None")
            return None


class GoodmanFocus(object):

    keywords = ['DATE',
                'DATE-OBS',
                'INSTCONF',
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

    def __init__(self,
                 data_path=os.getcwd(),
                 file_pattern="*.fits",
                 obstype="FOCUS",
                 features_model='gaussian',
                 plot_results=False,
                 debug=False):

        self.data_path = data_path
        self.file_pattern = file_pattern
        self.obstype = obstype
        self.features_model = features_model
        self.plot_results = plot_results
        self.debug = debug

        self.log = logging.getLogger(__name__)
        if self.debug:
            self.log.setLevel(level=logging.DEBUG)

        if self.features_model == 'gaussian':
            self.feature_model = models.Gaussian1D()
        elif self.features_model == 'moffat':
            self.feature_model = models.Moffat1D()

        self.__ccd = None
        self.file_name = None
        self.__best_focus = None
        self.__best_fwhm = None
        self.__best_image = None
        self.__best_image_focus = None
        self.__best_image_fwhm = None
        self._fwhm = None

        self.polynomial = models.Polynomial1D(degree=5)
        self.fitter = fitting.LevMarLSQFitter()
        self.linear_fitter = fitting.LinearLSQFitter()

        if os.path.isdir(self.data_path):
            self.full_path = self.data_path
        else:
            self.log.critical("No such directory")
            sys.exit(0)

    def __call__(self, files=None):
        if files is None:
            if not os.listdir(self.full_path):
                self.log.critical("Directory is empty")
                sys.exit(0)

            elif not glob.glob(os.path.join(self.full_path, self.file_pattern)):
                self.log.critical(f"Directory {self.full_path} does not containe files matching the pattern {self.file_pattern}")
                sys.exit(0)

            _ifc = ImageFileCollection(location=self.full_path,
                                       keywords=self.keywords,
                                       glob_include=self.file_pattern)

            self.ifc = _ifc.summary.to_pandas()
            self.log.debug(f"Found {self.ifc.shape[0]} FITS files")
            self.ifc = self.ifc[(self.ifc['OBSTYPE'] == self.obstype)]
            if self.ifc.shape[0] != 0:
                self.log.debug(f"Found { self.ifc.shape[0]} FITS files with OBSTYPE = FOCUS")

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
                    focus_group = self.ifc[
                        ((self.ifc['CAM_TARG'] == configs.iloc[i]['CAM_TARG']) &
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
            else:
                self.log.critical('Focus files must have OBSTYPE keyword equal to '
                                  '"FOCUS", none found.')
                self.log.info('Please use "--obstype" to change the value though '
                              'it is not recommended to use neither "OBJECT" nor '
                              '"FLAT" because it may contaminate the sample with '
                              'non focus images.')
                sys.exit(0)
        else:
            if isinstance(files, list):
                full_path_content = os.listdir(self.full_path)

                if not all([_file in full_path_content for _file in files]):
                    files_dont_exist = [_file for _file in files if _file not in full_path_content]
                    for _file in files_dont_exist:
                        self.log.critical(f"File {_file} does not exist in {self.full_path}")
                    sys.exit(0)
                else:
                    data = {'file': files}

                    for key in ['DATE', 'DATE-OBS', 'INSTCONF', 'FILTER', 'FILTER2', 'WAVMODE']:
                        key_data = [fits.getval(os.path.join(self.full_path,
                                                             _file), key) for _file in files]

                        data[key] = key_data

                    self.focus_groups = [pandas.DataFrame(data)]

            else:
                self.log.critical('"files" argument must be a list')
                sys.exit(0)


        results = []
        for focus_group in self.focus_groups:
            mode_name = self._get_mode_name(focus_group)

            focus_dataframe = self.get_focus_data(group=focus_group)

            self._fit(df=focus_dataframe)
            self.log.info(f"Best Focus for mode {mode_name} is {self.__best_focus}")
            results.append({'date': focus_group['DATE'].tolist()[0],
                            'time': focus_group['DATE-OBS'].tolist()[0],
                            'mode_name': mode_name,
                            'focus': self.__best_focus,
                            'fwhm': self.__best_fwhm,
                            'best_image_name': self.__best_image,
                            'best_image_focus': self.__best_image_focus,
                            'best_image_fwhm': self.__best_image_fwhm,
                            'focus_data': focus_dataframe['focus'].tolist(),
                            'fwhm_data':  focus_dataframe['fwhm'].tolist()
                            })

            if self.plot_results:   # pragma: no cover

                fig, ax = plt.subplots()

                focus_list = focus_dataframe['focus'].tolist()
                fwhm_list = focus_dataframe['fwhm'].tolist()
                new_x_axis = np.linspace(focus_list[0], focus_list[-1], 1000)

                ax.plot(focus_list, fwhm_list, marker='x', label='Measured FWHM')
                ax.axvline(self.__best_focus, color='k', label='Best Focus')
                ax.set_title(f"Best Focus:\n{mode_name} {self.__best_focus:.3f}")
                ax.set_xlabel("Focus Value")
                if 'IM_' in mode_name:
                    ax.set_ylabel("FWHM")
                else:
                    ax.set_ylabel("Mean FWHM")
                ax.plot(new_x_axis,
                        self.polynomial(new_x_axis), label='Model')
                ax.legend(loc='best')
                plt.show()

        return results

    @property
    def fwhm(self):
        return self._fwhm

    @fwhm.setter
    def fwhm(self, value):
        if value is not None:
            self._fwhm = value

    def _fit(self, df):
        """

        Args:
            df:

        Returns:

        """
        focus = df['focus'].tolist()
        fwhm = df['fwhm'].tolist()
        files = df['file'].tolist()
        max_focus = np.max(focus)
        min_focus = np.min(focus)
        self.polynomial = self.fitter(self.polynomial, focus, fwhm)
        self._get_local_minimum(x1=min_focus, x2=max_focus)

        index = np.argmin(np.abs(focus - self.__best_focus))

        self.__best_image = files[index]
        self.__best_image_focus = focus[index]
        self.__best_image_fwhm = fwhm[index]

        return self.polynomial

    def _get_local_minimum(self, x1, x2):
        """Finds best focus

        By calculating a pseudo-derivative of the fitted model to the focus
        values. The best focus is when the FWHM is minumum.

        Args:
            x1 (float): Minimum measured focus value.
            x2 (float): Maximum measured focus value.

        Returns:
            best_focus (float): Minimum of absolute value of pseudo-derivative
            values (i.e. closest to zero).

        """
        x_axis = np.linspace(x1, x2, 2000)
        modeled_data = self.polynomial(x_axis)
        derivative = []
        for i in range(len(modeled_data) - 1):
            derivative.append((modeled_data[i+1] - modeled_data[i])/(x_axis[i+1]-x_axis[i]))

        index_of_minimum = np.argmin(np.abs(derivative))
        self.__best_focus = x_axis[index_of_minimum]
        self.__best_fwhm = modeled_data[index_of_minimum]

        return self.__best_focus

    @staticmethod
    def _get_mode_name(group):
        """Defines a string characteristic of the instrument configuration

        Depending on the observing technique used the name is defined according
        to the following rules.

        Imaging: `IM_{INSTCONF}_{FILTER}` where the values in between the curly
        braces are keywords from the headers.

        Spectroscopy: `SP_{INSTCONF}_{WAVMODE}_{FILTER2}`

        Args:
            group (pandas.DataFrame): A `~pandas.DataFrame` containing only
            images with `OBSTYPE=FOCUS` or images from a list provided by the
            user.

        Returns:
            mode_name (str): A single string unique to the observing mode.

        """
        unique_values = group.drop_duplicates(
            subset=['INSTCONF', 'FILTER', 'FILTER2', 'WAVMODE'], keep='first')

        if unique_values['WAVMODE'].values == ['IMAGING']:
            mode_name = '__'.join(['IM',
                                   str(unique_values['INSTCONF'].values[0]),
                                   str(unique_values['FILTER'].values[0])])
        else:
            mode_name = '__'.join(['SP',
                                   str(unique_values['INSTCONF'].values[0]),
                                   str(unique_values['WAVMODE'].values[0]),
                                   str(unique_values['FILTER2'].values[0])])
        mode_name = re.sub('[<> ]', '', mode_name)
        # mode_name = re.sub('[- ]', '_', mode_name)
        return mode_name

    def get_focus_data(self, group):
        """Collects all the relevant data for finding best focus

        It is important that the data is not very contaminated because there is
        no built-in cleaning process.


        Args:
            group (DataFrame): The `group` refers to a set of images obtained
            most likely in series and with the same configuration.

        Returns:
            a `pandas.DataFrame` with three columns. `file`, `fwhm` and `focus`.

        """
        focus_data = []
        for self.file_name in group.file.tolist():
            self.log.debug(f"Processing file: {self.file_name}")
            self.__ccd = CCDData.read(os.path.join(self.full_path,
                                                   self.file_name),
                                      unit='adu')

            peaks, values, x_axis,  profile = get_peaks(
                ccd=self.__ccd,
                file_name=self.file_name,
                plots=self.debug)

            self.fwhm = get_fwhm(peaks=peaks,
                                 values=values,
                                 x_axis=x_axis,
                                 profile=profile,
                                 model=self.feature_model)

            self.log.info(f"File: {self.file_name} Focus: {self.__ccd.header['CAM_FOC']} FWHM: {self.fwhm}")
            if self.fwhm:
                focus_data.append([self.file_name, self.fwhm, self.__ccd.header['CAM_FOC']])
            else:
                self.log.warning(f"File: {self.file_name} FWHM is: {self.fwhm} FOCUS: {self.__ccd.header['CAM_FOC']}")

        focus_data_frame = pandas.DataFrame(
            focus_data,
            columns=['file', 'fwhm', 'focus']).sort_values(by='focus')

        return focus_data_frame


def run_goodman_focus(args=None):   # pragma: no cover
    """Entrypoint

    Args:
        args (list): (optional) a list of arguments and respective values.

    """
    LOG_FORMAT = '[%(asctime)s][%(levelname)s]: %(message)s'
    LOG_LEVEL = logging.INFO

    DATE_FORMAT = '%H:%M:%S'

    logging.basicConfig(level=LOG_LEVEL,
                        format=LOG_FORMAT,
                        datefmt=DATE_FORMAT)

    log = logging.getLogger(__name__)

    args = get_args(arguments=args)
    goodman_focus = GoodmanFocus(data_path=args.data_path,
                                 file_pattern=args.file_pattern,
                                 obstype=args.obstype,
                                 features_model=args.features_model,
                                 plot_results=args.plot_results,
                                 debug=args.debug)

    result = goodman_focus()
    log.info("Summary")
    for key in result.keys():
        log.info(f"Mode: {key} Best Focus: {result[key]['focus']} at FWHM: {result[key]['fwhm']}. "
                 f"Best image: {result[key]['best_image']['file_name']} with focus: "
                 f"{result[key]['best_image']['focus']} and FWHM: {result[key]['best_image']['fwhm']}")


if __name__ == '__main__':   # pragma: no cover
    run_goodman_focus()
