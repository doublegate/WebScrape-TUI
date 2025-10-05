"""Unit tests for model classes."""

from datetime import datetime

from scrapetui.models import User, Article, ScraperProfile, Tag, Session, Role


class TestUserModel:
    """Test User model."""

    def test_user_creation(self):
        """Test User model creation."""
        user = User(
            id=1,
            username='testuser',
            password_hash='hashed_password',
            email='test@example.com',
            role='user',
            created_at='2025-01-01T00:00:00',
            last_login='2025-01-02T00:00:00',
            is_active=True
        )

        assert user.id == 1
        assert user.username == 'testuser'
        assert user.role == 'user'
        assert user.is_active is True

    def test_user_role_enum(self):
        """Test User role_enum property."""
        admin = User(
            id=1, username='admin', password_hash='hash', email=None,
            role='admin', created_at='2025-01-01T00:00:00',
            last_login=None, is_active=True
        )

        assert admin.role_enum == Role.ADMIN

        user = User(
            id=2, username='user', password_hash='hash', email=None,
            role='user', created_at='2025-01-01T00:00:00',
            last_login=None, is_active=True
        )

        assert user.role_enum == Role.USER

    def test_user_created_datetime(self):
        """Test User created_datetime property."""
        user = User(
            id=1, username='test', password_hash='hash', email=None,
            role='user', created_at='2025-01-01T12:00:00',
            last_login=None, is_active=True
        )

        created = user.created_datetime
        assert isinstance(created, datetime)
        assert created.year == 2025
        assert created.month == 1

    def test_user_last_login_datetime(self):
        """Test User last_login_datetime property."""
        user = User(
            id=1, username='test', password_hash='hash', email=None,
            role='user', created_at='2025-01-01T00:00:00',
            last_login='2025-01-02T12:00:00', is_active=True
        )

        last_login = user.last_login_datetime
        assert isinstance(last_login, datetime)
        assert last_login.day == 2

    def test_user_last_login_none(self):
        """Test User last_login_datetime when None."""
        user = User(
            id=1, username='test', password_hash='hash', email=None,
            role='user', created_at='2025-01-01T00:00:00',
            last_login=None, is_active=True
        )

        assert user.last_login_datetime is None

    def test_user_to_dict(self):
        """Test User to_dict method (excludes password_hash)."""
        user = User(
            id=1, username='test', password_hash='secret_hash', email='test@example.com',
            role='user', created_at='2025-01-01T00:00:00',
            last_login=None, is_active=True
        )

        user_dict = user.to_dict()
        assert 'password_hash' not in user_dict
        assert user_dict['username'] == 'test'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['id'] == 1

    def test_user_from_db_row(self):
        """Test User.from_db_row factory method."""
        row = {
            'id': 1,
            'username': 'test',
            'password_hash': 'hash',
            'email': 'test@example.com',
            'role': 'user',
            'created_at': '2025-01-01T00:00:00',
            'last_login': None,
            'is_active': 1
        }

        user = User.from_db_row(row)
        assert user.id == 1
        assert user.username == 'test'
        assert user.is_active is True

    def test_user_repr(self):
        """Test User __repr__ method."""
        user = User(
            id=1, username='test', password_hash='hash', email=None,
            role='admin', created_at='2025-01-01T00:00:00',
            last_login=None, is_active=True
        )

        repr_str = repr(user)
        assert 'User' in repr_str
        assert 'test' in repr_str
        assert 'admin' in repr_str


