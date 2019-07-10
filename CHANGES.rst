0.2.1 (Unreleased)
==================

- add entry

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