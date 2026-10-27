#!/usr/bin/env python3
"""Meaningful static-release checks, without browser or private source access."""
import csv,json,re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
root=Path(__file__).resolve().parents[1]
def load(p):return json.loads((root/p).read_text())
s=load('data/study.json');roles=s['roles'];assert len(roles)==5
assert sum(r['sample_n'] for r in roles)==2846
skills=[x for r in roles for b in r['branches'] for x in b['skills']]
assert len(skills)==99 and len({x['id'] for x in skills})==99
for r in roles:
 for b in r['branches']:
  for sk in b['skills']:
   assert 0<=sk['count']<=r['sample_n']
   assert sk['n']==r['sample_n']
   assert sk['definition'] and sk['include_when'] and sk['exclude_when']
   if r['id'] in ['uxr','design','pm']:assert sk['status']=='ai_reviewed' and sk['reviewed_n']<sk['n']
   for ex in sk['evidence']:
    assert len(ex.get('quote','').split())<=25
    if ex.get('source_url'):assert ex['source_url'].startswith('https://')
metadata=load('downloads/cohort-metadata.json');assert len(metadata)==2846
assert len({x.get('canonical_posting_id') or x.get('posting_id') for x in metadata})==2846
for x in metadata:assert 'analysis_text' not in x and 'raw' not in x
rows=list(csv.DictReader((root/'downloads/skill-counts.csv').open()));assert len(rows)==99
for sk,row in zip(skills,rows):assert int(row['count'])==sk['count']
links=[]
class Links(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v:links.append(v)
for p in root.rglob('*.html'):
 if 'qa' in p.parts:continue
 links.clear();Links().feed(p.read_text())
 for link in links:
  u=urlsplit(link)
  if not u.scheme and u.path:assert (p.parent/unquote(u.path)).resolve().exists(),(str(p),link)
for x in s['downloads']+s['methods']['links']:assert (root/x['url']).exists(),x['url']
for p in root.rglob('*'):
 if not p.is_file() or any(x in p.parts for x in ['.git','qa','__pycache__']):continue
 if p.suffix in ['.json','.csv','.html','.js','.css','.py','.md']:
  text=p.read_text()
  # The checker itself contains these test strings; do not scan its source.
  if p.name!='validate_release.py':
   assert not re.search(r'/Users/|ghp_[A-Za-z0-9]{20,}|github_pat_|Bearer [A-Za-z0-9]{20,}|Satoko|satokoo|photoslibrary',text),p
print('PASS: 5 roles, 2846 unique source postings, 99 definitions, count/denominator consistency, bounded excerpts, local links and public-field checks.')