class TestArticleModel:
    """Test Article model."""

    def test_article_creation(self):
        """Test Article model creation."""
        article = Article(
            id=1,
            url='https://example.com',
            title='Test Article',
            content='Article content here',
            summary='Summary here',
            link='https://example.com/article',
            timestamp='2025-01-01T00:00:00',
            sentiment='positive',
            user_id=1
        )

        assert article.id == 1
        assert article.title == 'Test Article'
        assert article.user_id == 1

    def test_article_has_summary(self):
        """Test Article has_summary property."""
        article_with = Article(
            id=1, url='https://example.com', title='Test',
            content='Content', summary='Summary', link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment=None, user_id=1
        )

        article_without = Article(
            id=2, url='https://example.com', title='Test',
            content='Content', summary=None, link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment=None, user_id=1
        )

        assert article_with.has_summary is True
        assert article_without.has_summary is False

    def test_article_has_sentiment(self):
        """Test Article has_sentiment property."""
        article_with = Article(
            id=1, url='https://example.com', title='Test',
            content='Content', summary=None, link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment='positive', user_id=1
        )

        article_without = Article(
            id=2, url='https://example.com', title='Test',
            content='Content', summary=None, link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment=None, user_id=1
        )

        assert article_with.has_sentiment is True
        assert article_without.has_sentiment is False

    def test_article_content_length(self):
        """Test Article content_length property."""
        article = Article(
            id=1, url='https://example.com', title='Test',
            content='12345', summary=None, link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment=None, user_id=1
        )

        assert article.content_length == 5

    def test_article_to_dict_no_content(self):
        """Test Article to_dict without content."""
        article = Article(
            id=1, url='https://example.com', title='Test',
            content='Long content here', summary='Summary', link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment='positive', user_id=1
        )

        article_dict = article.to_dict(include_content=False)
        assert 'content' not in article_dict
        assert 'summary' not in article_dict
        assert article_dict['has_summary'] is True
        assert article_dict['content_length'] > 0

    def test_article_to_dict_with_content(self):
        """Test Article to_dict with content."""
        article = Article(
            id=1, url='https://example.com', title='Test',
            content='Content here', summary='Summary here', link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment=None, user_id=1
        )

        article_dict = article.to_dict(include_content=True)
        assert article_dict['content'] == 'Content here'
        assert article_dict['summary'] == 'Summary here'

    def test_article_from_db_row(self):
        """Test Article.from_db_row factory method."""
        row = {
            'id': 1,
            'url': 'https://example.com',
            'title': 'Test',
            'content': 'Content',
            'summary': None,
            'link': 'https://example.com/1',
            'timestamp': '2025-01-01T00:00:00',
            'sentiment': 'positive',
            'user_id': 1
        }

        article = Article.from_db_row(row)
        assert article.id == 1
        assert article.sentiment == 'positive'

    def test_article_repr(self):
        """Test Article __repr__ method."""
        article = Article(
            id=1, url='https://example.com', title='Test Article Title',
            content='Content', summary=None, link='https://example.com',
            timestamp='2025-01-01T00:00:00', sentiment=None, user_id=1
        )

        repr_str = repr(article)
        assert 'Article' in repr_str
        assert '1' in repr_str


