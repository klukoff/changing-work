#!/usr/bin/env python3
"""Pin and optionally archive a public OpenJobData change batch.

This is collection infrastructure, not an eligibility or prevalence analysis.
Raw files and candidate payloads must stay outside the published repository.
Requires duckdb only when --capture is requested. No credentials are needed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

REPO = 'scholarweave/Jobs-Dataset-v2'
API = 'https://huggingface.co/api/datasets/' + REPO
ROLE_PATTERNS = {
    'uxr': r'\b(?:ux|user|usability|design|customer experience|consumer experience)\s*(?:research|insight)|\bresearch\s*(?:scientist|manager|lead).*(?:user|ux|design)',
    'design': r'\b(?:product|ux|ui|interaction|experience|digital)\s*(?:design)|\bdesign\s*engineer',
    'pm': r'\bproduct\s*(?:manager|management|owner|lead|director)|\b(?:head|vp|director|vice president)\s+(?:of\s+)?product\b',
    'marketing': r'\bmarketing\b|\b(?:brand|growth|customer experience|consumer engagement|omnichannel|digital strategy)\s*(?:manager|director|lead|strategist|head)',
    'swe': r'\bsoftware\b.*\b(?:engineer|developer)|\b(?:frontend|front.end|backend|back.end|full.stack|platform|machine learning|data|devops|mobile)\s*(?:engineer|developer)|\b(?:web|application)\s*developer',
}

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Changing-Work-Research/0.1'})
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.load(response)

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def roles_for(title):
    return [role for role, pattern in ROLE_PATTERNS.items() if re.search(pattern, title or '', re.I)]

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + '\n')

def download(item, base, folder):
    path = folder / Path(item['path']).name
    expected = item.get('lfs', {}).get('oid')
    if not expected:
        raise ValueError('Expected publisher LFS SHA256 missing: ' + item['path'])
    if path.exists() and path.stat().st_size == item['size'] and sha(path) == expected:
        return {'path': item['path'], 'bytes': item['size'], 'sha256': expected, 'cached': True}
    for attempt in range(3):
        try:
            req = urllib.request.Request(base + urllib.parse.quote(item['path'], safe='/'), headers={'User-Agent': 'Changing-Work-Research/0.1'})
            temporary = path.with_suffix('.part')
            with urllib.request.urlopen(req, timeout=120) as response, temporary.open('wb') as output:
                for chunk in iter(lambda: response.read(1024 * 1024), b''):
                    output.write(chunk)
            if temporary.stat().st_size != item['size'] or sha(temporary) != expected:
                raise ValueError('Publisher bytes/SHA256 mismatch: ' + item['path'])
            temporary.replace(path)
            return {'path': item['path'], 'bytes': item['size'], 'sha256': expected, 'cached': False}
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', help='Immutable source commit; omitted pins current commit before reading data')
    parser.add_argument('--date', help='Source batch date; default newest available change batch')
    parser.add_argument('--capture', action='store_true', help='Download the full batch and retain title-retrieved candidate payloads')
    parser.add_argument('--max-download-mb', type=int, default=1500, help='Fail before downloads if full batch exceeds this bound')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    info = get(API + ('/revision/' + args.revision if args.revision else ''))
    revision = info['sha']
    base = 'https://huggingface.co/datasets/' + REPO + '/resolve/' + revision + '/'
    manifest = get(base + 'data/manifests/current.json')
    choices = [x for x in manifest['changes'] if not args.date or x['date'] == args.date]
    if not choices:
        raise ValueError('Requested date is absent from current manifest. Select an archived revision explicitly.')
    batch = sorted(choices, key=lambda x: (x['date'], x['run_id']))[-1]
    root = args.output / revision / batch['run_id']
    root.mkdir(parents=True, exist_ok=True)
    tree_path = 'data/changes/full/date=' + batch['date'] + '/run_id=' + batch['run_id']
    files = get(API + '/tree/' + revision + '/' + tree_path)
    files = sorted([x for x in files if x['type'] == 'file' and x['path'].endswith('.parquet')], key=lambda x: x['path'])
    if len(files) >= 1000:
        raise ValueError('Pagination must be handled before treating this tree as complete.')
    write_json(root / 'manifest.json', manifest)
    write_json(root / 'file_manifest.json', files)
    summary = {
        'version': 'prospective-capture-v1', 'repository': REPO, 'revision': revision,
        'captured_at': datetime.now(timezone.utc).isoformat(), 'source_updated_at': manifest['updated_at'],
        'batch': batch, 'expected_files': len(files), 'expected_bytes': sum(x['size'] for x in files),
        'status': 'manifest_only', 'interpretation': 'Source change batch; inserts, updates, and closures are not newly posted vacancies.',
        'candidate_status': 'Unscreened title retrieval, not eligible occupational cohorts. No AI filter.',
        'date_policy': 'Keep posted_at, first_seen_at, observation and collection dates separate. Collector onboarding and backfills can introduce old ads.',
        'publication_policy': 'Raw descriptions and private review notes are not part of public downloads.',
    }
    if args.capture:
        if summary['expected_bytes'] > args.max_download_mb * 1000000:
            raise ValueError('Batch exceeds configured download bound; no partial frame will be reported.')
        folder = root / 'raw'
        folder.mkdir(exist_ok=True)
        with ThreadPoolExecutor(max_workers=3) as pool:
            verified = list(pool.map(lambda item: download(item, base, folder), files))
        write_json(root / 'download_log.json', verified)
        import duckdb
        db = duckdb.connect()
        db.execute("SET threads=2")
        rows_seen, candidate_rows = 0, 0
        event_counts = Counter()
        counts = {k: 0 for k in ROLE_PATTERNS}
        unique = {k: set() for k in ROLE_PATTERNS}
        seen_versions = set()
        with (root / 'candidates.jsonl').open('w') as output:
            for file in files:
                cursor = db.execute('SELECT * FROM read_parquet(?)', [str(folder / Path(file['path']).name)])
                names = [x[0] for x in cursor.description]
                while True:
                    rows = cursor.fetchmany(2000)
                    if not rows:
                        break
                    for row in rows:
                        rows_seen += 1
                        record = dict(zip(names, row))
                        event_counts[str(record.get('event_type') or 'unspecified')] += 1
                        roles = roles_for(record.get('title'))
                        if not roles:
                            continue
                        key = (record.get('posting_id'), record.get('content_hash'), str(record.get('event_type') or record.get('change_type') or ''))
                        if key in seen_versions:
                            continue
                        seen_versions.add(key)
                        record['_collection'] = {'revision': revision, 'source_file': file['path'], 'source_sha256': file['lfs']['oid'], 'candidate_roles': roles, 'screening_status': 'not_screened'}
                        output.write(json.dumps(record, ensure_ascii=False, default=str) + '\n')
                        candidate_rows += 1
                        for role in roles:
                            counts[role] += 1
                            unique[role].add(record.get('posting_id'))
        expected_events = {k.split(':', 1)[1]: v for k, v in batch.get('counts', {}).items() if k.startswith('full:')}
        discrepancies = {k: {'manifest': v, 'archived_rows': event_counts.get(k, 0)}
                         for k, v in expected_events.items() if event_counts.get(k, 0) != v}
        summary.update(status='listed_full_files_archived' if not discrepancies else 'listed_files_archived_manifest_discrepancy',
                       verified_files=len(verified), rows_seen=rows_seen,
                       archived_event_counts=dict(event_counts), manifest_discrepancies=discrepancies,
                       completeness_note='All listed full Parquet files verified. Event counts must reconcile before this capture can define a complete change cohort.',
                       candidate_versions=candidate_rows, candidate_versions_by_role=counts,
                       candidate_unique_ids_by_role={k: len(v) for k,v in unique.items()},
                       candidates_sha256=sha(root / 'candidates.jsonl'))
    write_json(root / 'capture_summary.json', summary)
    write_json(args.output / 'latest_capture_summary.json', summary)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
