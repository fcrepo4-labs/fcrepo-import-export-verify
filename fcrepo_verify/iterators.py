from os.path import basename, isfile
from .utils import get_directory_contents, get_child_nodes


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
