import pytest

from conduit.apps.articles.serializers import ArticleSerializer, CommentSerializer


@pytest.mark.django_db
class TestArticleSerializerValidation:
    def test_valid_payload_is_valid(self):
        serializer = ArticleSerializer(data={
            'title': 'A Valid Title',
            'description': 'A description',
            'body': 'Some body text',
        })
        assert serializer.is_valid() is True

    def test_missing_title_is_invalid(self):
        serializer = ArticleSerializer(data={
            'description': 'A description',
            'body': 'Some body text',
        })
        assert serializer.is_valid() is False
        assert 'title' in serializer.errors

    def test_missing_body_is_invalid(self):
        serializer = ArticleSerializer(data={
            'title': 'A Valid Title',
            'description': 'A description',
        })
        assert serializer.is_valid() is False
        assert 'body' in serializer.errors

    def test_description_is_optional(self):
        serializer = ArticleSerializer(data={
            'title': 'A Valid Title',
            'body': 'Some body text',
        })
        assert serializer.is_valid() is True

    def test_slug_is_optional(self):
        # Slug is populated by a pre_save signal
        # (conduit/apps/articles/signals.py) when absent, not required on
        # input.
        serializer = ArticleSerializer(data={
            'title': 'A Valid Title',
            'body': 'Some body text',
        })
        assert serializer.is_valid() is True
        assert 'slug' not in serializer.validated_data

    def test_author_is_read_only_and_not_settable_via_input(self):
        serializer = ArticleSerializer(data={
            'title': 'A Valid Title',
            'body': 'Some body text',
            'author': {'username': 'someone-else'},
        })
        assert serializer.is_valid() is True
        assert 'author' not in serializer.validated_data


@pytest.mark.django_db
class TestCommentSerializerValidation:
    def test_valid_payload_is_valid(self):
        serializer = CommentSerializer(data={'body': 'A comment'})
        assert serializer.is_valid() is True

    def test_missing_body_is_invalid(self):
        serializer = CommentSerializer(data={})
        assert serializer.is_valid() is False
        assert 'body' in serializer.errors
