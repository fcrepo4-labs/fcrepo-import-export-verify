# fcrepo-import-export-verify
Compare two sets of Fedora resources (in live fcrepo or serialized to disk) and verify their sameness.

## Installation
To install script and dependencies, navigate to the location on your local system where you wish to install and do:
```
$ git clone http://github.com/fcrepo4-labs/fcrepo-import-export-verify
$ cd fcrepo-import-export-verify
$ pip3 install -r requirements.txt
```
Note: pip3 is recommended for use of the script with Python3, to install dependencies for Python2, use the 'pip' command.

## Usage

```
Usage: verify.py [-h] [-u USER] [-c CSV] [-l LOG] [-v] configfile

Compare two sets of Fedora resources, either in fcrepo or serialized on disk.

positional arguments:
  configfile            Path to import/export config file.

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  Repository credentials in the form username:password.
  -c CSV, --csv CSV     Path to file to store summary csv data.
  -l LOG, --log LOG     Path to log file.
  -v, --verbose         Show details of each resource checked on screen.
```
