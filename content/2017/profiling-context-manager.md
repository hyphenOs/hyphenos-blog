Title: Using Context Manager for Profiling
Date: 2017-08-24
Tags: profiling, with-statement, context manager, python
Category: Python Profiling
Slug: profiling-context-manager
Author: Abhijit Gadgil
Summary: We needed an ability to perform profiling in one of the classes we were implementing. The class was implementing a functionality that involved heavy computations, so it was a good idea to run profiling and find out where extra time is spent.

Recently, was implementing a class, where, we wanted to be able to 'plug-in' profiling in some functions. Summarizing some of the requirements -

1. Ability to add profiling information in several places in code. (Something like `cProfile.Profile().enable()` and `cProfile.Profile.disable()` done frequently.

2. Ability to enable profiling globally or not, so when globally disabled, it should add a minimum overhead.

3. Being able to related profiling information with the code.

My initial idea was to have a class wide `cProfile.Profile()` object and keep enabling and disabling it for the parts of the code I wanted to profile. There are a few problems with this - viz.

1. The code gets littered with `enable`/`disable` code.

2. Also, to meet requirement 2. above, this would have been wrapped in an `if` statement

3. Dumping stats only for some part of the code - in a section would become a little irritating to handle (see below).

For this type of problems, Context Managers in Python look like a good choice. All the `enable`/`disable` logic, `if` conditions etc. can be neatly wrapped inside the `__enter__` and `__exit__` methods.

The code for the `class Profiler` looks like following

```python

class Profiler(object):

    def __init__(self, parent=None, enabled=False, contextstr=None):
				"""
				parent: the callee
				enabled: Should profile or not
				contextstr: used as a marker to separate dump data.
				"""

        self.parent = parent
        self.enabled = True

        self.stream = StringIO.StringIO()
        self.contextstr = contextstr or str(self.__class__)

        self.profiler = cProfile.Profile()

    def __enter__(self, *args):

        if not self.enabled:
            return

        # Start profiling.
        self.stream.write("profile: {}: enter\n".format(self.contextstr))
        self.profiler.enable()

    def __exit__(self, exc_type, exc_val, exc_tb):

        if not self.enabled:
            return

        self.profiler.disable()

        sort_by = 'cumulative'
        ps = pstats.Stats(self.profiler, stream=self.stream).sort_stats(sort_by)
        ps.print_stats(0.1)

        self.stream.write("profile: {}: exit\n".format(self.contextstr))
        print (self.stream.getvalue())

				# Raise any exception if raised during execution of code.
			  return False

```

And then this code can be called as follows -

```python

		with Profiler(contextstr="---foo profiling ----", enabled=True):
				# code to be profiled

```

Pretty simple and extremely readable. Also, this just works fine as a nested Context Manager, cool right?

Some Notes:

1. Just noticed a quirk of `pstats.Stats` Constructor. If we pass a `Profile` object to the `pstats.Stats` Constructor as above, unless the `Profile` object is `enable`d, the Constructor raises an Exception that looks like -

```bash

  File "/usr/lib/python2.7/pstats.py", line 81, in __init__
    self.init(arg)
  File "/usr/lib/python2.7/pstats.py", line 95, in init
    self.load_stats(arg)
  File "/usr/lib/python2.7/pstats.py", line 124, in load_stats
    % (self.__class__, arg))
TypeError: Cannot create or construct a <class pstats.Stats at 0x7f683bec19a8> object from <cProfile.Profile object at 0x7f683bf1a6e0>
```

2. Also, returning `False` would make sure, if the running code within a `with` block raised an exception, that gets re-raised (so we do not mess up with the Application flow by consuming exceptions.)
