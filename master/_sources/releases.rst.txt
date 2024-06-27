Release History
###############


v1.21.0 (2024-08-20)
====================

Features
--------
- Automatically timeout and closes hutch-python sessions after the user has been
  idle for a certain number of hours. The number of hours can be set in conf.yml
  for each hutch. If no value is set the default timeout duration is 48 hours.

Maintenance
-----------
- Document some first-pass efforts at running hutch-python in jupyter notebooks.
- Fix an issue where an upstream numpy 2 incompatibilty was breaking the pypi builds.

Contributors
------------
- janeliu-slac
- zllentz



v1.20.0 (2024-04-19)
====================

Features
--------
- Allow per-session separate ipython histories via ``--hist-file``
  command-line argument. If omitted, default ipython behavior is used.
  When ``--hist-file`` is included with no argument, the history file
  will be written a local operator console hard drive, if available.
  An argument can be provided to use any file as the history.sqlite file.

Contributors
------------
- zllentz



v1.19.0 (2024-04-15)
====================

Features
--------
- Updates EpicsArch script, adding several debug/testin flags and ensuring
  information is up-to-date.  Includes:

  - ``update_file``: feature that updates EpicsArch based on current questionnaire
  - ``--softlink``: point arch file to new experiment via symbolic link
  - ``--level``: specify a debug level
  - ``--cds-items``: displays questionnaire data for a given run and experiment
  - ``--link-path``: allows user to provide custom filepath for softlinks
- Adds load_level conf.yaml key for choosing the method used to gather happi devices

Contributors
------------
- c-tsoi
- tangkong



v1.18.5 (2023-09-14)
====================

Maintenance
-----------
- Strips whitespace from PVs gathered during cam_load routine.

Contributors
------------
- tangkong


v1.18.4 (2023-07-26)
====================

Maintenance
-----------
- Unpin strict pyqt pin, we now just require pyqt5 of any flavor.
- Fix a bug where non-conda installs and non-standard conda installs
  (like mambabuild intermediates) would be unable to use the
  `hutch-python --create` cookiecutter tool.
- Add send and recv methods to the fake zmq socket because newer
  versions of the lcls2 daq code are expecting recv.
- Fix pyproject.toml typo docs -> doc.
- Update requirements.txt for accuracy now that
  psdaq-control-minimal is available on pypi.
- Include docs-versions-menu for the sphinx docs builds.


Contributors
------------
- klauer
- zllentz


v1.18.3 (2023-04-11)
====================

Maintenance
-----------
- Set the package name back to hutch-python for conda builds
  for consistency's sake.

Contributors
------------
- klauer
- zllentz


v1.18.2 (2023-04-11)
====================

Maintenance
-----------
- Fix an issue where the test suite would not run with the latest
  lightpath. This was a test-suite only bug, not a runtime
  function bug.
- Fix an issue where pypi/conda upload builds would not have
  proper authentication.

Contributors
------------
- zllentz


v1.18.1 (2023-04-04)
====================

Bugfixes
--------
- Fix an edge case where all hutch devices may be skipped in the load
  if all of them are missing from lightpath.

Maintenance
-----------
- hutch-python no longer uses Travis CI and has migrated to GitHub Actions for
  continuous integration, testing, and documentation deployment.
- hutch-python has been migrated to use setuptools-scm, replacing versioneer, as its
  version-string management tool of choice.
- hutch-python has been migrated to use the modern ``pyproject.toml``, replacing
  ``setup.py`` and related files.
- Older language features and syntax found in the repository have been updated
  to Python 3.9+ standards by way of ``pyupgrade``.
- Sphinx 6.0 is now supported for documentation building.
  ``docs-versions-menu`` replaces ``doctr-versions-menu`` and ``doctr`` usage
  for documentation deployment on GitHub Actions.  The deployment key is now no
  longer required.
- pyupgrade was used to update annotations, and pycln was used to clean up
  imports.

Contributors
------------
- klauer
- zllentz



v1.18.0 (2022-10-25)
====================

Features
--------
- Updates database loading to utilize updated lightpath (v1.0.0)
  for loading devices. This makes the newer, reworked version of
  lightpath available in the session instead of the old version.

Maintenance
-----------
- Fix issues with running tests offline on LCLS servers.

Contributors
------------
- tangkong
- zllentz


v1.17.0 (2022-07-27)
====================

Features
--------
- In the facility logger, show the source of the exception in the facility
  log message summary. This will make it easier to understand the cause of
  uncaught exceptions that get sent to the facility logger.


v1.16.0 (2022-06-03)
====================

