from conduit.apps.core.utils import DEFAULT_CHAR_STRING, generate_random_string


def test_generate_random_string_default_length():
    assert len(generate_random_string()) == 6


def test_generate_random_string_custom_length():
    assert len(generate_random_string(size=20)) == 20


def test_generate_random_string_uses_default_charset():
    result = generate_random_string(size=500)
    assert all(char in DEFAULT_CHAR_STRING for char in result)


def test_generate_random_string_respects_custom_charset():
    result = generate_random_string(chars='x', size=10)
    assert result == 'x' * 10


def test_generate_random_string_zero_size():
    assert generate_random_string(size=0) == ''
