import datetime
import numpy as np
import logging
import pandas
import os

from astropy.io import fits
from astropy.modeling import models
from unittest import TestCase, skip
from ccdproc import CCDData

from ..goodman_focus import GoodmanFocus
from ..goodman_focus import get_args, get_peaks, get_fwhm

import matplotlib.pyplot as plt

logging.disable(logging.CRITICAL)


class ArgumentTests(TestCase):

    def setUp(self):
        self.arg_list = ['--data-path', os.getcwd(),
                         '--file-pattern', '*.myfile',
                         '--obstype', 'ANY',
                         '--features-model', 'moffat',
                         '--plot-results',
                         '--debug']

    def test_get_args_default(self):
        args = get_args(arguments=self.arg_list)
        self.assertEqual(args.__class__.__name__, 'Namespace')
        self.assertEqual(args.data_path, os.getcwd())
        self.assertEqual(args.file_pattern, '*.myfile')
        self.assertEqual(args.obstype, 'ANY')
        self.assertEqual(args.features_model, 'moffat')
        self.assertTrue(args.plot_results)
        self.assertTrue(args.debug)


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
        self.assertAlmostEqual(mean_fwhm, np.mean(set_fwhms), delta=0.1)


class GoodmanFocusTests(TestCase):

    def setUp(self):
        arguments = ['--data-path', os.getcwd(),
                     '--file-pattern', '*.fits',
                     '--obstype', 'FOCUS',
                     '--features-model', 'gaussian']

        number_of_test_subjects = 21
        self.file_list = ["file_{}.fits".format(i+1) for i in range(number_of_test_subjects)]
        self.focus_values = list(np.linspace(-2000, 2000, number_of_test_subjects))
        fwhm_model = models.Polynomial1D(degree=5)
        fwhm_model.c0.value = 5
        fwhm_model.c1.value = 1e-6
        fwhm_model.c2.value = 1e-6
        # fwhm_model.c3.value = 1e-6
        # fwhm_model.c4.value = 1e-6
        # fwhm_model.c5.value = 1e-6

        self.list_of_fwhm = fwhm_model(self.focus_values)



        for i in range(number_of_test_subjects):
            now = datetime.datetime.now()
            ccd = CCDData(data=np.ones((100, 1000)),
                          meta=fits.Header(),
                          unit='adu')
            ccd.header['DATE'] = now.strftime("%Y-%m-%d")
            ccd.header['DATE-OBS'] = now.isoformat()
            ccd.header['instconf'] = 'Red'
            ccd.header['obstype'] = 'FOCUS'
            ccd.header['cam_foc'] = self.focus_values[i]
            ccd.header['cam_targ'] = 0
            ccd.header['grt_targ'] = 0
            ccd.header['filter'] = 'filter'
            ccd.header['filter2'] = 'filter2'
            ccd.header['grating'] = 'grating'
            ccd.header['slit'] = '0.4 slit'
            ccd.header['wavmode'] = '400m2'
            ccd.header['rdnoise'] = 1
            ccd.header['gain'] = 1
            ccd.header['roi'] = 'user-defined'

            gaussian = models.Gaussian1D(
                mean=500,
                amplitude=600,
                stddev=self.list_of_fwhm[i]/2.35482004503)

            for e in range(100):
                ccd.data[e] = gaussian(range(1000))

            ccd.write(self.file_list[i], overwrite=True)

        self.focus_group = pandas.DataFrame(self.file_list, columns=['file'])

        focus_data = []
        for i in range(number_of_test_subjects):
            row_data = [self.file_list[i],
                        self.list_of_fwhm[i],
                        self.focus_values[i]]
            focus_data.append(row_data)
        self.focus_data_frame = pandas.DataFrame(
            focus_data,
            columns=['file', 'fwhm', 'focus'])

        self.goodman_focus = GoodmanFocus()

    def test_get_focus_data(self):

        result = self.goodman_focus.get_focus_data(group=self.focus_group)

        self.assertIsInstance(result, pandas.DataFrame)
        np.testing.assert_array_almost_equal(np.array(result['fwhm'].tolist()),
                                             self.list_of_fwhm)

    def test__fit(self):
        result = self.goodman_focus._fit(df=self.focus_data_frame)


        self.assertIsInstance(result, models.Polynomial1D)

    def test__call__(self):
        self.goodman_focus()
        self.assertIsNotNone(self.goodman_focus.fwhm)

    def test__call__Moffat1D(self):
        self.goodman_focus = GoodmanFocus(features_model='moffat')
        self.goodman_focus()
        self.assertIsNotNone(self.goodman_focus.fwhm)

    def test__call__with_list(self):
        self.assertIsNone(self.goodman_focus.fwhm)
        result = self.goodman_focus(files=self.file_list)
        self.assertIsNotNone(self.goodman_focus.fwhm)

    def test__call__list_file_no_exist(self):
        file_list = ["no_file_{}.fits".format(i) for i in range(10, 20)]
        self.assertRaises(SystemExit, self.goodman_focus, file_list)

    def test__call__not_a_list(self):
        _string = 'not a list'
        self.assertRaises(SystemExit, self.goodman_focus, _string)

    def tearDown(self):
        for _file in self.file_list:
            os.unlink(_file)


