#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from hashlib import sha1
import os.path
import rdflib
import rdflib.compare as compare
import re
import requests
import sys
from urllib.parse import urlparse, quote


def is_binary(node, auth):
    '''Using link headers, determine whether a resource is rdf or non-rdf.'''
    response = requests.head(url=node, auth=auth)
    if response.status_code == 200:
        if response.links['type']['url'] == \
            'http://www.w3.org/ns/ldp#NonRDFSource':
            return True
        else:
            return False
    else:
        print("Error communicating with repository.")
        sys.exit(1)


def calculate_sha1(filepath):
    '''Given a file or stream, return the sha1 checksum.'''
    with open(filepath, 'rb') as f:
        sh = sha1()
        while True:
            data = f.read(8192)
            if not data:
                break
            sh.update(data)
    return sh.hexdigest()


def get_child_nodes(node, auth):
    '''Get the children based on LDP containment.'''
    if is_binary(node, auth):
        metadata = [node + "/fcr:metadata"]
        return metadata
    else:
        response = requests.get(node, auth=auth)
        if response.status_code == 200:
            graph = rdflib.Graph()
            graph.parse(data=response.text, format="text/turtle")
            predicate = rdflib.URIRef('http://www.w3.org/ns/ldp#contains')
            children = [str(obj) for obj in graph.objects(
                            subject=None, predicate=predicate
                            )]
            return children
        else:
            print("Error communicating with repository.")
            sys.exit(1)


def get_directory_contents(localpath):
    '''Get the children based on the directory hierarchy.'''
    if os.path.isfile(localpath):
        return None
    else:
        return [p.path for p in os.scandir(localpath)]


class Config():
    '''Object representing the options from import/export config and 
       command-line arguments.'''
    def __init__(self, configfile, auth):
        print("Loading configuration options from import/export config file...")
        self.auth = auth
        with open(configfile, 'r') as f:
            opts = [line for line in f.read().split('\n')]
        
        for line in range(len(opts)):
            if opts[line] == '-m':
                self.mode = opts[line + 1]
            elif opts[line] == '-r':
                self.repo = opts[line + 1]
            elif opts[line] == '-d':
                self.desc = opts[line + 1]
            elif opts[line] == '-b':
                self.bin = opts[line + 1]
            elif opts[line] == '-x':
                self.ext = opts[line + 1]
            elif opts[line] == '-l':
                self.lang = opts[line + 1]
                
        # if not specified in config, set default ext & lang to turtle
        if not hasattr(self, 'ext'):
            self.ext = '.ttl'
        if not hasattr(self, 'lang'):
            self.lang = 'text/turtle'
        
        self.repopath = urlparse(self.repo).path
        self.repobase = self.repo[:-len(self.repopath)]
        


class Walker:
    '''Walk a set of Fedora resources.'''
    def __init__(self, root):
        self.to_check = [root]
      
    def __iter__(self):
        return self


class FcrepoWalker(Walker):
    '''Walk resources in a live repository.'''
    def __init__(self, root, auth):
        Walker.__init__(self, root)
        self.auth = auth
    
    def __next__(self):
        if not self.to_check:
            raise StopIteration()
        else:
            current = self.to_check.pop()
            children = get_child_nodes(current, self.auth)
            if children:
                self.to_check.extend(children)
            return current


class LocalWalker(Walker):
    '''Walk serialized resources on disk.'''
    def __init__(self, root):
        Walker.__init__(self, root)
        
    def __next__(self):
        if not self.to_check:
            raise StopIteration()
        else:
            current = self.to_check.pop()
            if os.path.basename(current).startswith('.'):
                return None
            else:
                children = get_directory_contents(current)
                if children:
                    self.to_check.extend(children)
                    return None
                else:
                    return current


