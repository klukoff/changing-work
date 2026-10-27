import sys,json,collections,hashlib
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,required=True);args=p.parse_args();root=args.project_root;sys.path.insert(0,str(root/'analysis/software_engineering_2026-10-26'));sys.path.insert(0,str(root/'analysis/openjobdata_pilot_500_2026-10-16/design_pm'))
from body_geography import assess_with_body,VERSION
files={r:root/f'collection/openjobdata_pilot_500_2026-10-16/{r}/pilot_sample.json' for r in ['uxr','design','pm']};files.update(marketing=root/'collection/marketing_pilot_500_2026-10-17/sample.json',swe=root/'collection/software_engineering_2026-10-26/sample.json')
ann=json.load(open(root/'outputs/expanded_coding_2026-10-26/annotations.json'))+json.load(open(root/'analysis/software_engineering_2026-10-26/annotations.json'));idx={x['record_id']:x for x in ann}
report={'version':'quality-audit-2026-10-26','geography_version':VERSION,'interpretation':'Sensitivity variants, not corrected population estimates. Main samples are retained. Automated AI signals remain unvalidated. Geography is a rule-assisted audit, not independent ground truth.','roles':{}}
private={'roles':{}}
for role,p in files.items():
 ads=json.load(open(p));g={a['record_id']:assess_with_body(a) for a in ads};groups={'retained_cohort':ads,'corroborated_US':[a for a in ads if g[a['record_id']]['classification'] in ['us_corroborated_raw_job_location','us_and_non_us_location_options']],'known_2026_original_date':[a for a in ads if (a.get('posted_at') or '').startswith('2026-')],'posted_since_2026_07_18':[a for a in ads if '2026-07-18'<=(a.get('posted_at') or '')[:10]<='2026-10-16'],'active_at_snapshot':[a for a in ads if a.get('source_state')=='active']}
 employer=collections.Counter(a.get('employer') or a.get('company_name') for a in ads);largest,count=employer.most_common(1)[0];groups['excluding_largest_source_employer']=[a for a in ads if (a.get('employer') or a.get('company_name'))!=largest]
 text_seen=set();unique=[]
 for a in ads:
  h=a.get('analysis_text_sha256') or hashlib.sha256(a['analysis_text'].encode()).hexdigest()
  if h not in text_seen:unique.append(a);text_seen.add(h)
 groups['one_record_per_exact_text_hash']=unique
 stats={}
 for group,rows in groups.items():
  counts={m:sum(idx[a['record_id']].get('common_signals',idx[a['record_id']].get('common_dimensions',{}))[m]['detected'] for a in rows) for m in ['any_ai_reference','workflow','product','enablement']}
  stats[group]={'n':len(rows),'automatic_signal_counts':counts,'automatic_signal_percent':{k:round(v/len(rows)*100,2) if rows else None for k,v in counts.items()}}
 report['roles'][role]={'n':len(ads),'geography_classifications':dict(collections.Counter(x['classification'] for x in g.values())),'non_US_or_unresolved_after_body_check_n':sum(x['decision']!='include_us' for x in g.values()),'largest_source_employer':{'name':largest,'ads':count},'unique_exact_text_hashes':len(unique),'sensitivity':stats}
 private['roles'][role]={'assessments':g}
packets=json.load(open(root/'outputs/expanded_coding_2026-10-26/review_packets.json'))
report['role_boundary_review_flags']=[{k:packets[i][k] for k in ['role','record_id','title','employer']} for i in [93,117,150,231]]
report['role_boundary_review_note']='These retained hybrid or adjacent titles need primary-role adjudication. The public release preserves original cohort membership; do not treat these flags alone as exclusions.'
(root/'site/downloads/quality-report.json').write_text(json.dumps(report,indent=2)+'\n');(root/'analysis/public_release_2026-10-26/geography_sensitivity.json').write_text(json.dumps(private,indent=2)+'\n')
print({r:{'n':x['n'],'flagged':x['non_US_or_unresolved_after_body_check_n'],'corroborated':x['sensitivity']['corroborated_US']['n']} for r,x in report['roles'].items()})
