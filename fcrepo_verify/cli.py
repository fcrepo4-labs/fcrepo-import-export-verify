import click
from csv import DictWriter
import logging
from datetime import datetime
from rdflib.compare import isomorphic
from fcrepo_verify.verify import Config, FcrepoWalker, LocalWalker, \
    FedoraResource, LocalResource, sys, EXT_BINARY_EXTERNAL


class CredentialsParamType(click.ParamType):
    '''A custom credentials parameter type that produces a
    tuple(username, password) from a username:password formatted string.'''

    name = 'credentials'

    def convert(self, value, param, ctx):
        try:
            auth = tuple(value.split(":"))
            if len(auth) == 2:
                return auth
            else:
                raise ValueError
        except ValueError:
            self.fail('Credentials must be given in the form user:password.',
                      param, ctx)

# ============================================================================
# Main function
# ============================================================================


@click.command()
@click.option('--csv', '-c', help='Path to CSV file (to store summary data).',
              default='verify_summary.txt')
@click.option('--user', '-u',
              help='Repository credentials in the form of username:password',
              type=CredentialsParamType(), default=None)
@click.option('--log', '-l',
              help='Path to log file (to store details of verification run).',
              default='verify_output.txt')
@click.option('--loglevel', '-g',
              help='Level of information to output (INFO, WARN, DEBUG, ERROR)',
              default='INFO')
@click.option('--verbose', '-v',
              help='Show detailed info for each resource checked',
              is_flag=True, default=False)
@click.argument('configfile', type=click.Path(exists=True), required=True)
def main(configfile, csv, user, log, loglevel, verbose):
    """This utility compares two sets of Fedora resources
       (in live Fedora server or serialized to disk) and verify their sameness
       using CONFIGFILE (i.e. path to an import/export config file)."""
    # click.echo('success!')

    # Set up csv file, if specified
    if csv:
        csvfile = open(csv, "w")
        fieldnames = ["number", "type", "original", "destination", "verified",
                      "verification"]
        writer = DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    # set up logging to a file
    logger = logging.getLogger("output")
    level = getattr(logging, loglevel.upper(), None)
    logger.setLevel(level)
    fh = logging.FileHandler(filename=log, mode="w")
    fh.setLevel(level)
    logger.addHandler(fh)

    logger.info("\nStarting verification: {}".format(datetime.now()))
    # Create configuration object and setup import/export iterators
    config = Config(configfile, user, logger)
    if config.mode == "export":
        tree = FcrepoWalker(config, logger)
    elif config.mode == "import":
        tree = LocalWalker(config, logger)

    logger.info("\nRunning verification on Fedora 4 {0}".format(config.mode))
    print("\nRunning verification on Fedora 4 {0}".format(config.mode))

    counter = 0

    # Step through the tree and verify resources
    for filepath in tree:
        # iterator can return None, in which case skip
        if filepath is not None:
            counter += 1
            if filepath.startswith(config.repo):
                original = FedoraResource(filepath, config, logger)
            elif filepath.startswith(config.dir):
                original = LocalResource(filepath, config, logger)
            else:
                logger.warn("Resource not in path specified in config file.")
                sys.exit(1)

            # skip binaries and fcr:metadata if no binaries exported
            if not config.bin:
                if original.type == "binary" or \
                        original.origpath.endswith("/fcr:metadata"):
                    continue

            try:
                if filepath.startswith(config.repo):
                    destination = LocalResource(
                        original.destpath, config, logger
                        )
                elif filepath.startswith(config.dir):
                    destination = FedoraResource(
                        original.destpath, config, logger
                        )
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
                        verification = "{0} triples".format(
                            len(original.graph)
                            )
                    else:
                        verified = False
                        verification = ("{0}+{1} triples - mismatch".format(
                                            len(original.graph),
                                            len(destination.graph)
                                            ))
            except FileNotFoundError:
                verified = False
                verification = "destination file not found"

            # always tell user if something doesn't match
            if not verified:
                print("\nWARN: Resource Mismatch \"{}\"".format(
                    original.relpath))

            # If verbose flag is set, print full resource details to
            # screen/file
            if verbose:
                print("\nRESOURCE {0}: {1} {2}".format(
                      counter, original.location, original.type
                      ))
                print("  rel  => {}".format(original.relpath))
                print("  orig => {}".format(original.origpath))
                print("  dest => {}".format(original.destpath))
                print("  Verifying original to copy... {0} -- {1}".format(
                    verified, verification
                    ))
            else:
                # Display a simple counter
                print("Checked {0} resources...".format(counter), end="\r")

            if not verified:
                logger.warn("\nWARN: Resource Mismatch \"{}\"".format(
                    original.relpath))
                logger.info("RESOURCE {0}: {1} {2}".format(
                      counter, original.location, original.type
                      ))

                logger.info("  rel  => {}".format(original.relpath))
                logger.info("  orig => {}".format(original.origpath))
                logger.info("  dest => {}".format(original.destpath))
                logger.info(
                        "  Verifying original to copy... {0} -- {1}"
                        .format(verified, verification))

            # If a CSV summary file has been specified, write results there
            if csv:
                row = {"number":       str(counter),
                       "type":         original.type,
                       "original":     original.origpath,
                       "destination":  original.destpath,
                       "verified":     str(verified),
                       "verification": verification}
                writer.writerow(row)

    # Clear the resource counter display
    print("")
    logger.info("Verified {} resources".format(counter))

    if csv:
        csvfile.close()
