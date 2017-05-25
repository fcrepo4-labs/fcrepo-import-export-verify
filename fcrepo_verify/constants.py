__author__ = 'dbernstein'

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
BAG_DATA_DIR = "/data"
