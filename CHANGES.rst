.. _v2.0.0:

2.0.0 Unreleased
================

- Added FWHM, Best image and data to results.
- Bumped version one major step due to the change on the format of the results.
- Returned result is a list of dictionaries now.


.. _v1.0.0:

1.0.0
=====

- Removed Travis CI [#31]
- Replaced separator to double underscore [#34, #35]
- Updated documentation.


.. _v0.3.6:

0.3.6
=====

- Added python 3.7 and 3.8 to Travis CI
- Removed astroconda from environment.yml and specified python 3.8 to avoid 3.9


.. _v0.3.5:

0.3.5
=====

- Implemented Github Actions
- Removed astroconda channel from environment


.. _v0.3.4:

0.3.4
=====

- Fixed version of `ccdproc` to `1.3.0.post1`. `ccdproc==2.0.0` does have some
  problems reported on `astropy/ccdproc#699`


.. _v0.3.3:

0.3.3
=====

- Changed Sigma Clipping iterations from 1 to 3
- Added sigma clip iterations as argument to function `get_fwhm` though this is
  not exposed to the user.

.. _v0.3.2:

0.3.2
=====

- Changed logger setup
- Moved data directory validation from instantiation to execution.


.. _v0.3.1:

0.3.1
=====

- Fixed bug on the calculation of the pseudo-derivate used to find best focus
  value
- Updated hardcoded string that defines the Imaging wavmode from `Imaging` to
  the new `IMAGING`.
- Added docstrings

.. _v0.3.0:

0.3.0
=====

- Created dedicated documentation for readthedocs.
- Fixed bug where return was missing,
- GoodmanFocus need to be instantiated only once [#19]
- Calling instance of GoodmanFocus can receive a list of files as input [#19]
- Argument --file-pattern is now actually used in file selection [#18]
- Eliminated some warnings.
- Included plots in documentation.

.. _v0.2.0:

0.2.0
=====

- Added messages when no file matches the `--obstype` value, by default is
  `FOCUS` [#9]
- Replaced `parser.error` by `log.error` and `sys.exit` when the directory does
  not exist and when exists but is empty.
- Added test for cases when the directory does not exist, when is empty and when
  no file matches the selection on `--obstype` which by default is `FOCUS`.
- Replaced `logging.config.dictConfig` by `logging.basicConfig` which fixed
  several issues. For instance `--debug` was unusable, and also there were
  duplicated log entries for the file handler when used as a library in other
  application. [#10]
- Replaced the use of the function `get_args` by using arguments on class
  instantiation instead
- Created name for modes [#11]

0.1.3
=====

- Fixed some issues with documentation
- Added .readthedocs.yml file for RTD builds
- Added ``install_requires`` field in ``setup()``
- Removed python 3.5 from the supported versions.