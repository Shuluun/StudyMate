"""Exercise the real offline HTTP app, including a real process restart.

Uses a temporary SQLite directory, synthetic accounts, and loopback requests only.
Run from the source checkout: python tools/smoke.py
"""
import json
import os
from contextlib import contextmanager
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]
DAY = '2026-10-26'


def stop(process):
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


@contextmanager
def scratch_directory():
    temporary = tempfile.TemporaryDirectory(prefix='studymate-smoke-')
    target = Path(temporary.name).resolve()
    if target.parent != Path(tempfile.gettempdir()).resolve() or not target.name.startswith('studymate-smoke-'):
        raise RuntimeError('Unexpected smoke-test temporary directory')
    try:
        yield str(target)
    finally:
        # Windows scanners can briefly retain SQLite handles after the child exits.
        # Retry only our own verified temporary directory; never clean user data.
        for attempt in range(12):
            try:
                temporary.cleanup()
                break
            except PermissionError:
                if attempt == 11:
                    raise
                time.sleep(0.2)


def launch(port, data_dir, environment):
    process = subprocess.Popen([sys.executable, '-m', 'app.demo', '--port', str(port),
        '--data-dir', str(data_dir)], cwd=ROOT, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError('Local demo exited before startup completed')
            try:
                if httpx.get(f'http://127.0.0.1:{port}/api/health', timeout=1).status_code == 200:
                    return process
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        raise RuntimeError('Local demo did not become ready')
    except BaseException:
        stop(process)
        raise


def slots(client):
    response = client.get('/api/schedule/week', params={'day': DAY})
    assert response.status_code == 200
    return response.json()['entries']


def csrf(client):
    page = client.get('/schedule', params={'day': DAY})
    assert page.status_code == 200
    payload = json.loads(re.search(r'<script id="calendar-week-data" type="application/json">(.*?)</script>',page.text,re.S)[1])
    return {'X-CSRF-Token': payload['csrf']}


def main():
    checks = []
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    environment = {**os.environ, 'STUDYMATE_SESSION_SECRET': secrets.token_urlsafe(48)}
    password = secrets.token_urlsafe(20)
    with scratch_directory() as directory:
        process = launch(port, directory, environment)
        try:
            with httpx.Client(base_url=f'http://127.0.0.1:{port}',follow_redirects=True,timeout=10) as ada, \
                 httpx.Client(base_url=f'http://127.0.0.1:{port}',follow_redirects=True,timeout=10) as bob:
                for client, name in ((ada,'Ada'),(bob,'Bob')):
                    assert client.post('/register',data={'name':name+' Synthetic','email':name.lower()+'@example.invalid','password':password}).status_code == 200
                    response=client.put('/api/profile/me',json={'major':'Physics','year':2,'courses':'Math 54',
                        'street_address':'UC Berkeley','radius_meters':1500,'group_min':2,'group_max':3,
                        'study_styles':['talk'],'place_types':['library']})
                    assert response.status_code == 200
                checks.append('register and save two independent profiles')
                assert ada.get('/api/profile/me').json()['id'] != bob.get('/api/profile/me').json()['id']
                assert 'email' not in ada.get('/api/profile/me').json()
                headers=csrf(ada)
                assert ada.post('/api/schedule/entry',headers=headers,json={'kind':'busy',
                    'starts_at':DAY+'T15:30','ends_at':DAY+'T16:00'}).status_code == 200
                busy_id=next(e['id'] for e in slots(ada) if e['kind']=='busy')
                assert not any(e['id']==busy_id for e in slots(bob))
                assert bob.get('/schedule?owner_id=u_maya').status_code == 403
                checks.append('own schedule edits and cross-account isolation')
                response=ada.post('/session/rooms',data={'course_id':'math54','starts_at':DAY+'T13:00',
                    'ends_at':DAY+'T14:00','place_type':'library','group_size':'3'},follow_redirects=False)
                assert 'error=' not in response.headers['location']
                room=next(e for e in slots(ada) if e['kind']=='session')
                response=bob.post('/session/rooms/'+room['id']+'/join',follow_redirects=False)
                assert 'error=' not in response.headers['location']
                assert any(e['id']==room['id'] for e in slots(bob))
                checks.append('create and join a room, both schedules update')
                response=ada.post('/session/rooms/'+room['id']+'/time',data={'course_id':'math54',
                    'starts_at':DAY+'T13:00','ends_at':DAY+'T14:00','place_type':'library',
                    'room_day':DAY,'room_start':'14:00','room_end':'15:00'},follow_redirects=False)
                assert 'error=' not in response.headers['location']
                assert next(e for e in slots(bob) if e['id']==room['id'])['starts_at']==DAY+'T14:00'
                checks.append('host rescheduling updates another member')
                stop(process)
                process=launch(port,directory,environment)
                for client,name in ((ada,'Ada'),(bob,'Bob')):
                    assert client.post('/login',data={'email':name.lower()+'@example.invalid','password':password}).status_code == 200
                    assert client.get('/api/profile/me').json()['major']=='Physics'
                    assert any(e['id']==room['id'] and e['starts_at']==DAY+'T14:00' for e in slots(client))
                assert any(e['id']==busy_id for e in slots(ada))
                checks.append('accounts, profiles, schedules and rooms survive a real process restart')
                bob.post('/session/rooms/'+room['id']+'/leave',follow_redirects=False)
                assert not any(e['id']==room['id'] for e in slots(bob))
                assert any(e['id']==room['id'] for e in slots(ada))
                ada.post('/session/rooms/'+room['id']+'/leave',follow_redirects=False)
                assert not any(e['id']==room['id'] for e in slots(ada))
                checks.append('leaving removes reservations and closes an empty room')
        finally:
            stop(process)
    print(json.dumps({'result':'PASS','checks':checks,'database':'temporary SQLite',
        'external_services_used':False,'real_process_restart':True},indent=2))


if __name__ == '__main__':
    main()
