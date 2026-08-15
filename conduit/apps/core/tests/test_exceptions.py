import pytest
from rest_framework.exceptions import NotFound, ValidationError

from conduit.apps.articles.models import Article
from conduit.apps.core.exceptions import core_exception_handler


class FakeViewWithQueryset:
    queryset = Article.objects.all()


class FakeViewWithoutQueryset:
    pass


def test_validation_error_is_wrapped_in_errors_key():
    exc = ValidationError('bad data')
    response = core_exception_handler(exc, context={'view': None})

    assert response.data == {'errors': ['bad data']}


def test_not_found_uses_model_verbose_name_as_error_key():
    exc = NotFound('An article with this slug does not exist.')
    response = core_exception_handler(
        exc, context={'view': FakeViewWithQueryset()}
    )

    assert response.data == {
        'errors': {'article': 'An article with this slug does not exist.'}
    }


def test_not_found_without_a_queryset_falls_back_to_generic_wrapping():
    exc = NotFound('nope')
    response = core_exception_handler(
        exc, context={'view': FakeViewWithoutQueryset()}
    )

    assert response.data == {'errors': {'detail': 'nope'}}


def test_not_found_with_no_view_falls_back_to_generic_wrapping():
    exc = NotFound('nope')
    response = core_exception_handler(exc, context={'view': None})

    assert response.data == {'errors': {'detail': 'nope'}}


def test_unhandled_exception_type_passes_through_default_handler():
    # PermissionDenied isn't in `handlers`, so it should come back exactly
    # as DRF's own default exception_handler would produce it.
    from rest_framework.exceptions import PermissionDenied

    exc = PermissionDenied()
    response = core_exception_handler(exc, context={'view': None})

    assert response.data == {'detail': 'You do not have permission to perform this action.'}
