"""Public demo defaults: isolated data, no accidental model calls, private sessions."""
import pytest
from fastapi.testclient import TestClient
from app import advise, demo, omnara_client
from app.main import create_app


def test_offline_blocks_implicit_omnara_configuration(monkeypatch):
    monkeypatch.setenv('STUDYMATE_OFFLINE', '1')
    # Even a configured developer machine must not make requests in offline mode.
    for key in (*advise.SETTINGS, 'OMNARA_AGENT'):
        monkeypatch.setenv(key, 'synthetic-configuration')
    with pytest.raises(advise.AdviseUnavailable, match='Offline'):
        advise.OmnaraAdviseClient().complete('system', 'user', {}, 0.2)
    with pytest.raises(omnara_client.OmnaraError, match='Offline'):
        omnara_client.interpret_request([], [])


def test_demo_explicitly_uses_local_data_over_cloud_settings(tmp_path, monkeypatch):
    for key in ('DATABASE_URL','STUDYMATE_CALENDAR_DB','STUDYMATE_OFFLINE','STUDYMATE_CALENDAR_MODE',
                'STUDYMATE_DB','STUDYMATE_SECURE_COOKIES'):
        monkeypatch.setenv(key, 'synthetic-old-setting')
    demo.configure(tmp_path)
    import os
    assert os.environ['DATABASE_URL'].startswith('sqlite+pysqlite:///')
    assert os.environ['STUDYMATE_CALENDAR_DB'].startswith('sqlite+pysqlite:///')
    assert os.environ['STUDYMATE_OFFLINE'] == '1'
    assert os.environ['STUDYMATE_DB'] == 'local'


def test_session_secret_is_required_to_be_strong_when_supplied(monkeypatch):
    monkeypatch.setenv('STUDYMATE_SESSION_SECRET', 'short')
    with pytest.raises(ValueError, match='32 characters'):
        create_app()


def test_unconfigured_app_instances_do_not_share_a_public_cookie_key(monkeypatch):
    monkeypatch.delenv('STUDYMATE_SESSION_SECRET', raising=False)
    a, b = create_app(), create_app()
    first = next(m for m in a.user_middleware if m.cls.__name__ == 'SessionMiddleware')
    second = next(m for m in b.user_middleware if m.cls.__name__ == 'SessionMiddleware')
    assert first.kwargs['secret_key'] != second.kwargs['secret_key']
    assert len(first.kwargs['secret_key']) >= 32


def test_https_cookie_option_and_login_redirect(monkeypatch):
    monkeypatch.setenv('STUDYMATE_SESSION_SECRET', 'synthetic-private-test-secret-'+'x'*32)
    monkeypatch.setenv('STUDYMATE_SECURE_COOKIES', '1')
    app = create_app()
    middleware = next(m for m in app.user_middleware if m.cls.__name__ == 'SessionMiddleware')
    assert middleware.kwargs['https_only'] is True
    with TestClient(app, base_url='https://testserver') as client:
        assert client.get('/schedule', follow_redirects=False).headers['location'] == '/login'
