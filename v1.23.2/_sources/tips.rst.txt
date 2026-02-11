===============
Tips and Tricks
===============


Using Partial for Scan Variants
-------------------------------
Suppose in an experiment you're always calling a function with a particular
argument, or at a hutch you want a specially-named scan for a motor that is
used every shift. You can write custom variants of any scan using a
Python built-in, ``functools.partial``

.. code-block:: python

   from bluesky.plans import scan
   from functools import partial
   from hutch.db import my_motor

   # Put arguments in early
   my_scan = partial(scan, [], my_motor)

   # Now we only need to provide start, stop, number of points
   RE(my_scan(0, 100, num=10))


Device Console Logging Configuration
------------------------------------
Hutch Python has some built-in spam prevention, but sometimes you'll find
yourself wanting to get rid of specific object's console logs, typically
because they are distracting and irrelevant to what you're trying to
accomplish. Other times you'll want to focus on specific objects, or
perhaps turn off the console logging entirely. All of these are possible
using the ``logs`` namespace.

Here are some example of this:

.. code-block:: python

   # In IPython, you can skip these imports
   from hutch.db import logs, noisy_device, important_noisy_device

   # Silence a specific noisy device
   logs.filter.blacklist.append(noisy_device.name)

   # Unsilence an automatically filtered spammy device
   logs.filter.whitelist.append(important_noisy_device.name)

   # Focus on specific objects to see extra debug information
   logs.log_objects(important_noisy_device)

   # Clear the "log_objects" focus from the previous line
   logs.log_objects_off()


In an active Hutch Python session, try ``logs.filter`` to see the current
filter status.
