import pytest
from tools.package_release import content_issues, eligible


@pytest.mark.parametrize('path',['.env','data/users.db','secrets/client.json','.tmp/output.txt',
    'app/__pycache__/main.pyc','.venv/test.py','docs/token.json','docs/client_secret.json',
    '../README.md','/app/main.py','docs/private.key','docs/schedule.db-wal',
    'docs/users.sqlite3-journal','docs/account-export.csv','docs/nested.zip'])
def test_export_excludes_private_and_runtime_files(path):
    assert not eligible(path)


@pytest.mark.parametrize('path',['README.md','LICENSE','.env.example','app/main.py',
    'docs/screenshots/schedule.png','.github/workflows/tests.yml','requirements-lock.txt','tools/smoke.py'])
def test_export_includes_reusable_source_and_documentation(path):
    assert eligible(path)


def test_secret_checks_report_rule_names_not_secret_values():
    fake=b'ghp_'+b'A'*36
    result=content_issues(fake)
    assert result==['github-token'] and fake.decode() not in str(result)
    assert content_issues(b'-----BEGIN '+b'PRIVATE KEY-----')==['private-key']
    assert content_issues(b'No keys; DATABASE_URL is set privately.')==[]
