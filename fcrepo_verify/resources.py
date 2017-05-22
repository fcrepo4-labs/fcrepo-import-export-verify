from __future__ import print_function
from hashlib import sha1
from rdflib import Graph
from re import search
import requests
from urllib.parse import urlparse, quote

from fcrepo_verify.constants import EXT_BINARY_INTERNAL, \
    EXT_BINARY_EXTERNAL, LDP_NON_RDF_SOURCE


class Resource(object):
    """Common properties of any resource."""
    def __init__(self, inputpath, config, logger):
        self.config = config
        self.origpath = inputpath
        self.logger = logger


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
