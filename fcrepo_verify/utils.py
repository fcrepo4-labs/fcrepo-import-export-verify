from .constants import LDP_CONTAINS, LDP_NON_RDF_SOURCE
from rdflib import Graph, URIRef
import requests
import sys

try:
    from os import scandir
except ImportError:
    from scandir import scandir


def get_child_nodes(node, predicates, auth, logger):
    """Get the children based on specified containment predicates."""
    # set up containment predicates as specified
    if 'predicates' is not None:
        containment_predicates = predicates
    else:
        containment_predicates = [LDP_CONTAINS]
    # check the resource
    head = requests.head(url=node, auth=auth)
    if head.status_code in [200, 307]:
        # check if resource is binary and if so return metadata node
        if head.links["type"]["url"] == LDP_NON_RDF_SOURCE:
            metadata = [node + "/fcr:metadata"]
            return metadata
        else:
            # get the node's graph
            response = requests.get(url=node, auth=auth)
            graph = Graph().parse(data=response.text, format="text/turtle")
            children = []
            # get all the objects of containment triples
            for cp in containment_predicates:
                predicate = URIRef(cp)
                children.extend(
                    [str(obj) for obj in graph.objects(subject=None,
                                                       predicate=predicate)]
                    )
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
