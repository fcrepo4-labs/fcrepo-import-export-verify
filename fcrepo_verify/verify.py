#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

from hashlib import sha1
from os.path import basename, isfile
try:
    from os import scandir
except ImportError:
    from scandir import scandir
from rdflib import Graph, URIRef
from re import search
import requests
import sys
from urllib.parse import urlparse, quote
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

EXT_MAP = {"application/ld+json":   ".json",
           "application/n-triples": ".nt",
           "application/rdf+xml":   ".xml",
           "text/n3":               ".n3",
           "text/rdf+n3":           ".n3",
           "text/plain":            ".txt",
           "text/turtle":           ".ttl",
           "application/x-turtle":  ".ttl"
           }
LDP_NON_RDF_SOURCE = "http://www.w3.org/ns/ldp#NonRDFSource"
LDP_CONTAINS = "http://www.w3.org/ns/ldp#contains"

EXT_BINARY_INTERNAL = ".binary"
EXT_BINARY_EXTERNAL = ".external"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_child_nodes(node, auth, logger):
    """Get the children based on LDP containment."""
    head = requests.head(url=node, auth=auth)
    if head.status_code in [200, 307]:
        if head.links["type"]["url"] == LDP_NON_RDF_SOURCE:
            metadata = [node + "/fcr:metadata"]
            return metadata
        else:
            response = requests.get(url=node, auth=auth)
            graph = Graph().parse(data=response.text, format="text/turtle")
            predicate = URIRef(LDP_CONTAINS)
            children = [str(obj) for obj in graph.objects(
                            subject=None, predicate=predicate
                            )]
            return children
    else:
        logger.error("Error communicating with repository.")
        sys.exit(1)


def get_directory_contents(localpath):
    """Get the children based on the directory hierarchy."""
    return [p.path for p in scandir(localpath)]


# ============================================================================
# CONFIGURATION CLASS
# ============================================================================


class Config():
    """Object representing the options from import/export config and
       command-line arguments."""
    def __init__(self, configfile, auth, logger):
        logger.info("\nLoading configuration options from config file:")
        logger.info("  '{0}'".format(configfile))
        self.auth = auth

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
                logger.error(
                    "Unrecognized RDF serialization specified in config file!")
                print(
                    "Unrecognized RDF serialization specified in config file!")
                sys.exit(1)

        # split the repository URI into base and path components
        self.repopath = urlparse(self.repo).path
        self.repobase = self.repo[:-len(self.repopath)]


# ============================================================================
# ITERATOR CLASSES
# ============================================================================


class Walker:
    """Walk a set of Fedora resources."""
    def __init__(self, root, logger):
        self.to_check = [root]
        self.logger = logger

    def __iter__(self):
        return self


class FcrepoWalker(Walker):
    """Walk resources in a live repository."""
    def __init__(self, config, logger):
        Walker.__init__(self, config.repo, logger)
        self.auth = config.auth

    def __next__(self):
        if not self.to_check:
            raise StopIteration()
        else:
            current = self.to_check.pop()
            children = get_child_nodes(current, self.auth, self.logger)
            if children:
                self.to_check.extend(children)
            return current


class LocalWalker(Walker):
    """Walk serialized resources on disk."""
    def __init__(self, config, logger):
        Walker.__init__(self, config.dir, logger)

    def __next__(self):
        if not self.to_check:
            raise StopIteration()
        else:
            current = self.to_check.pop()
            # ignore hidden directories and files
            if basename(current).startswith("."):
                return None
            elif isfile(current):
                return current
            else:
                children = get_directory_contents(current)
                if children:
                    self.to_check.extend(children)
                return None


# ============================================================================
# MAIN RESOURCE CLASS
# ============================================================================


class Resource(object):
    """Common aspects of any resource, either local or in fcrepo."""
    def __init__(self, inputpath, config, logger):
        self.config = config
        self.origpath = inputpath
        self.logger = logger


# ============================================================================
# FEDORA RESOURCE CLASS
# ============================================================================


class FedoraResource(Resource):
    """Properties and methods for a resource in a Fedora repository."""
    def __init__(self, inputpath, config, logger):
        Resource.__init__(self, inputpath, config, logger)
        self.location = "fedora"
        self.relpath = urlparse(self.origpath).path.rstrip("/")
        self.fetch_headers()
        if self.is_binary():
            self.type = "binary"
            self.metadata = self.origpath + "/fcr:metadata"
            if self.external:
                self.destpath = quote(
                    (self.config.dir + self.relpath + EXT_BINARY_EXTERNAL)
                    )
            else:
                self.destpath = quote(
                    (self.config.dir + self.relpath + EXT_BINARY_INTERNAL)
                    )
            self.lookup_sha1()
        else:
            self.type = "rdf"
            self.destpath = quote(
                (self.config.dir + self.relpath + self.config.ext)
                )
            response = requests.get(self.origpath, auth=self.config.auth)
            if response.status_code == 200:
                self.graph = Graph().parse(
                    data=response.text, format="text/turtle"
                    )

    def fetch_headers(self):
        response = requests.head(url=self.origpath, auth=self.config.auth)
        if response.status_code in [200, 307]:
            self.headers = response.headers
            self.ldp_type = response.links["type"]["url"]
            if response.status_code == 200:
                self.external = False
            elif response.status_code == 307:
                self.external = True
            return True
        else:
            # handle other response codes appropriately here
            return False

    def is_binary(self):
        if self.headers:
            return self.ldp_type == LDP_NON_RDF_SOURCE

    def lookup_sha1(self):
        response = requests.get(self.metadata, auth=self.config.auth)
        if response.status_code == 200:
            m = search(
                r"premis:hasMessageDigest[\s]+<urn:sha1:(.+?)>", response.text
                )
            self.sha1 = m.group(1) if m else ""
            return True


# ============================================================================
# LOCAL RESOURCE CLASS
# ============================================================================


class LocalResource(Resource):
    """Properties and methods for a resource serialized to disk."""
    def __init__(self, inputpath, config, logger):
        Resource.__init__(self, inputpath, config, logger)
        self.location = "local"
        self.relpath = self.origpath[len(config.dir):]
        urlinfo = urlparse(config.repo)
        config_repo = urlinfo.scheme + "://" + urlinfo.netloc
        if self.is_binary():
            self.type = "binary"
            self.external = False
            if self.origpath.endswith(EXT_BINARY_EXTERNAL):
                self.external = True

            if self.external:
                self.destpath = config_repo + \
                        self.relpath[:-len(EXT_BINARY_EXTERNAL)]
            else:
                self.destpath = config_repo + \
                        self.relpath[:-len(EXT_BINARY_INTERNAL)]

            self.sha1 = self.calculate_sha1()
        elif self.origpath.startswith(config.dir) and \
                self.origpath.endswith(config.ext):
            self.type = "rdf"
            self.destpath = config_repo + self.relpath[:-len(config.ext)]
            self.graph = Graph().parse(
                location=self.origpath, format=config.lang
                )
        else:
            msg = "ERROR: RDF resource lacks expected extension!".format(
                    self.origpath)

            print(msg)
            self.logger.error(msg)

    def is_binary(self):
        if self.origpath.endswith(EXT_BINARY_INTERNAL) or \
                self.origpath.endswith(EXT_BINARY_EXTERNAL):
            return True
        else:
            return False

    def calculate_sha1(self):
        with open(self.origpath, "rb") as f:
            sh = sha1()
            while True:
                data = f.read(8192)
                if not data:
                    break
                sh.update(data)
        return sh.hexdigest()