class TestScraperProfileModel:
    """Test ScraperProfile model."""

    def test_scraper_creation(self):
        """Test ScraperProfile model creation."""
        scraper = ScraperProfile(
            id=1,
            name='Test Scraper',
            url='https://example.com',
            selector='article',
            default_limit=10,
            default_tags_csv='tech,news',
            description='Test description',
            is_preinstalled=False,
            user_id=1,
            is_shared=True
        )

        assert scraper.name == 'Test Scraper'
        assert scraper.is_shared is True

    def test_scraper_is_editable(self):
        """Test ScraperProfile is_editable property."""
        preinstalled = ScraperProfile(
            id=1, name='Built-in', url='https://example.com',
            selector='div', default_limit=0, default_tags_csv=None,
            description=None, is_preinstalled=True, user_id=1, is_shared=True
        )

        custom = ScraperProfile(
            id=2, name='Custom', url='https://example.com',
            selector='div', default_limit=0, default_tags_csv=None,
            description=None, is_preinstalled=False, user_id=1, is_shared=False
        )

        assert preinstalled.is_editable is False
        assert custom.is_editable is True

    def test_scraper_visibility(self):
        """Test ScraperProfile visibility property."""
        shared = ScraperProfile(
            id=1, name='Shared', url='https://example.com',
            selector='div', default_limit=0, default_tags_csv=None,
            description=None, is_preinstalled=False, user_id=1, is_shared=True
        )

        private = ScraperProfile(
            id=2, name='Private', url='https://example.com',
            selector='div', default_limit=0, default_tags_csv=None,
            description=None, is_preinstalled=False, user_id=1, is_shared=False
        )

        assert shared.visibility == 'shared'
        assert private.visibility == 'private'

    def test_scraper_tags_list(self):
        """Test ScraperProfile tags_list property."""
        scraper = ScraperProfile(
            id=1, name='Test', url='https://example.com',
            selector='div', default_limit=0, default_tags_csv='tech,news,python',
            description=None, is_preinstalled=False, user_id=1, is_shared=False
        )

        tags = scraper.tags_list
        assert tags == ['tech', 'news', 'python']

    def test_scraper_tags_list_empty(self):
        """Test ScraperProfile tags_list when None."""
        scraper = ScraperProfile(
            id=1, name='Test', url='https://example.com',
            selector='div', default_limit=0, default_tags_csv=None,
            description=None, is_preinstalled=False, user_id=1, is_shared=False
        )

        assert scraper.tags_list == []

    def test_scraper_to_dict(self):
        """Test ScraperProfile to_dict method."""
        scraper = ScraperProfile(
            id=1, name='Test', url='https://example.com',
            selector='article', default_limit=10, default_tags_csv='tech',
            description='Desc', is_preinstalled=False, user_id=1, is_shared=True
        )

        scraper_dict = scraper.to_dict()
        assert scraper_dict['name'] == 'Test'
        assert scraper_dict['visibility'] == 'shared'
        assert scraper_dict['is_editable'] is True

    def test_scraper_from_db_row(self):
        """Test ScraperProfile.from_db_row factory method."""
        row = {
            'id': 1,
            'name': 'Test',
            'url': 'https://example.com',
            'selector': 'article',
            'default_limit': 10,
            'default_tags_csv': 'tech',
            'description': 'Desc',
            'is_preinstalled': 0,
            'user_id': 1,
            'is_shared': 1
        }

        scraper = ScraperProfile.from_db_row(row)
        assert scraper.id == 1
        assert scraper.is_shared is True

    def test_scraper_repr(self):
        """Test ScraperProfile __repr__ method."""
        scraper = ScraperProfile(
            id=1, name='Test', url='https://example.com',
            selector='div', default_limit=0, default_tags_csv=None,
            description=None, is_preinstalled=False, user_id=1, is_shared=True
        )

        repr_str = repr(scraper)
        assert 'ScraperProfile' in repr_str
        assert 'Test' in repr_str


class TestTagModel:
    """Test Tag model."""

    def test_tag_creation(self):
        """Test Tag model creation."""
        tag = Tag(id=1, name='python')

        assert tag.id == 1
        assert tag.name == 'python'

    def test_tag_to_dict(self):
        """Test Tag to_dict method."""
        tag = Tag(id=1, name='python')
        tag_dict = tag.to_dict()

        assert tag_dict == {'id': 1, 'name': 'python'}

    def test_tag_from_db_row(self):
        """Test Tag.from_db_row factory method."""
        row = {'id': 1, 'name': 'python'}
        tag = Tag.from_db_row(row)

        assert tag.id == 1
        assert tag.name == 'python'

    def test_tag_repr(self):
        """Test Tag __repr__ method."""
        tag = Tag(id=1, name='python')
        repr_str = repr(tag)

        assert 'Tag' in repr_str
        assert 'python' in repr_str

    def test_tag_str(self):
        """Test Tag __str__ method."""
        tag = Tag(id=1, name='python')
        assert str(tag) == 'python'