class Resource():
    '''Object representing any resource, either local or in fcrepo.'''
    def __init__(self, inputpath, config):
    
        self.origpath = inputpath
        
        if self.origpath.startswith(config.repo):
            self.location = 'fcrepo'
            self.relpath = urlparse(self.origpath).path
            
            if is_binary(self.origpath, config.auth):
                self.type = 'binary'
                self.metadata = self.origpath + '/fcr:metadata'
                self.destpath = quote((config.bin + self.relpath + '.binary'))
                response = requests.get(self.metadata, auth=config.auth)
                self.filename = re.search(
                    r'ebucore:filename \"(.+?)\"', response.text
                    ).group(1)
                self.sha1 = re.search(
                    r'premis:hasMessageDigest <urn:sha1:(.+?)>', response.text
                    ).group(1)
            else:
                self.type = 'rdf'
                self.destpath = quote((config.desc + self.relpath + config.ext))
                self.graph = rdflib.Graph().parse(self.origpath)
        
        elif self.origpath.startswith(config.bin):
            self.location = 'local'
            self.type = 'binary'
            self.relpath = self.origpath[len(config.bin):]
            if not self.relpath.endswith('.binary'):
                print('ERROR: Binary resource lacks expected extension!')
            self.destpath = config.repobase + self.relpath[:-len('.binary')]
            self.sha1 = calculate_sha1(self.origpath)
            
        elif self.origpath.startswith(config.desc):
            self.location = 'local'
            self.type = 'rdf'
            self.relpath = self.origpath[len(config.desc):]
            if not self.relpath.endswith(config.ext):
                print('ERROR: RDF resource lacks expected extension!')
            self.destpath = config.repobase + self.relpath[:-len(config.ext)]
            self.graph = rdflib.Graph().parse(location=self.origpath,
                                              format=config.lang
                                              )
        else:
            print("ERROR reading resource at {0}.".format(self.origpath))


def main():

    def credentials(user):
        '''Custom handling of credentials passed as argument.'''
        auth = tuple(user.split(':'))
        if len(auth) == 2:
            return auth
        else:
            raise argparse.ArgumentTypeError(
                '''Credentials must be given in the form user:password.'''
                )

    parser = argparse.ArgumentParser(
                        description='''Compare two sets of Fedora resources, 
                        either in fcrepo or serialized on disk.'''
                        )
        
    parser.add_argument('-u', '--user',
                        help='''Repository credentials in the form 
                                username:password.''',
                        action='store',
                        type=credentials,
                        required=False,
                        default=None
                        )
    
    parser.add_argument('-l', '--log',
                        help='''Path to file to store output. 
                                Defaults to stdout.''',
                        action='store',
                        required=False,
                        default=None
                        )
    
    parser.add_argument('-v', '--verbose',
                        help='''Show details of each resource checked on 
                                screen.''',
                        action='store_true',
                        required=False,
                        default=False
                        )
                        
    parser.add_argument('configfile',
                        help='''Path to import/export config file.''',
                        action='store'
                        )
                        
    args = parser.parse_args()
    
    
    # Create configuration object and setup import/export iterators
    config = Config(args.configfile, args.user)
    if config.mode == 'export':
        trees = [FcrepoWalker(config.repo, args.user)]
    elif config.mode == 'import':
        trees = [LocalWalker(config.bin), LocalWalker(config.desc)]
        
    # Set up log file, if specified
    if args.log:
        logfile = open(args.log, 'w')
    else:
        logfile = sys.stdout
        
    counter = 1
    
    # Step through each iterator and verify resources
    for walker in trees:
        for filepath in walker:
            if filepath is not None:
                original = Resource(filepath, config)
                destination = Resource(original.destpath, config)
                
                if original.type == 'binary':
                    if original.sha1 == destination.sha1:
                        verified = True
                        verification = original.sha1
                    else:
                        verified = False
                        verification = "{0} != {1}".format(
                            original.sha1, destination.sha1
                            )
                
                elif original.type == 'rdf':
                    if compare.isomorphic(original.graph, destination.graph):
                        verified = True
                        verification = "{0} triples match".format(
                                        len(original.graph)
                                        )
                    else:
                        verified = False
                        verification = ('{0}+{1} triples - mismatch'.format(
                                            len(original.graph),
                                            len(desination.graph)
                                            ))
                
                # If verbose flag is set, print full resource details to screen
                if args.verbose:
                    print("\nRESOURCE {0}: {1} {2}".format(
                          counter, original.location, original.type
                          ))
                    print("  rel  =>", original.relpath)
                    print("  orig =>", original.origpath)
                    print("  dest =>", original.destpath)
                    print("  Verifying original to copy... ", end='')
                    print("{0} -- {1}".format(verified, verification))
                
                # Display a simple counter
                else:
                    print("Checked {0} resources...".format(counter), end='\r')
                
                # Log results to logger report
                logfile.write(','.join([str(counter), original.type,
                                        original.origpath, original.destpath, 
                                        str(verified), verification]
                                        ) + '\n')
                counter += 1
    
    # Clear the resource counter display
    print('')

    if args.log:
        logfile.close()


if __name__ == "__main__":
    main()


