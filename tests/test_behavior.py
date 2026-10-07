import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

@pytest.fixture
def application():
    # No production DB engine, credentials, or identity provider is used by tests.
    db = MagicMock()
    db.Model = type('Model', (), {})
    sqlalchemy = MagicMock()
    sqlalchemy.SQLAlchemy.return_value = db
    spec = importlib.util.spec_from_file_location('risk_app_under_test', Path(__file__).resolve().parents[1] / 'app.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'flask_sqlalchemy':sqlalchemy,'psycopg2':MagicMock(),'msal':MagicMock(),'risk_app_under_test':module}):
        spec.loader.exec_module(module)
    module.app.config.update(TESTING=True, SECRET_KEY='test-only-secret')
    return module

def test_anonymous_requests_redirect_to_login(application):
    client = application.app.test_client()
    response = client.get('/')
    assert response.status_code == 302
    assert response.location.endswith('/login')
    application.db.session.commit.assert_not_called()

def test_login_saves_state_and_redirects_to_provider(application, monkeypatch):
    monkeypatch.setattr(application,'_build_auth_url',lambda **kwargs:'https://login.example.test/authorize')
    client = application.app.test_client()
    response = client.get('/login')
    assert response.location == 'https://login.example.test/authorize'
    with client.session_transaction() as session:
        assert session['state']

def test_logout_clears_authenticated_session(application):
    client = application.app.test_client()
    with client.session_transaction() as session:
        session['user'] = {'name':'Test User'}
    response = client.get('/logout')
    assert response.status_code == 302
    assert 'logout' in response.location
    with client.session_transaction() as session:
        assert 'user' not in session
