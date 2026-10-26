"""Export an allowlisted source ZIP; never copy working databases or credentials.

Run after reviewing/committing your changes: python tools/package_release.py
This checks current export contents, not old Git history or a deployed host.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP = {'README.md','LICENSE','CONTRIBUTORS.md','CONTRIBUTING.md','SECURITY.md',
       '.gitignore','.env.example','.env.calendar.example','Setup-StudyMate.cmd','Start-StudyMate.cmd','render.yaml'}
PREFIXES = {'app','docs','tests','tools','.github'}
RULES = {
    'private-key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'github-token': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{45,})'),
    'google-oauth-secret': re.compile(rb'GOCSPX-[A-Za-z0-9_-]{20,}'),
    'google-api-key': re.compile(rb'AIza[0-9A-Za-z_-]{30,}'),
}


def eligible(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:
        return False
    if any(part in {'.git','.venv','.tmp','__pycache__','data','secrets','node_modules'} for part in path.parts):
        return False
    if re.search(r'\.(?:db|sqlite3?)(?:[-.]|$)',path.name,re.I):
        return False
    if path.suffix.lower() in {'.pyc','.pem','.key','.log','.zip','.csv'}:
        return False
    if path.name.startswith('.env') and name not in {'.env.example','.env.calendar.example'}:
        return False
    if re.match(r'(?:client_secret|credentials|tokens?)(?:[._-]|$)',path.name,re.I):
        return False
    return (name in TOP or path.parts[0] in PREFIXES
            or path.name.startswith('requirements') and path.suffix == '.txt')


def content_issues(data):
    return [name for name, pattern in RULES.items() if pattern.search(data)]


def collect(root=ROOT):
    result = subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],
        cwd=root,check=True,capture_output=True)
    files = {}
    for name in sorted(set(result.stdout.decode('utf-8').split('\0'))-{''}):
        path=root/name
        if not eligible(name) or not path.is_file():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Source links outside the checkout are not allowed')
        data=path.read_bytes()
        issues=content_issues(data)
        if issues:
            # Never print a matched secret or surrounding line.
            raise ValueError(f'Review required: {name} ({", ".join(issues)})')
        files[name]=data
    for required in ('README.md','LICENSE','app/main.py','requirements-lock.txt'):
        if required not in files:
            raise ValueError('Required release file missing: '+required)
    return files


def build(destination, root=ROOT):
    files=collect(root)
    revision=subprocess.run(['git','rev-parse','HEAD'],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
    dirty=bool(subprocess.run(['git','status','--porcelain'],cwd=root,check=True,capture_output=True).stdout)
    manifest={'source_commit':revision,'uncommitted_changes':dirty,'history_included':False,
        'license':'MIT; original notice preserved','scanner_scope':'current allowlisted files; heuristic, not a full secret/history audit',
        'files':{name:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for name,data in files.items()}}
    destination=Path(destination).resolve()
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in files.items():
            archive.writestr('StudyMate/'+name,data)
        archive.writestr('StudyMate/RELEASE_MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    digest=hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix('.sha256').write_text(digest+'  '+destination.name+'\n',encoding='utf-8')
    return {'archive':str(destination),'files':len(files),'sha256':digest,
        'source_commit':revision,'uncommitted_changes':dirty}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'dist'/'StudyMate-source.zip')
    args=parser.parse_args()
    print(json.dumps(build(args.output),indent=2))


if __name__=='__main__':
    main()
