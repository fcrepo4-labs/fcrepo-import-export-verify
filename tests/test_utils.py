from fcrepo_verify.utils import get_data_dir, replace_strings_in_file
from fcrepo_verify.constants import BAG_DATA_DIR
import os
import tempfile


class MockConfig(dict):
    pass


config = MockConfig({})
config.dir = "/tmp"


def test_get_data_dir():
    config.bag = False
    data_dir = get_data_dir(config)
    assert data_dir == "/tmp"


def test_get_data_dir_for_bag():
    config.bag = True
    data_dir = get_data_dir(config)
    assert data_dir == "/tmp" + BAG_DATA_DIR


def test_replace_strings_in_file():
    tmp = tempfile.mkstemp()
    filename = tmp[1]
    with open(filename, "w") as source:
        source.write("test y\n")
        source.write("test z")
    newfile = replace_strings_in_file(filename, "test", "confirm")
    os.remove(filename)
    with open(newfile, "r") as dest:
        assert dest.readline().startswith("confirm y")
        assert dest.readline() == "confirm z"
    os.remove(newfile)
