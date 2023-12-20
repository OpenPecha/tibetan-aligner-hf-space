from tm import get_next_version


def test_get_next_version():
    next_version = get_next_version("TM0731")
    assert next_version == "v2"