class TestSessionModel:
    """Test Session model."""

    def test_session_creation(self):
        """Test Session model creation."""
        session = Session(
            id=1,
            session_token='abc123',
            user_id=1,
            created_at='2025-01-01T00:00:00',
            expires_at='2025-01-02T00:00:00',
            ip_address='127.0.0.1'
        )

        assert session.id == 1
        assert session.user_id == 1
        assert session.ip_address == '127.0.0.1'

    def test_session_created_datetime(self):
        """Test Session created_datetime property."""
        session = Session(
            id=1, session_token='token', user_id=1,
            created_at='2025-01-01T12:00:00',
            expires_at='2025-01-02T00:00:00'
        )

        created = session.created_datetime
        assert isinstance(created, datetime)
        assert created.hour == 12

    def test_session_expires_datetime(self):
        """Test Session expires_datetime property."""
        session = Session(
            id=1, session_token='token', user_id=1,
            created_at='2025-01-01T00:00:00',
            expires_at='2025-01-02T12:00:00'
        )

        expires = session.expires_datetime
        assert isinstance(expires, datetime)
        assert expires.day == 2

    def test_session_is_expired_true(self):
        """Test Session is_expired when expired."""
        # Past session
        session = Session(
            id=1, session_token='token', user_id=1,
            created_at='2020-01-01T00:00:00',
            expires_at='2020-01-02T00:00:00'
        )

        assert session.is_expired is True

    def test_session_is_expired_false(self):
        """Test Session is_expired when active."""
        # Future session
        session = Session(
            id=1, session_token='token', user_id=1,
            created_at='2025-01-01T00:00:00',
            expires_at='2099-01-02T00:00:00'
        )

        assert session.is_expired is False

    def test_session_time_remaining_expired(self):
        """Test Session time_remaining when expired."""
        session = Session(
            id=1, session_token='token', user_id=1,
            created_at='2020-01-01T00:00:00',
            expires_at='2020-01-02T00:00:00'
        )

        assert session.time_remaining is None

    def test_session_time_remaining_active(self):
        """Test Session time_remaining when active."""
        session = Session(
            id=1, session_token='token', user_id=1,
            created_at='2025-01-01T00:00:00',
            expires_at='2099-01-02T00:00:00'
        )

        remaining = session.time_remaining
        assert remaining is not None
        assert remaining > 0

    def test_session_to_dict(self):
        """Test Session to_dict excludes token for security."""
        session = Session(
            id=1, session_token='secret_token', user_id=1,
            created_at='2025-01-01T00:00:00',
            expires_at='2025-01-02T00:00:00'
        )

        session_dict = session.to_dict()
        assert 'session_token' not in session_dict
        assert session_dict['user_id'] == 1
        assert 'is_expired' in session_dict

    def test_session_from_db_row(self):
        """Test Session.from_db_row factory method."""
        row = {
            'id': 1,
            'session_token': 'token',
            'user_id': 1,
            'created_at': '2025-01-01T00:00:00',
            'expires_at': '2025-01-02T00:00:00',
            'ip_address': '127.0.0.1'
        }

        session = Session.from_db_row(row)
        assert session.id == 1
        assert session.session_token == 'token'
        assert session.ip_address == '127.0.0.1'

    def test_session_from_db_row_no_ip(self):
        """Test Session.from_db_row without IP address."""
        row = {
            'id': 1,
            'session_token': 'token',
            'user_id': 1,
            'created_at': '2025-01-01T00:00:00',
            'expires_at': '2025-01-02T00:00:00'
        }

        session = Session.from_db_row(row)
        assert session.ip_address is None

    def test_session_repr(self):
        """Test Session __repr__ method."""
        session = Session(
            id=1, session_token='token', user_id=1,
            created_at='2020-01-01T00:00:00',
            expires_at='2020-01-02T00:00:00'
        )

        repr_str = repr(session)
        assert 'Session' in repr_str
        assert 'expired' in repr_str
