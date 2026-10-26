"""Run a persistent, offline, loopback-only demonstration with no credentials."""
import argparse
import os
from pathlib import Path


def configure(directory):
    """Explicit local URLs take priority over a developer's private .env file."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    os.environ['DATABASE_URL'] = 'sqlite+pysqlite:///' + (directory/'studymate.db').as_posix()
    os.environ['STUDYMATE_CALENDAR_DB'] = 'sqlite+pysqlite:///' + (directory/'calendar.db').as_posix()
    os.environ['STUDYMATE_OFFLINE'] = '1'
    os.environ['STUDYMATE_CALENDAR_MODE'] = 'synthetic'
    os.environ['STUDYMATE_DB'] = 'local'
    # HTTP loopback preview only. Public HTTPS hosts must use the normal entrypoint.
    os.environ['STUDYMATE_SECURE_COOKIES'] = '0'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8020)
    parser.add_argument('--data-dir', type=Path, default=Path('data/demo'))
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be between 1 and 65535')
    configure(args.data_dir)
    import uvicorn
    print(f'StudyMate offline demo: http://127.0.0.1:{args.port}/')
    print('Fictional accounts and places; no Google, model, email or calendar writes.')
    uvicorn.run('app.main:app', host='127.0.0.1', port=args.port, access_log=False)


if __name__ == '__main__':
    main()