Features
--------
- Add the ``obj_config`` key to the ``conf.yml`` configuration file.
  This allows the user to pass in the path to a file that contains
  object reconfiguration information.
  Currently, tab completion whitelists/blacklists and ``ophyd``
  component ``kind`` configuration are supported.
- Switch the best effort callback instance ``bec`` to use the
  ``BECOptionsPerRun`` callback from ``nabs`` instead of the previous
  ``BestEffortCallback`` from ``bluesky``.
  This new class is a subclass of ``BestEffortCallback`` that allows
  us to configure its options on a per-scan basis by setting metadata keys.
  This means we can do things like disabling plots on scans where it
  makes no sense, and perhaps more features in the future.

Contributors
------------
- tangkong


v1.15.0 (2022-05-02)
====================

Features
--------
- Add automatic ELOG post configuration to the run engine.
- Add a much more helpful startup banner that calls out specific
  helpful objects in the namespace.

Fixes
-----
- Make the dev package identifier very robust.

Maintenance
-----------
- Configure and satisfy pre-commit checks.
- Rework and clean up the post-IPython initialization.

Contributors
------------
- tangkong


v1.14.0 (2022-03-31)
====================

Features
--------
- Ctrl+C now aborts the current run, returning the RunEngine to a
  ready / idle state.  The old pause functionality has been moved to
  Ctrl+\\.
- Include per-device load times for devices loaded from happi.
- Load a run-engine wrapped namespace (lowercase ``re``) as a replacement
  for the proliferation of roll-your-own wrappers, and also add wrapped
  daq scan functions to the ``daq`` object.
- Add plan wrappers to all plans to make it clear which are plans and
  which are functions.
- Show the environment information at startup so the user knows what
  version of the software they are running.

Contributors
------------
- klauer
- tangkong
- zllentz


v1.13.2 (2022-02-11)
====================

Fixes and Maintenance
---------------------
Configure ``IPython`` to disable ``black`` input reformatting,
for three reasons:

  1. Throws errors in our terminal after the first input
  2. Conflicts with advice in the ``black`` github issues that assert that
     ``black`` is not ready to be used as an import.
  3. I don't think it's a good fit for the scientific computing and expect
     that it will be annoying in practice.

Contributors
------------
- zllentz


v1.13.1 (2022-02-07)
====================

Fixes and Maintenance
---------------------
- Noisy logger detection is now configured but disabled by default.
- Noisy logger detection is split between the file and the console.
- Allow both QtAgg and Qt5Agg as valid matplolib backends for the loaded
  environment.
- Include ``daq_type`` and ``daq_host`` in the list of valid keys for the
  purpose of warning the user about a malformed config. These have been
  valid, but produce an incorrect warning.
- Expand the default LCLS2 DAQ timeout from 1 second to 10 seconds to fix
  an issue where we would time out on expected long operations.

Contributors
------------
- klauer
- zllentz


v1.13.0 (2021-11-10)
====================

Features
--------
- Noisy loggers will automatically be filtered based on message rate metrics
  as to not disturb the user.
- Warnings will be redirected to the logging stream, making them show up
  in the log files.
- Warnings will only be shown once each per session per warning source,
  rather than after every IPython line, via demoting them to DEBUG level
  in the console, as to not disturb the user.
- Callback exception log messages will be demoted to DEBUG level in the
  console as to not disturb the user.

Fixes and Maintenance
---------------------
- Add documentation about the log namespace.
- Fix an issue where certain helpful namespaces inside of helpful namespaces
  in specific situations would not render properly.
- Fix various issues with the CI and move it to Python 3.9 only.
- Remove no longer needed inflection dependency


v1.12.0 (2021-09-28)
====================

Features
--------
- Add functionality for specifying parameters for and automatically
  instantiating the LCLS2 DAQ object (BlueskyScan) via an optional
  psdaq.control dependency and configuration keys.

Fixes and Maintenance
---------------------
- Restore the CI pypi build to running.
- Properly setup lightpath, psdm_qs_cli, and elog as optional dependencies.
- Clean up the documentation about the configuration file.


v1.11.2 (2021-08-09)
====================

Fixes and Maintenance
---------------------
- Fix order of message logging in the IPython input logger. Previously, the
  In log message wouldn't happen until after the command had already finished.
  Now, the In message is logged, then any normal log messages are logged, and
  then finally the Out message is logged, all neatly in order.
- Adjust exception handling output for log files and for centralized logger.
- Log exceptions in threads
- Only log to the centralized PCDS logger when on a PCDS host
- Support stacklevel for centralized logging on Python 3.8+
- Make elog and lightpath optional dependencies for pip


