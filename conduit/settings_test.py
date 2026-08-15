"""
Settings overrides used only when running the test suite (pytest-django,
via DJANGO_SETTINGS_MODULE=conduit.settings_test — see pytest.ini). Isolates
the test run from the dev `db.sqlite3` file and speeds up password hashing,
without touching the app's own settings.py.
"""
from .settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# PBKDF2 (the default) is deliberately slow; MD5 keeps the suite fast
# without changing what's being tested (password *validation* rules, not
# the hashing algorithm itself, are the thing under test).
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