class SpectroscopicModeNameTests(TestCase):

    def setUp(self):
        self.data = {'file': ['file_{}.fits'.format(i + 1) for i in range(5)],
                     'INSTCONF': ['Blue'] * 5,
                     'FILTER': ['FILTER-X'] * 5,
                     'FILTER2': ['NO FILTER'] * 5,
                     'WAVMODE': ['IMAGING'] * 5}


    def test_imaging_mode(self):
        df = pandas.DataFrame(self.data)
        expected_name = 'IM__Blue__FILTER-X'
        mode_name = GoodmanFocus._get_mode_name(group=df)
        self.assertEqual(mode_name, expected_name)

    def test_spectroscopy_mode(self):
        self.data['WAVMODE'] = ['400  z1'] * 5
        df = pandas.DataFrame(self.data)

        expected_name = 'SP__Blue__400z1__NOFILTER'

        mode_name = GoodmanFocus._get_mode_name(group=df)

        self.assertEqual(mode_name, expected_name)



class DirectoryAndFilesTest(TestCase):

    def setUp(self):
        os.mkdir(os.path.join(os.getcwd(), 'test_dir_empty'))
        os.mkdir(os.path.join(os.getcwd(), 'test_dir_no_matching_files'))
        os.mkdir(os.path.join(os.getcwd(), 'test_dir_no_focus'))
        for i in range(3):
            ccd = CCDData(data=np.ones((100, 100)),
                          meta=fits.Header(),
                          unit='adu')
            ccd.header['obstype'] = 'OBJECT'
            ccd.header['cam_foc'] = 0
            ccd.header['cam_targ'] = 0
            ccd.header['grt_targ'] = 0
            ccd.header['filter'] = 'filter'
            ccd.header['filter2'] = 'filter2'
            ccd.header['grating'] = 'grating'
            ccd.header['slit'] = '0.4 slit'
            ccd.header['wavmode'] = '400m2'
            ccd.header['rdnoise'] = 1
            ccd.header['gain'] = 1
            ccd.header['roi'] = 'user-defined'

            ccd.write(os.path.join(os.getcwd(),
                                   'test_dir_no_focus',
                                   'file_{}.fits'.format(i+1)))

    def test_directory_does_not_exists(self):

        # goodman_focus = GoodmanFocus(arguments=arguments)
        path_non_existing = os.path.join(os.getcwd(), 'non-existing')
        self.assertRaises(SystemExit, GoodmanFocus, path_non_existing)

    def test_directory_exists_but_empty(self):
        empty_path = os.path.join(os.getcwd(), 'test_dir_empty')
        goodman_focus = GoodmanFocus(data_path=empty_path)
        self.assertRaises(SystemExit, goodman_focus)

    def test_directory_not_empty_and_no_matching_files(self):
        path = os.path.join(os.getcwd(), 'test_dir_no_matching_files')

        open(os.path.join(path, 'sample_file.txt'), 'a').close()

        goodman_focus = GoodmanFocus(data_path=path)

        self.assertRaises(SystemExit, goodman_focus)

    def test_no_focus_files(self):
        path_no_focus_files = os.path.join(os.getcwd(), 'test_dir_no_focus')
        goodman_focus = GoodmanFocus(data_path=path_no_focus_files)
        self.assertRaises(SystemExit, goodman_focus)

    def tearDown(self):

        for _file in os.listdir(os.path.join(os.getcwd(), 'test_dir_no_focus')):
            os.unlink(os.path.join(os.getcwd(), 'test_dir_no_focus', _file))

        for _file in os.listdir(os.path.join(
                os.getcwd(),
                'test_dir_no_matching_files')):

            os.unlink(os.path.join(os.getcwd(),
                                   'test_dir_no_matching_files',
                                   _file))

        os.rmdir(os.path.join(os.getcwd(), 'test_dir_empty'))
        os.rmdir(os.path.join(os.getcwd(), 'test_dir_no_focus'))
        os.rmdir(os.path.join(os.getcwd(), 'test_dir_no_matching_files'))
