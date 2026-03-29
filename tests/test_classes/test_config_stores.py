# SPDX-License-Identifier: MIT
import pytest
from unittest.mock import Mock

from augur.application.config import JsonConfig, DatabaseConfig, NotWriteableException, AugurConfig, default_config


@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def mock_session():
    return Mock()


def test_jsonconfig_readonly_flags(mock_logger):
    cfg = JsonConfig({"A": {"x": 1}}, mock_logger)
    assert cfg.writable is False
    assert cfg.empty is False


def test_jsonconfig_empty_true_false(mock_logger):
    assert JsonConfig({}, mock_logger).empty is True
    assert JsonConfig({"A": {}}, mock_logger).empty is False


def test_jsonconfig_write_protection(mock_logger):
    # JsonConfig should be not writeable by default, so we should be unable to change
    # its values, even by abusing references
    
    data = {"Alpha": {"a": 1, "b": "str"}, "Beta": {}}
    cfg = JsonConfig(data, mock_logger)

    # mutation via input
    data["Alpha"]["a"] = 2

    config_test = cfg.retrieve_dict() 
    assert config_test != data # the data in the config should not change

    # mutation via output
    config_test["Alpha"]["a"] = 3
    
    config_test = cfg.retrieve_dict() 
    assert config_test != data # the data in the config should not change

def test_jsonconfig_retrieve_has_get(mock_logger):
    data = {"Alpha": {"a": 1, "b": "str"}, "Beta": {}}
    cfg = JsonConfig(data, mock_logger)

    # retrieve full dict
    assert cfg.retrieve_dict() == data

    # has/get section
    assert cfg.has_section("Alpha") is True
    assert cfg.has_section("Missing") is False
    assert cfg.get_section("Alpha") == {"a": 1, "b": "str"}
    assert cfg.get_section("Missing") is None

    # has/get value
    assert cfg.has_value("Alpha", "a") is True
    assert cfg.has_value("Alpha", "missing") is False
    assert cfg.has_value("Missing", "a") is False
    assert cfg.get_value("Alpha", "a") == 1
    assert cfg.get_value("Alpha", "missing") is None
    assert cfg.get_value("Missing", "a") is None


@pytest.mark.parametrize(
    "callable_name, args, kwargs",
    [
        ("load_dict", ({"X": {"y": 2}},), {"ignore_existing": False}),
        ("clear", tuple(), {}),
        ("remove_section", ("X",), {}),
        ("create_section", ("X", {"y": 2}), {"ignore_existing": False}),
        ("remove_value", ("X", "y"), {}),
        ("add_value", ("X", "y", 2), {"ignore_existing": False}),
    ],
)
def test_jsonconfig_mutations_raise_not_writable(mock_logger, callable_name, args, kwargs):
    cfg = JsonConfig({"A": {"x": 1}}, mock_logger)
    with pytest.raises(NotWriteableException):
        getattr(cfg, callable_name)(*args, **kwargs)


def test_dict_to_config_table_happy_path():
    input_dict = {
        "Section1": {"alpha": 1, "beta": "x"},
        "Section2": {"gamma": False, "delta": 3.14},
    }

    rows = DatabaseConfig._dict_to_config_table(input_dict)

    # Expect a list of row dicts with section_name, setting_name, value
    assert isinstance(rows, list)
    expected = [
        { 
            "section_name": "Section1",
            "setting_name": "alpha",
            "value": 1,
            "type": "int"
        },
        { 
            "section_name": "Section1",
            "setting_name": "beta",
            "value": "x",
            "type": "str"
        },
        { 
            "section_name": "Section2",
            "setting_name": "gamma",
            "value": False,
            "type": "bool"
        },
        { 
            "section_name": "Section2",
            "setting_name": "delta",
            "value": 3.14,
            "type": "float"
        },
    ]
    assert rows == expected



def test_fetching_real_defaults(mock_logger, mock_session):
    cfg = AugurConfig(mock_logger, mock_session)
    cfg.config_sources = [JsonConfig(default_config, mock_logger)]

    assert cfg.get_value("Redis", "cache_group") == 0


def test_load_config_utilizes_hierarchy():

    default_dict = {
        "Section1": {"alpha": 1, "beta": "x"},
        "Section2": {"gamma": False, "delta": 3.14},
    }

    override_dict = {
        "Section1": {"beta": "y"},
        "Section2": {"Epsilon": True, "delta": 6.28},
        "Section3": {"hi": "there"}
    }

    cfg = AugurConfig(None, None, [JsonConfig(default_dict, mock_logger), JsonConfig(override_dict, mock_logger)])

    expected_dict = {
        "Section1": {"alpha": 1, "beta": "y"},
        "Section2": {"gamma": False, "Epsilon": True, "delta": 6.28},
        "Section3": {"hi": "there"} # test that new sections are accounted for too
    }

    assert cfg.load_config() == expected_dict


def test_get_section_incorporates_hierarchy():

    default_dict = {
        "Section1": {"alpha": 1, "beta": "x"},
        "Section2": {"gamma": False, "delta": 3.14},
    }

    override_dict = {
        "Section1": {"beta": "y"},
        "Section2": {"gamma": False, "delta": 3.14},
    }

    cfg = AugurConfig(None, None, [JsonConfig(default_dict, mock_logger), JsonConfig(override_dict, mock_logger)])

    expected_dict = {"alpha": 1, "beta": "y"}

    assert cfg.get_section("Section1") == expected_dict

