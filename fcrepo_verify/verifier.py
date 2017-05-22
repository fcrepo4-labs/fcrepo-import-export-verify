from csv import DictWriter
import sys
import time
import threading
from rdflib.compare import isomorphic

from fcrepo_verify.constants import EXT_BINARY_EXTERNAL
from fcrepo_verify.iterators import FcrepoWalker, LocalWalker
from fcrepo_verify.resources import FedoraResource, LocalResource


class FedoraImportExportVerifier:
    """Contains logic for performing a verification."""
    def __init__(self, config, loggers):
        self.config = config
        self.loggers = loggers

    def execute(self):
        """Executes the verification process."""
        config = self.config
        csv = self.config.csv

        loggers = self.loggers
        logger = loggers.file_only
        console = loggers.console
        console_only = loggers.console_only

        # Set up csv file, if specified
        if csv:
            csvfile = open(csv, "w")
            fieldnames = ["number", "type", "original", "destination",
                          "verified",
                          "verification"]
            writer = DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        console.info("Starting verification...")
        if config.mode == "export":
            tree = FcrepoWalker(config, logger)
        elif config.mode == "import":
            tree = LocalWalker(config, logger)

        console.info(
            "Running verification on Fedora 4 {0}".format(config.mode)
            )

        success_count = 0
        failure_count = 0

        def total_count():
            return success_count + failure_count

        def log_summary(logger):
            logger.info(
                "Verified {} resources: successes = {}, failures = {}".format(
                    total_count(), success_count, failure_count)
                    )

        def count_logger():
            while(True):
                time.sleep(10)
                log_summary(console_only)

        t = threading.Thread(target=count_logger)
        t.daemon = True
        t.start()

        # Step through the tree and verify resources
        for filepath in tree:
            # iterator can return None, in which case skip
            if filepath is not None:

                if filepath.startswith(config.repo):
                    original = FedoraResource(filepath, config, logger)
                elif filepath.startswith(config.dir):
                    original = LocalResource(filepath, config, logger)
                else:
                    logger.warn(
                        "Resource not in path specified in config file."
                        )
                    sys.exit(1)

                # skip binaries and fcr:metadata if no binaries exported
                if not config.bin:
                    if original.type == "binary" or \
                            original.origpath.endswith("/fcr:metadata"):
                        continue

                if filepath.startswith(config.repo):
                    destination = LocalResource(original.destpath,
                                                config,
                                                loggers.file_only)
                elif filepath.startswith(config.dir):
                    destination = FedoraResource(original.destpath,
                                                 config,
                                                 loggers.file_only)

                if original.type == "binary":
                    if destination.origpath.endswith(EXT_BINARY_EXTERNAL):
                        verified = False
                        verification = "external resource"
                    if original.sha1 == destination.sha1:
                        verified = True
                        verification = original.sha1
                    else:
                        verified = False
                        verification = "{0} != {1}".format(
                            original.sha1, destination.sha1
                            )

                elif original.type == "rdf":
                    if isomorphic(original.graph, destination.graph):
                        verified = True
                        verification = \
                            "{0} triples".format(len(original.graph))
                    else:
                        verified = False
                        verification = ("{0}+{1} triples - mismatch".format(
                                            len(original.graph),
                                            len(destination.graph)
                                            ))

                logger.info(
                    "RESOURCE {0}: {1} {2}".format(
                        total_count(), original.location, original.type)
                        )

                if not verified:
                    logger.warn(
                        "Resource Mismatch \"{}\"".format(original.relpath)
                        )
                    failure_count += 1
                else:
                    success_count += 1

                if config.verbose:
                    logger.info("  rel  => {}".format(original.relpath))
                    logger.info("  orig => {}".format(original.origpath))
                    logger.info("  dest => {}".format(original.destpath))
                    logger.info(
                        "  Verifying original to copy... {0} -- {1}".format(
                            verified, verification)
                            )

                # write csv if exists
                if csv:
                    row = {"number":       str(total_count()),
                           "type":         original.type,
                           "original":     original.origpath,
                           "destination":  original.destpath,
                           "verified":     str(verified),
                           "verification": verification}
                    writer.writerow(row)

        log_summary(console)
        console.info("Verification complete")

        if csv:
            csvfile.close()
