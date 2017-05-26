# fcrepo-import-export-verify
Verify that sets of resources in a Fedora repository and serialized to disk are
the same.

This tool is used to test an import or export from/to a 
[Fedora](http://github.com/fcrepo4/fcrepo4) server.
To learn how to export or import data from/to a Fedora system, please visit the
[Fedora Import Export 
Utility](http://github.com/fcrepo4-labs/fcrepo-import-export).

## Installation
This tool requires Python 3. It has not been tested with Python 2. To install
it with its dependencies, navigate to the location on your local system where
you wish to install it and do:
```
$ git clone http://github.com/fcrepo4-labs/fcrepo-import-export-verify
$ cd fcrepo-import-export-verify
$ python3 setup.py install
```
This will download all dependencies and install the program on your PATH.

## Usage
The simplest scenario is to run the script with a single argument pointing to 
the location of the import/export configuration file.
```
$ fcrepo-verify CONFIGFILE
```
If, when running the import/export tool, you did not supply a configuration
file, the import/export tool should have created one in a temporary location
that is displayed near the beginning of its console output.

This same configuration file is used by the verification tool to set up the 
verification process, and is the only required argument. Optional additional 
arguments for the tool are described below.

### Running tests
```
$ pytest tests
```

### Logging
Information about errors or discrepancies found will be printed to the console
and logged to a file named with a timestamp. The location of the logs (default 
is the 'logs' directory) can be specified with the `-l/--logdir` parameter. To 
have the tool log detailed information about each resource comparison use the 
`-v/--verbose` flag.

The default log level for the log file is `INFO`. the log level can be 
specified with the `-g/--loglevel` flag.

In addition to the logs, a CSV output file is written to the output directory.  
The location of this output can be specified with the `-o/--output` parameter. 
This file contains information about each resource and how it compared to its 
counterpart in the other location, as well as the reason why a resource and its 
counterpart were determined to be the same, or different in the case of errors 
(via SHA1 checksum for binaries and by graph comparison for RDF resources).

```
Usage: fcrepo-verify [OPTIONS] CONFIGFILE

  Verify that the resources in Fedora and on disk are the same.

  Using a CONFIGFILE (i.e. path to an fcrepo-import-export configuration
  file) this utility compares two sets of Fedora resources, one in a live
  server and the other serialized to disk, and verifies that the two sets
  are the same.

Options:
  -o, --outputdir TEXT    Path to directory for output files such as csv
                          reports of the verification process.
  -u, --user CREDENTIALS  Repository credentials in the form of
                          username:password
  -l, --logdir TEXT       Path to log file (to store details of verification
                          run).
  -g, --loglevel TEXT     Level of information to output (INFO, WARN, DEBUG,
                          ERROR)
  -v, --verbose           Show detailed info for each resource checked
  --help                  Show this message and exit.
```

## Unicode Errors
The verification tool has been observed to generate spurious verification 
errors when comparing Unicode characters in the repository to the equivalent 
Unicode characters in RDF on disk. This issue applies to Fedora 4.6.0, 
and possibly other releases prior to 4.7.2.
