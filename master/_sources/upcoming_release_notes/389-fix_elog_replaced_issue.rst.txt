389 fix_elog_replaced_issue
#################

API Changes
-----------
- N/A

Features
--------
- N/A

Bugfixes
--------
- Fix an issue where the user could clobber their own ``elog``
  object in a way that would allow the ``ElogPoster`` utility to
  load and then fail at scan time.

Maintenance
-----------
- N/A

Contributors
------------
- zllentz