v1.11.1 (2021-07-09)
====================

Fixes and Maintenance
---------------------
- Fix issues related to matplotlib setup in headless mode. This means that it
  will no longer crash the session when used without x-forwarding.


v1.11.0 (2021-06-04)
====================

Features
--------
- Added ability to opt-in to specific Ophyd Object instance DEBUG logs.  Call
  ``logs.log_objects(obj1, obj2)`` to configure it for ``obj1`` and ``obj2``,
  for example, and clear it by way of ``logs.log_objects_off()``.
- Added a new ``logs`` object in the IPython namespace, offering easy access
  to common log-related tools.


Fixes and Maintenance
---------------------
- Refactored logging setup to be more modular and slightly better documented.
  The ophyd logger is no longer "hushed", but is now filtered through the
  new ``ObjectFilter`` mechanism.


v1.10.1 (2021-06-03)
====================

Bugfixes
--------
- Fix an issue where ophyd signals were configured to wait "forever" for their
  write timeouts. By default, this is now a 5 second timeout instead of no
  timeout. This unfortunate default resulted in some cases where PVs would
  get "stuck" in a "set_and_wait" that would never end. In ophyd, this default
  is intentionally left to infinite to satisfy the common case where signals
  don't update to the final value for a long period of time.
  These cases are very uncommon at the LCLS.


v1.10.0 (2021-04-15)
====================

Features
--------
- ``IterableNamespace`` has been upgraded to be ``HelpfulNamespace``, while
  maintaining a backward-compatible import name.  This class supports the
  IPython "pretty repr" and HTML repr hooks to provide user-friendly tables of
  items available in the namespace, as well as direct keyword-access to
  elements of the namespace.
- All objects loaded in load_conf have been annotated with what they are used
  for in the Python session. These annotations are available when viewing
  the ``HelpfulNamespace`` pretty and HTML reprs.

Bugfixes
--------
- Fix an issue where the get_current_hutch scripts were using a deprecated and
  removed argument structure.


v1.9.1 (2021-02-10)
===================

Bugfixes
--------
- Display small values in scientific notation during scans, rather than as
  0.000000. Similarly handle very large values.
- Include the BestEffortCallback that we are using in the hutch's namespace
  for easy access.


v1.9.0 (2020-12-22)
===================

Features
--------
- Add ``epicsarch-qs`` script that will handle creating ``epicsArch`` files
  from the LCLS questionnaire.
- Include plans from ``nabs`` in the default namespaces.
- Include calcs from ``pcdsdevices`` in the default namespaces.

Bugfixes
--------
- Fix issue where tab completion filters would not work due to ``IPython``
  quirks in cases where ``jedi`` is disabled.
- Fix issue where devices with negative z would not load from ``happi``.

Maintenance
-----------
- Update the hutch environment templates.


v1.8.0 (2020-10-23)
===================

Features
--------
- Include the beam_stats and lcls objects in every hutch python session.
- Enable scan PVs for all consumers (instead of starting as disabled).

Bugfixes
--------
- Fix load order so that beamline and experiment files happen as late as possible.


v1.7.0 (2020-10-21)
===================

Features
--------
- Alert and show the user the full traceback when there are issues loading
  user files like beamline and experiment files.
- Ask the user if it is okay to proceed with the user file loading failure,
  which typically renders the session useless, rather than just
  passing over the issue.


v1.6.1 (2020-10-07)
===================

Fixes and Maintenance
---------------------
- Re-tag of v1.6.0 to trigger the anaconda upload.


v1.6.0 (2020-10-07)
===================

Features
--------
- Expand motors group to have all positioners.
- Add detectors (d) namespace for ami detectors.
- Time safe_load and report duration.
- Add a few simulated motors by default in a sim namespace.


Fixes and Maintenance
---------------------
- Pass hutch name to daq to avoid calling get_hutch_name, which can be slow.
- Disable tree namespace until issues are resolved.


v1.5.1 (2020-10-02)
===================

Fixes and Maintenance
---------------------
- Remove jedi tab completion again, again.


v1.5.0 (2020-09-18)
===================

Features
--------
- Send uncaught exceptions to the centrally configured logstash

Fixes and Maintenance
---------------------
- Fix issues related to LivePlot segmentation faults
- Remove jedi tab completion, again
- Fix and standardize the CI configuration


v1.4.0 (2020-08-18)
===================

Features
--------
- Load hutch-python with engineering mode disabled to optimize interactive
  use.

Fixes and Maintenance
---------------------
- Fix bad log message handler in test suite


