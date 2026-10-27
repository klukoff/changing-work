#!/usr/bin/env python3
"""Apply the release's common AI-text screen to locally recovered descriptions.
Input: JSON list of {record_id,role,analysis_text}; output is private evidence JSON.
Counts are automatic candidates, not validated employee expectations or AI adoption.
"""
import argparse,json
from collections import defaultdict,Counter
from pathlib import Path
from common_detector import common_dimensions,VERSION
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
rows=json.loads(a.input.read_text());counts=defaultdict(Counter);ns=Counter();results=[]
for r in rows:
 text=r['analysis_text'];role=r.get('role','unspecified');signals=common_dimensions(text);ns[role]+=1
 for k,v in signals.items():counts[role][k]+=bool(v['detected'])
 results.append({'record_id':r['record_id'],'role':role,'signals':signals})
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps({'detector':VERSION,'status':'automatic_candidates_not_validated','roles':{r:{'n':ns[r],'counts':dict(v)} for r,v in counts.items()},'records':results},indent=2)+'\n')
print(json.dumps({'detector':VERSION,'n':len(rows),'output_contains_source_excerpts':True,'publication_instruction':'Keep this output private; publish only vetted aggregates and bounded excerpts.'}))
