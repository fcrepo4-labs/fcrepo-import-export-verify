from .constants import LDP_CONTAINS, LDP_NON_RDF_SOURCE
from rdflib import Graph, URIRef
import requests
import sys

try:
    from os import scandir
except ImportError:
    from scandir import scandir


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


def get_data_dir(config):
    """Returns the root directory containing serialized fedora objects
    based on the configuration."""
    return config.dir if not config.bag else config.dir + "/data"
