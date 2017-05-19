import click
import logging
from fcrepo_verify.model import Config
from fcrepo_verify.loggers import createLoggers
from fcrepo_verify.verifier import FedoraImportExportVerifier


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

    level = getattr(logging, loglevel.upper(), None)
    loggers = createLoggers(level, log)
    # Create configuration object and setup import/export iterators
    config = Config(configfile, user, loggers, csv, verbose)
    # Create and execute verifier logic
    verifier = FedoraImportExportVerifier(config, loggers)
    verifier.execute()
