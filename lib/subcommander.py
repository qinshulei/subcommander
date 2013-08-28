#!/usr/bin/python

'''subcommander.py

A python implementation of subcommander.sh. It should work almost exactly the
same way.

'''

import os
import warnings
import subprocess
import textwrap
import logging

logger = None


def format_msg(s):
    """Helper that unindents and unwraps multiline docstrings."""
    return textwrap.fill(textwrap.dedent(s).strip())


def format_script(s):
    """Helper that unindents multiline docstrings."""
    return textwrap.dedent(s).strip() + '\n'


class SubcommanderUserError(Exception):
    """Subclasses of this class will not display a python traceback when thrown
    to the user.

    """
    def __str__(self):
        if self.filename:
            return format_msg("%s: %s" % (self.strerror, self.filename))
        else:
            return format_msg(self.strerror)


class CalledDirectlyError(SubcommanderUserError, EnvironmentError):
    def __init__(self):
        super(CalledDirectlyError, self).__init__(
            1,
            """Subcommander is an abstraction that is not meant to be run under
            its own name. Instead, create a symlink to it, with a different
            name. And read the instructions.""")


class SubcommandDirectoryNotConfiguredError(SubcommanderUserError, EnvironmentError):
    def __init__(self, exec_path_envname, rcfile):
        super(SubcommandDirectoryNotConfiguredError, self).__init__(
            6,
            """Could not find %s set in the environment. This should specify
            the path to subcommands. Recommend adding it to %s.""" % (
                exec_path_envname, rcfile))


class SubcommandDirectoryMissingError(SubcommanderUserError, EnvironmentError):
    def __init__(self, exec_path):
        super(SubcommandDirectoryMissingError, self).__init__(
            4,
            """Subcommands directory does not exist. Place executable files
            here to enable them as sub-commands""",
            exec_path)


class NoCommandSpecifiedError(SubcommanderUserError, EnvironmentError):
    def __init__(self):
        super(NoCommandSpecifiedError, self).__init__(
            2,
            "No COMMAND specified.")


class ConfigFileNotExecutableError(SubcommanderUserError, EnvironmentError):
    def __init__(self, configfile):
        super(ConfigFileNotExecutableError, self).__init__(
            5,
            "Configuration file is not executable",
            configfile)


class UnknownSubcommandError(SubcommanderUserError, EnvironmentError):
    def __init__(self, command):
        super(UnknownSubcommandError, self).__init__(
            7,
            "Unknown %s command" % os.environ['SC_MAIN'],
            command)


def create_rc_file(rcfile, exec_path_envname):
    """The rcfile does not exist, so create one prepopulated with some helpful
    comments.

    """
    logger.warn("Creating rcfile %s." % rcfile)
    with open(rcfile, 'w') as fp:
        fp.write(format_script("""
            #!/bin/sh

            # This file is executed by '%(SC_MAIN)s' every time you run a
            # '%(SC_MAIN)s' subcommand. You can edit this script, or replace it
            # with your own executable script or compiled program, so long as
            # you take care to exec() the command passed in as arguments, as is
            # done below.

            # This line sets %(exec_path_envname)s to ~/usr/lib/%(SC_MAIN)s
            # unless it is overridden in the environment.
            export %(exec_path_envname)s="${%(exec_path_envname)s:-~/usr/lib/%(SC_MAIN)s}"

            # If you have hooks to execute or customizations to make to the
            # environment, you may do so here.

            # The following line must be present for '%(SC_MAIN)s' to function.
            # It ends the script; any lines after it will never be reached.
            exec "$@"
            """ % {
                'exec_path_envname': exec_path_envname,
                'SC_MAIN': os.environ['SC_MAIN'],
            }))
        os.fchmod(fp.fileno(), 0755)


def verify_not_called_directly():
    # Users shouldn't invoke 'subcommander' directly.
    if os.environ['SC_MAIN'].startswith('subcommander'):
        # FIXME: this should instead walk a user through setting up a
        # subcommander-based tool, creating symlinks etc.
        raise CalledDirectlyError


def get_exec_path(exec_path_envname, rcfile):
    try:
        exec_path = os.environ[exec_path_envname]
    except KeyError:
        raise SubcommandDirectoryNotConfiguredError(exec_path_envname, rcfile)

    exec_path = os.path.expanduser(exec_path)

    if not os.path.isdir(exec_path):
        raise SubcommandDirectoryMissingError(exec_path)

    return exec_path


def show_help(exec_path):
    help_executable = os.path.join(exec_path, 'help')
    if os.access(help_executable, os.R_OK|os.X_OK):
        subprocess.call([help_executable])
    else:
        logger.error("usage: %(SC_NAME)s COMMAND [ARGS...]\n" % os.environ)


def get_subcommand(command, exec_path):
    """Find the first executable file that matches the set of commands"""
    subcommand = exec_path
    args = []
    for n, arg in enumerate(command):
        commands, args = command[:n+1], command[n+1:]
        subcommand = os.path.join(exec_path, *commands)

        if not os.access(subcommand, os.R_OK|os.X_OK):
            raise UnknownSubcommandError(' '.join(commands))

        if os.path.isfile(subcommand):
            break

    return subcommand, args


def subcommander(argv0, *args):
    """

    The following arguments are special to subcommander-based tools, and will
    be plucked out of the command line for processing:

    -h, --help
    -V, --version
    -v, --verbose

    """
    argv0_basename = os.path.basename(argv0)
    os.environ['SUBCOMMANDER_ARGV0'] = argv0_basename
    rcfile = "%(HOME)s/.%(SUBCOMMANDER_ARGV0)src" % os.environ
    exec_path_envname = ('%s_EXEC_PATH' % argv0_basename).upper().replace(' ', '_')

    verify_not_called_directly()

    # create boilerplate rcfile if nonexistent
    if not os.path.exists(rcfile):
        create_rc_file(rcfile, exec_path_envname)

    # ensure rcfile is executable
    if not os.access(rcfile, os.X_OK):
        raise ConfigFileNotExecutableError(rcfile)

    # if we haven't set the "seen the rc file" flag, set it and bounce through
    # the rcfile
    if not os.environ.get('SC_RC_APPLIED'):
        os.environ['SC_RC_APPLIED'] = 1
        return os.execv(rcfile, (rcfile, argv0) + args)

    exec_path = get_exec_path(exec_path_envname, rcfile)

    subcommand, args = get_subcommand(args, exec_path)

    if os.path.isdir(subcommand):
        show_help(subcommand)
        raise NoCommandSpecifiedError()

    # execv never returns; I 'return' to indicate execution won't continue
    return os.execv(subcommand, (subcommand,) + args)


def main():
    import sys
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logger.addHandler(logging.StreamHandler())
    try:
        return subcommander(*sys.argv)
    except SubcommanderUserError, e:
        # If a SubcommanderUserError occurs, show a normal-looking error
        # message, not a Python traceback.
        logger.error(e)
        return e.errno


if __name__ == '__main__':
    raise SystemExit(main())
