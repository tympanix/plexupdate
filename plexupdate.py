# Plex update script

import requests
import shutil
import sys
import platform
import os
import time
from subprocess import call
from plexapi.server import PlexServer

dist = 'Ubuntu'
arch = platform.machine()

baseurl = 'http://localhost:32400'
token = os.environ.get('PLEX_TOKEN')

if not token:
    print('Missing plex token')
    exit(1)

plex = PlexServer(baseurl, token)

r = requests.get('https://plex.tv/api/downloads/1.json')
releases = r.json().get('computer').get('Linux').get('releases')

release = None
for rel in releases:
    label = rel.get('label')
    build = rel.get('build')
    if dist in label and arch in build:
        release = rel
        break

if not release:
    print('Could not find release!')
    exit(1)

if plex.version in release.get('url'):
    print('Skip update!')
    exit(0)

print(release.get('url'))

name = release.get('url').split('/')[-1]
path = '/tmp/{}'.format(name)

r = requests.get(release.get('url'), stream=True)
if r.status_code != 200:
    print('Could not download file')
with open(path, 'wb') as f:
    r.raw.decode_content = True
    shutil.copyfileobj(r.raw, f)

while len(plex.sessions()) > 0:
    print('Waiting for sessions to be over')
    time.sleep(300)

install = ['dpkg', '-i', path]
code = call(install, stdout=sys.stdout, stderr=sys.stderr)
if code != 0:
    print('Could not install update!')

restart = ['service', 'plexmediaserver', 'restart']
code = call(restart, stdout=sys.stdout, stderr=sys.stderr)
if code != 0:
    print('Could not restart plex!')
    exit(1)

os.remove(path)
