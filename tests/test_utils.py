from fcrepo_verify.utils import get_data_dir
from fcrepo_verify.constants import BAG_DATA_DIR


class MockConfig(dict):
    pass


config = MockConfig({})


def test_get_data_dir():
    config.bag = False
    data_dir = get_data_dir(config)
    assert data_dir == "/tmp"


def test_get_data_dir_for_bag():
    config.dir = "/tmp"
    config.bag = True
    data_dir = get_data_dir(config)
    assert data_dir == "/tmp" + BAG_DATA_DIR
