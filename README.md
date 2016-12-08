# fcrepo-import-export-verify
Compare two sets of Fedora resources (in live fcrepo or serialized to disk) and verify
their sameness.

This tool is used to test an import or export from/to a [Fedora](http://github.com/fcrepo4/fcrepo4) server.
To learn how to export or import data from/to a Fedora system, please visit
the [Fedora Import Export Utility](http://github.com/fcrepo4-labs/fcrepo-import-export).

## Installation
This tool requires Python. To install it with its dependencies, navigate to the location on
your local system where you wish to install it and do:
```
$ git clone http://github.com/fcrepo4-labs/fcrepo-import-export-verify
$ cd fcrepo-import-export-verify
$ pip3 install -r requirements.txt
```
Note: 'pip3' is the required command for the installation of dependencies in a local
Python3 environment (the recommended interpreter); to install dependencies for use
with Python2 instead, simply use the equivalent command with 'pip'.

## Usage
The simplest scenario is to run the script with a single argument pointing to the
location of the import/export configuration file. If, when running the import/export
tool, you did not supply a configuration file, the import/export tool should have
created one in a temporary location that is displayed in the tool's screen output
near the beginning of its run.

This same configuration file is used by the verification tool to set up the verification
process, and is the only required argument. Optional additional arguments for the tool are
described below.

### Logging
Information about errors or discrepancies found will be output to the log file and to the
screen.  To have the tool output information about each resource being examined include the `-v` flag.
Information about each resource being looked at will then be sent to standard out.

The default log level for the log file is `INFO` and the default log file is `./verify_output.txt`

A CSV file can be created.  It will contain information about each resource and how it compared
to it's counterpart in the other system.

```
usage: verify.py [-h] [-u USER] [-c CSV] [-l LOG] [--loglevel LOGLEVEL] [-v]
                 configfile

Compare two sets of Fedora resources (in live Fedora server or serialized to
disk) and verify their sameness.

positional arguments:
  configfile            Path to an import/export config file.

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  Repository credentials in the form username:password.
  -c CSV, --csv CSV     Path to CSV file (to store summary data).
  -l LOG, --log LOG     Path to log file (to store details of verification
                        run).
  --loglevel LOGLEVEL   Level of information to output (INFO, WARN, DEBUG,
                        ERROR)
  -v, --verbose         Show detailed info for each resource checked
```
