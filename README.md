# Subcommander

Branch 'mkii':

- Eliminate default .d directory; default to /usr/lib/blah or ~/usr/lib/blah
- Perform recursive walk; don't rely on sub-symlinks to subcommander
- implement in python
- try for python 2.4/centos 5 compatibility (yuck)
- creates rcfile if nonexistent
- package so may be installed system-wide by package manager/pip/easy\_install,

---

Do you have a collection of tools and scripts that you've written to save time
at the command line? Is it hard to keep them documented, and difficult for new
teammates to get familiar with them? Subcommander is here to help.

Several familiar tools (like git, subversion, cvs, zip, even django-admin.py,
etc., follow a pattern where the main executable is invoked with an argument
naming another executable specific to that system. For example, `git push`
causes `git` to invoke `git-push`. This establishes a kind of "namespace" for
executables.

Git also performs *context discovery* for its subcommands. Whenever git is
invoked, the first thing it does is identify what git repository you intend for
it to work with, by checking environment variables and walking up the directory
tree. Subcommander apes this as well, allowing your disparate tools to have an
easy way to determine the location of the root directory of the current
context/project/checkout/virtualenv you are working with.

Subcommander attempts to provide a simple convention-based way to encapsulate
these patterns, so you can get your piles of disparate scripts organized. It
intends to be **language agnostic**: all sub-commands and context files may be
implemented in any number of languages. Subcommander itself happens to be
implemented in Python, but this should make no difference to the user. The
author plans to re-implement the same functionality in C.

## Install

Clone this repository somewhere on your system.

## Example Configuration

Let's pretend that you have a collection of scripts in your `~/bin` directory
that you use while working on your project: `proj_runserver`, `proj_db_start`,
`proj_db_stop`, and `proj_deploy`. Let's use subcommander to clean this up a
bit, and create a single tool named `proj`.

1. Create a symlink to (or a copy of) the subcommander.sh script in ~/bin named
   `proj`.

        $ ln -s /path/to/lib/subcommander.sh ~/bin/proj

2. At this point, running `proj` will already produce useful information:

        $ proj
        Subcommands directory ~/usr/lib/proj not found. Specify the path to
        proj subcommands with the PROJ_EXEC_PATH environment variable.

3. So, do what it recommends. Create the directory `~/usr/lib/proj` to hold all
   the sub-scripts:

        $ mkdir -p ~/usr/lib/proj

4. You should now have:

        ~
        ├── bin/
        │   └── proj -> /path/to/lib/subcommander.sh
        └── usr/
            └── lib/
                └── proj/

5. `help` is a subcommand included with subcommander that you will probably
   want as well. Place a symlink (or copy) of it in your scripts directory.

        $ ln -s /path/to/lib/subcommander/help ~/usr/lib/proj/

4. You should now have:

        ~
        ├── bin/
        │   └── proj -> /path/to/lib/subcommander.sh
        └── usr/
            └── lib/
                └── proj/
                    └── help -> /path/to/lib/subcommander/help

4. Now, running `proj` produces:

        $ proj
        usage: proj COMMAND [OPTION...] [ARG]...

        Available proj commands are:
           help                 Lists the available sub-commands (this text)

        No COMMAND specified.

Pretty good for two symlinks and a couple directories, eh?

5. Let's move your scripts into that scripts directory. Since we have a nice
   namespace, we can make their names a bit less verbose.

        $ mv ~/bin/proj_db_start ~/usr/lib/proj/db_start
        $ mv ~/bin/proj_db_stop ~/usr/lib/proj/db_stop
        $ mv ~/bin/proj_deploy ~/usr/lib/proj/deploy
        $ mv ~/bin/proj_runserver ~/usr/lib/proj/runserver

        $ tree
        ~
        ├── bin/
        │   └── proj -> /path/to/lib/subcommander.sh
        └── usr/
            └── lib/
                └── proj/
                    ├── db_start
                    ├── db_stop
                    ├── deploy
                    ├── help -> /path/to/lib/subcommander/help
                    └── runserver

        $ proj
        usage: proj COMMAND [OPTION...] [ARG]...

        Available proj commands are:
           db_start
           db_stop
           deploy
           help                 Lists the available sub-commands (this text)
           runserver

        No COMMAND specified.

        $ proj db_start
        Starting the database...

### Sub-sub-commands

The steps above are sufficient for most, but we need not stop there. In the
example above, we have two commands `db_start` and `db_stop` that are
database-specific: we can further organize them into their own namespace so
that we can call them with `proj db start` and `proj db stop` respectively.

        $ mkdir -p ~/usr/lib/proj/db
        $ mv ~/usr/lib/proj/db_start ~/usr/lib/proj/db/start
        $ mv ~/usr/lib/proj/db_stop ~/usr/lib/proj/db/stop

        $ tree
        ~
        ├── bin/
        │   └── proj -> /path/to/lib/subcommander.sh
        └── usr/
            └── lib/
                └── proj/
                    ├── db/
                    │   ├── start
                    │   └── stop
                    ├── deploy
                    ├── help -> /path/to/lib/subcommander/help
                    └── runserver

Now the main command list is shorter:

        $ proj
        usage: proj COMMAND [OPTION...] [ARG]...

        Available proj commands are:
           db                   Runs subcommands
           deploy               copies working directory up to server
           help                 Lists the available sub-commands (this text)
           runserver            runs my server on port 8080

        No COMMAND specified.

Running the new `db` command shows _its_ subcommands:

        $ proj db
        usage: proj COMMAND [OPTION...] [ARG]...

        Available proj db commands are:
           start                starts the database
           stop                 stops the database

        No COMMAND specified.

Which can be called like so:

        $ proj db start
        Starting the database...

## Improvements for subcommander-based sub-scripts

### Automatic descriptive text

Subcommander's `help` script has some built-in logic for pulling short
descriptive text out of your scripts for display in the list of available
commands. It's super simple: just add a comment near the top of your script
that begins with "Desc" or "description" followed by a colon or equals, and a
short line of text. Continuing with the examples above, let's add comments like
these to our scripts:

        # Description: runs my server on port 8080

        /* Description: starts the database
        */

        // desc: stops the database

        DESC=copies working directory up to server

The result:

        $ proj help
        Available proj commands are:
           db_start             starts the database
           db_stop              stops the database
           deploy               copies working directory up to server
           help                 Lists the available sub-commands (this text)
           runserver            runs my server on port 8080

### Environment variables available to sub-scripts

**Remember: Subcommander sub-scripts are just normal executables.**

You can implement them in any language, compiled or interpreted.

When executed as a sub-command, the following environment variables will be
available for their use:

* `SC_MAIN`: The basename of the top-level symlink to subcommander. In the
  examples above, this would be "`proj`".

* `SC_NAME`: The full command used to execute the script. When
  `~/usr/lib/proj/db/start` is being executed, this would be "`proj db start`".

* `SC_CONTEXT`: (Optional) The path to the context, if found. The context is
  the closest ancestor directory containing a `.proj.context` file.

To see what variables are set by subcommander when it executes your tool, try
the `info` subcommand included with subcommander.

        $ ln -s /path/to/lib/subcommander/info ~/usr/lib/proj/
        $ proj info

### "I don't like `~/usr/lib/proj`"

A subcommander-based tool named `proj` will default to looking in the directory
`~/usr/lib/proj` for its subcommands. This may be overridden by setting
`PROJ_EXEC_PATH` in the environment.

You can set this into the environment in the traditional way by adding a line
to your `~/.bashrc` file like:

    export PROJ_EXEC_PATH=/path/to/proj_subcommands

After editing, you will need to restart your shell for it to take effect.

Alternatively, you don't need to edit your startup scripts to set this into the
environment. You can employ the `proj` configuration script, `~/.projrc`. See
"Hook Scripts and Environment Variables" below for details.

These names are dependent on what you name your tool. If instead of `proj` you
called your tool `foo`, you would want to put subcommands in `/usr/lib/foo/`, use
`FOO_EXEC_PATH` to override that location, and put `foo`-specific configuration
in `~/.foorc`.

### Automatic context discovery

Subcommander-based tools know what directories they "own", and the `init`
script is included to make the setup of a context easy.

        $ ln -s /path/to/lib/subcommander/init ~/usr/lib/proj/

Now, let's say you're working on a version of your project, with a directory
structure like this:

        devel/branch1/
        ├── module1/
        └── module2/
            └── feature/

Within devel/branch1, `proj init` produces:

        devel/branch1/
        ├── module1/
        ├── module2/
        │   └── feature/
        └── .proj.context

Then, from anywhere within `devel/branch1`, running any `proj` command would
invoke it as before, but with the `SC_CONTEXT` environment variable set to
`devel/branch1`.

### Hook scripts and environment variables

If you would like to call hook scripts or set variables into the environment
every time you use `proj`, create an executable script named `~/.projrc`.

If you want to call hook scripts or set variables specific to your project, add
those commands to the context file `.proj.context` in the root of your proj
context.

The context file and rc file is by default an _executable shell script_. You
can replace it with any executable, written in any language, as long as you
follow its convention of executing (with `exec()`) its argument list. Here's a
context file that sets one environment variable:

    #!/bin/sh
    export FOO_PATH="/tmp/foo"
    exec "$@"

Here it is again, in Python:

    #!/usr/bin/python
    import os
    os.environ['FOO_PATH'] = '/tmp/foo'
    os.execv(*sys.argv[1:])

It doesn't even need to be a script. Here it is again, as a C program you can
compile and use as a context file. (Though I can't imagine why anybody would do
this.)

    #include <stdio.h>
    int main(int argc, char *argv[])
    {
        setenv("FOO_PATH", "/tmp/foo", 1);
        return execvp(argv[1], &(argv[1]));
    }

Now, whenever a subcommand is executed by `proj`, the environment variable
`FOO_PATH` will be set to `/tmp/foo`.

**Remember: Subcommander configuration files are just normal executables that
exec() their arguments.**

These names are dependent on what you name your tool. If instead of `proj` you
called your tool `foo`, your context files would be named `.foo.context`, and
your rc file would be named `~/.foorc`.

### Integration with virtualenv

I dislike the way virtualenv's `bin/activate` works; I prefer a system level
tool that launches a subshell. Such a method is described here: [Virtualenv's
bin/activate is Doing It Wrong](https://gist.github.com/2199506). You can
enable it for use with a subcommand script like this, which I call `inve`, for
"in the virtualenv":

        #!/bin/sh
        export VIRTUAL_ENV="$SC_CONTEXT"
        export PATH="$SC_CONTEXT/bin:$PATH"
        unset PYTHON_HOME
        exec "${@-:$SHELL}"

If you have already done `proj init` in the root of your virtualenv environment:

- `proj inve python` will run python as if it were being run after sourcing
  `bin/activate`.
- To simulate `bin/activate` try `proj inve`. Where you would normally use
  `deactivate`, just type CTRL+D or `exit`.
- Now `pip` behaves as you would expect. `pip` installs to your system or
  user-level environment unless you call it like `proj inve pip`.

## Other tools like this one

There are many tools that accomplish something similar. This is my defense
against accusations of [NIH Syndrome][]. Here is a comparison of similar tools
I have found, and the reason why I created this instead of using them.

* [https://github.com/37signals/sub](37signals/sub): This tool adopts many of the same principles as Subcommander, such as language-agnosticism. I discovered it months after I had written Subcommander. You might consider it if you prefer its architecture.

Others:

* [Wayne E. Seguin's BDSM](https://bdsm.beginrescueend.com/): Too complex, no context discovery(?), nsfw docs make my eyes bleed.
* [anandology/subcommand](https://github.com/anandology/subcommand): Requires commands to be implemented in Python.
* [jds/clik](https://github.com/jds/clik): Requires commands to be implemented in Python.
* [rkumar/subcommand](https://github.com/rkumar/subcommand): Requires commands to be implemented in Ruby.
* [reinh/commandant](https://github.com/reinh/commandant): Requires commands to be implemented in Ruby.
* [ander/subcommand](https://github.com/ander/subcommand): Requires commands to be implemented in Ruby.
* [tsantos/subcommander](https://github.com/tsantos/subcommander): Requires commands to be implemented in Ruby.
* [msassak/kerplutz](https://github.com/msassak/kerplutz): I can't really figure it out but I think it's Ruby-only.
* [fabric/fabric](https://github.com/fabric/fabric): Subcommands are implemented in Python. Strange command-line interface to support running commands on multiple remote hosts at once. Treats local host as remote host.
* [anandology/subcommand](https://github.com/anandology/subcommand): Requires subcommands to be implmented in Python.

It may be simple to create a small launcher for scripts in other languages, but
that means every time you add, move, or rename a script you'd have to touch
some main file. Subcommander is entirely configured by the existence of a
script at a particular place in the filesystem.

[NIH Syndrome]: http://en.wikipedia.org/wiki/Not_Invented_Here

## To Do:

- I built a much more robust and featureful `inve` at work, that checks that
  you are within a virtualenv environment, provides docs and friendly error
  messages, etc. Get permission to release it here, or re-write.
- Explore building unit tests for subcommander and subcommander-based tools
  using `chroot`. I would love some way to automatically verify whether or not
  all code paths in all of these scripts work perfectly on various unices--
  Ubuntu, Debian, OS X, Arch, Red Hat.
- Employ another way to get descriptive text; we won't be able to parse
  binaries for 'Description:' lines.

## License

[AGPLv3](http://www.gnu.org/licenses/agpl.html). If you need something more
corporate-friendly, contact me and I'll consider it.
