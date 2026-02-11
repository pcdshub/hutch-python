Reporting Issues
================
One advantage of standardizing the logging system and startup scripts with
hutch-python is programmatically being able to gather information about the
current Python environment. One common use case for much of this information
is being able to diagnose software bugs after the fact if we are diligent about
recording the pertinent information. The `hutch_python.bug.report_bug` command
wraps much of this functionality up by asking a few simple questions of the
operator and noting the current environment and log file. By the end of the
function we should have:

    * A one line description of the problem
    * A more verbose explanation of the issue and how it affects operations
    * A name to follow up with additional questions / closeout
    * The commands entered by the operator
    * The current CONDA environment
    * Relevant logfiles written to by this Python session
    * Capture output printed to the terminal
    * Any packages installed in "development" mode

This command is available as both an actual Python function and an IPython
magic. The ladder allows you to pinpoint the exact function that is causing
issues.

.. code-block:: python

   %report_bug my_buggy_function()

If you call `report_bug` as a regular function you can specify a number of past
commands you want to include in the overall report. This allows you to
posthumously report issues without running the actual function again.

   .. autofunction:: hutch_python.bug.report_bug
      :noindex:

Issue Lifecyle
^^^^^^^^^^^^^^
After reporting the issue on the command line, an issue will be created at
https://github.com/pcdshub/Bug-Reports. This will alert those subscribed to
this repository via email about the current issue and appropriate action will
be made by the PCDS staff. This may mean a deeper look at the linked log files
and/or creating a distilled issue or action item in a different repository.
