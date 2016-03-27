##
#  @file utils.py
#
#  Internal utilities for sconsUtils.
##

from __future__ import absolute_import, division, print_function
import os
import sys
import warnings
import subprocess
import platform
import SCons.Script


##
#  @brief A dead-simple logger for all messages.
#
#  This simply centralizes decisions about whether to throw exceptions or print user-friendly messages
#  (the traceback variable) and whether to print extra debug info (the verbose variable).
#  These are set from command-line options in state.py.
##
class Log(object):

    def __init__(self):
        self.traceback = False
        self.verbose = True

    def info(self, message):
        if self.verbose:
            print(message)

    def warn(self, message):
        if self.traceback:
            warnings.warn(message, stacklevel=2)
        else:
            print(message, file=sys.stderr)

    def fail(self, message):
        if self.traceback:
            raise RuntimeError(message)
        else:
            if message:
                print(message, file=sys.stderr)
            SCons.Script.Exit(1)

    def flush(self):
        sys.stderr.flush()


##
#  @brief Internal function indicating that the OS has System
#   Integrity Protection.
##
def _has_OSX_SIP():
    hasSIP = False
    os_platform = SCons.Platform.platform_default()
    # SIP is enabled on OS X >=10.11 equivalent to darwin >= 15
    if os_platform == 'darwin':
        release_str = platform.release()
        release_major = int(release_str.split('.')[0])
        if release_major >= 15:
            hasSIP = True
    return hasSIP


##
#  @brief Returns name of library path environment variable to be passed through
#  or else returns None if no pass through is required on this platform.
def libraryPathPassThrough():
    if _has_OSX_SIP():
        return "DYLD_LIBRARY_PATH"
    return None


##
#  @brief Returns True if the shebang lines of executables should be rewritten
##
def needShebangRewrite():
    return _has_OSX_SIP()

##
#  @brief Returns library loader path environment string to be prepended to external commands
#         Will be "" if nothing is required.
##


def libraryLoaderEnvironment():
    libpathstr = ""
    # If we have an OS X with System Integrity Protection enabled or similar we need
    # to pass through DYLD_LIBRARY_PATH to the external command.
    pass_through_var = libraryPathPassThrough()
    if pass_through_var is not None:
        for varname in (pass_through_var, "LSST_LIBRARY_PATH"):
            if varname in os.environ:
                libpathstr = '{}="{}"'.format(pass_through_var, os.environ[varname])
                break
    return libpathstr

##
#  @brief Safe wrapper for running external programs, reading stdout, and sanitizing error messages.
#
#  Note that the entire program output is returned, not just a single line.
##


def runExternal(cmd, fatal=False, msg=None):
    if msg is None:
        try:
            msg = "Error running %s" % cmd.split()[0]
        except:
            msg = "Error running external command"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        if fatal:
            raise RuntimeError("%s: %s" % (msg, stderr))
        else:
            from . import state  # can't import at module scope due to circular dependency
            state.log.warn("%s: %s" % (msg, stderr))
    return stdout


##
#  @brief A Python decorator that injects functions into a class.
#
#  For example:
#  @code
#  class test_class(object):
#      pass
#
#  @memberOf(test_class):
#  def test_method(self):
#      print "test_method!"
#  @endcode
#  ...will cause test_method to appear as as if it were defined within test_class.
#
#  The function or method will still be added to the module scope as well, replacing any
#  existing module-scope function with that name; this appears to be unavoidable.
##
def memberOf(cls, name=None):
    if isinstance(cls, type):
        classes = (cls,)
    else:
        classes = tuple(cls)
    kw = {"name": name}

    def nested(member):
        if kw["name"] is None:
            kw["name"] = member.__name__
        for scope in classes:
            setattr(scope, kw["name"], member)
        return member
    return nested
