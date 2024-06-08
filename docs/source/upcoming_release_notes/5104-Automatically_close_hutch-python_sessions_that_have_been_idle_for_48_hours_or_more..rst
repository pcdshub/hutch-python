5104 Automatically close hutch-python sessions that have been idle for 48 hours or more.
#################

API Changes
-----------
Added a new class object IPythonSessionTimer. The timer starts by calling the method _start_session().

Features
--------
Times out a hutch-python session if it has been idle for 48 hours or more.

Bugfixes
--------
- N/A

Maintenance
-----------
- N/A

Contributors
------------
Jane Liu
