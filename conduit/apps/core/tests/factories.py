"""
Shared factory_boy factories used across all apps' test suites. Lives under
`core` since it's the one app every other app already depends on.
"""
import factory
from factory.django import DjangoModelFactory

from conduit.apps.articles.models import Article, Comment, Tag
from conduit.apps.authentication.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.Sequence(lambda n: 'user%d@example.com' % n)
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ('slug',)

    tag = factory.Sequence(lambda n: 'tag%d' % n)
    slug = factory.LazyAttribute(lambda o: o.tag.lower())


class ArticleFactory(DjangoModelFactory):
    class Meta:
        model = Article

    slug = factory.Sequence(lambda n: 'article-%d' % n)
    title = factory.Sequence(lambda n: 'Article %d' % n)
    description = 'Test description'
    body = 'Test body'
    # `Profile` is created automatically via a post_save signal on `User`
    # (conduit/apps/authentication/signals.py) — a bare UserFactory() call
    # gives us a profile to hang the article off of.
    author = factory.LazyFunction(lambda: UserFactory().profile)


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    body = 'Test comment body'
    article = factory.SubFactory(ArticleFactory)
    author = factory.LazyFunction(lambda: UserFactory().profile)