v1.3.1 (2020-07-27)
===================

Fixes and Maintenance
---------------------
- Test suite update for compatibility with lightpath v0.6.5


v1.3.0 (2020-07-01)
===================

Features
--------
- Pack camviewer config into a camviewer namespace for ease of access
  and to avoid name collisions with other data sources.


v1.2.3 (2020-05-29)
===================

Fixes and Maintenance
---------------------
- Fix issue with tests freezing


v1.2.2 (2020-05-21)
===================

Fixes and Maintenance
---------------------
- Fix issue with generated area detectors having the wrong prefix


v1.2.1 (2020-05-21)
===================

Fixes and Maintenance
---------------------
- Fix issue preventing conda upload on tag


v1.2.0 (2020-05-21)
===================

Features
--------
- Configure the logstash logger using ``pcdsutils``

Fixes and Maintenance
---------------------
- Adjust for latest ``happi`` API
- Add documentation about logstash logging
- Hush the noisiest loggers that are spamming the terminal sessions


v1.1.1 (2020-02-05)
===================

Fixes and Maintenance
---------------------
- Make tests compatible with ``ophyd`` ``v1.1.1``
- Small adjustments to remove some warnings
- Small updates to hutch directory generator

v1.1.0 (2020-01-10)
===================

Features
--------
- Add ``archapp`` support. Check out the ``archive`` object in the hutch
  python namespace for access to the archiver appliance data.

v1.0.1 (2019-03-08)
===================

Fixes and Maintenance
---------------------
- Clean up code for the ``hutch-python`` launcher
- Fix issues with the test suite
- Fix issues with automatically loading ipython profiles

v1.0.0 (2018-10-12)
===================

API Breaks
----------
- Swap to the newer ``psdm_qs_cli`` API for experiment loading that is
  compatible with commissioning experiment names.

v0.7.0 (2018-08-06)
===================

Features
--------
- Add a ``ScanVars`` class for the legacy scan pvs tie-in.
- Automatically load all cameras defined in the camviewer config file.
- Add the ``--exp`` arg for forcing the active experiment for the duration
  of a session.

Bugfixes
--------
- Exclude having a beampath when there are no devices on the path.
  This is because the resulting empty path causes issues in the
  environment. This will most commonly occur when calling
  ``hutch-python`` with no arguments.

Misc
----
- Fix a few typos

v0.6.0 (2018-05-27)
===================

Features
--------
- Provide well-curated namespaces for ``bluesky`` plans. These are in the
  shell as ``bp`` (bluesky plans) for normal plans, ``bps`` (bluesky plan
  stubs) for plans that are not complete on their own, and ``bpp``
  (bluesky plan preprocessors) for plans that modify other plans.

Bugfixes
---------
- Show a correct error message when there is an ``ImportError`` in an
  experiment file. This previously assumed the ``ImportError`` was from
  a missing experiment file. (#126)
- Prevent duplicate names in `tree_namespace` from breaking the tree.
  Show a relevant warning message. (#128)
- Do not configure the ``matplotlib`` backend for IPython if a user does not
  have a valid ``$DISPLAY`` environment variable. The most common case of this
  is if X-Forwarding is disabled. (#132)

v0.5.0 (2018-05-08)
===================

Bugfixes
---------
- fix issue where importing hutchname.db could break under certain conditions
- fix issue where autocompleting a ``SimpleNamespace`` subclass would always
  have an extra mro() method, even though this is a class method not shared
  with instances.
- add logs folder to the hutch-python directory creator

API Changes
-----------
- ``metadata_namespace`` renamed to `tree_namespace`

v0.4.0 (2018-04-23)
===================

Features
--------
- ``elog`` object and posting
- load devices upstream from the hutch along the light path

Bugfixes
--------
- Allow posting bug reports to github from the control room machines through the proxy
- Optimize the namespaces for faster loads and avoid a critical slowdown bug
- Make hutch banner as early as possible to avoid errant log messages in front of the banner
- Make cxi's banner red, as was intended
- hutch template automatically picks the latest environment, instead of hard-coding it

v0.3.0 (2018-04-06)
===================

Features
--------
- In-terminal bug reporting
- Port of the old python presets system
- Objects from the questionnaire are included in the experiment object
- Experiment object is always included

Bugfixes
--------
- No longer create 1-item metadata objects
- ``db.txt`` is created in all-write mode

API Changes
-----------
- Daq platform map is no longer stored in the module, this now must be configured
  through ``conf.yml`` for nonzero platforms.

Minor Changes
-------------
- ``qs.cfg`` renamed to ``web.cfg``, with backwards compatibility
