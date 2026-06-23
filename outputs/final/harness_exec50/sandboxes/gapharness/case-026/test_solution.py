from solution import env_flag


def test_env_flag_false_string():
    assert env_flag('false') is False
    assert env_flag('yes') is True
