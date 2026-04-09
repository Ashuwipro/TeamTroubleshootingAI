#!/usr/bin/env python3
"""
Test navigation in SFTP directory
"""
import requests

r = requests.get('http://localhost:5000/api/sftp-directory', params={'saas': 'saasN', 'path': '/DEV1'})
print(f'Status: {r.status_code}')
d = r.json()
print(f'Path: {d.get("path")}')
print(f'Parent Path: {d.get("parentPath")}')
print(f'Entries count: {len(d.get("entries", []))}')
print('\nFirst entries:')
for e in d.get('entries', [])[:10]:
    print(f'  - {e["name"]} ({e["entryType"]})')

