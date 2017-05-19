__author__ = 'danny'

import sys
from urllib.parse import urlparse
from fcrepo_verify.constants import EXT_MAP
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# ============================================================================
# CONFIGURATION CLASS
# ============================================================================


class Config():
    """Object representing the options from import/export config and
       command-line arguments."""
    def __init__(self, configfile, auth, loggers, csv, verbose):
        console = loggers.console
        console.info("\nLoading configuration options from config file:")
        console.info("  '{0}'".format(configfile))
        self.auth = auth
        self.csv = csv
        self.verbose = verbose

        with open(configfile, "r") as f:
            yaml_data = f.read()

        opts = load(yaml_data, Loader=Loader)

        # initialize binaries option (will be overidden below if in config)
        self.bin = False
        # interpret the options in the stored config file
        for key, value in opts.items():
            print("key (" + str(key) + ") and (" + str(value) + ")")
            if key == "mode":
                self.mode = value
            elif key == "resource":
                self.repo = value
            elif key == "dir":
                self.dir = value
            elif key == "binaries":
                self.bin = value
            elif key == "rdfLang":
                self.lang = value

        # if lang not specified in config, set the ext & lang to turtle
        if not hasattr(self, "lang"):
            self.ext = ".ttl"
            self.lang = "text/turtle"
        # set the ext based on the rdfLang
        else:
            if self.lang in EXT_MAP:
                self.ext = EXT_MAP[self.lang]
            else:
                loggers.console.error(
                    "Unrecognized RDF serialization specified in config file!")
                sys.exit(1)

        # split the repository URI into base and path components
        self.repopath = urlparse(self.repo).path
        self.repobase = self.repo[:-len(self.repopath)]
