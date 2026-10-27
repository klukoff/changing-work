#!/usr/bin/env python3
"""Build the static release from retained private study artifacts.

Usage: python3 scripts/build_public.py --project-root /path/to/research-workspace
Does not collect ads. The source workspace layout is documented in README.
Exports an allowlist of aggregate/definition fields, never full ad text or feedback.
"""
import argparse, csv, hashlib, json, re, shutil, sys
from pathlib import Path
from collections import Counter

def load(p): return json.loads(p.read_text())
def save(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def aslist(x): return x if isinstance(x,list) else [x] if x else []
def main():
 p=argparse.ArgumentParser();p.add_argument('--project-root',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();root=a.project_root;out=a.output
 v3=root/'outputs/frontier_review_v3_2026-10-17';expanded=root/'outputs/expanded_coding_2026-10-26';swe=root/'analysis/software_engineering_2026-10-26'
 summary=load(expanded/'public_summary.json');examples=load(expanded/'public_examples.json');examples += load(root/'analysis/public_release_2026-10-26/marketing_examples.json') if (root/'analysis/public_release_2026-10-26/marketing_examples.json').exists() else [];common_annotations=load(expanded/'annotations.json');sa=load(swe/'annotations.json');ss=load(swe/'summary.json');sc=load(swe/'codebook.json')
 cbook=load(v3/'codebook.json');maps=load(v3/'competency_maps.json')['maps'];mc=load(v3/'marketing_results/codebook.json');md=load(v3/'marketing_results/data.json')
 samples={r:load(root/f'collection/openjobdata_pilot_500_2026-10-16/{r}/pilot_sample.json') for r in ['uxr','design','pm']}
 samples['marketing']=load(root/'collection/marketing_pilot_500_2026-10-17/sample.json');samples['swe']=load(root/'collection/software_engineering_2026-10-26/sample.json')
 codes={c['stable_skill_id']:c for c in cbook['competencies']}
 labels={'uxr':('UX research','UX research'),'design':('Product design','Design'),'pm':('Product management','Product management'),'marketing':('Marketing strategy & customer experience','Marketing'),'swe':('Software engineering','Software engineering')}
 scopes={'uxr':'User and UX research, including research leadership and adjacent roles retained by the pilot scope rules.','design':'Digital product, UX, interaction and related design roles.','pm':'Digital product management and product leadership.','marketing':'Marketing strategy, customer experience, channel and partner marketing, and marketing transformation. This is not all marketing.','swe':'General software engineering, including platform, data, ML, test and development leadership. AI language was not an inclusion requirement.'}
 metric_specs=[('any_ai_reference','Any AI reference','AI terms anywhere in the ad, including company and recruitment context.'),('workflow','Possible AI use in the work','Automated retrieval of passages about AI tools and occupational activities; role linkage needs review.'),('product','Possible work on AI products','Automated retrieval of AI product or system passages; employer descriptions can also trigger a match.'),('enablement','Possible AI enablement','Automated retrieval of AI adoption, tooling or enablement passages; not a confirmed duty.')]
 roles=[];annotation_index={x['record_id']:x for x in common_annotations};annotation_index.update({x['record_id']:x for x in sa})
 for r,ads in samples.items():
  n=len(ads);stats=summary['roles'].get(r);name,short=labels[r];role={'id':r,'label':name,'short_label':short,'description':scopes[r],'sample_n':n,'employer_n':len({x.get('employer') or x.get('company_name') for x in ads}),'status':'candidate','scope':scopes[r],'metrics':[],'branches':[]}
  state_counts=Counter(x.get('source_state','unknown') for x in ads);known=sum(bool(x.get('posted_at')) for x in ads)
  role['source_state_counts']=dict(state_counts);role['known_original_date_n']=known;role['unknown_original_date_n']=n-known
  role['methods_note']=f"{n:,} ads · {role['employer_n']:,} source employer names · {known} known 2026 posting dates, {n-known} unknown dates. Active and closed ads from the October 16 snapshot."
  for mid,label,note in metric_specs:
   count=ss['common_signal_counts'][mid] if r=='swe' else stats['common_signals'][mid]['n']
   role['metrics'].append({'id':mid,'label':label,'count':count,'n':n,'status':'candidate','note':note})
  if r in maps:
   branches=maps[r]['branches'];cs={s['short_id']:s for s in stats['skills']}
   for b in branches:
    branch={'id':b['id'],'title':b['title'],'description':b.get('definition',''),'skills':[]}
    for sk in b['skills']:
     cb=codes[sk['id']];stat=cs[cb['short_id']]
     item={'id':cb['stable_skill_id'],'short_id':cb['short_id'],'title':cb['title'],'definition':cb['operational_definition'],'count':stat['reviewed_positive_n'],'n':n,'status':'ai_reviewed','candidate_count':stat['candidate_n'],'facets':aslist(sk.get('facet'))+aslist(sk.get('secondary_facets')),'include_when':aslist(cb['include_when']),'exclude_when':aslist(cb['exclude_when']),'minimum_evidence':aslist(cb['minimum_evidence']),'reviewed_positive_count':stat['reviewed_positive_n'],'unreviewed_candidate_count':stat['unreviewed_candidate_n'],'reviewed_n':stats['contextually_reviewed_ads_n'],'note':f"Automated retrieval proposed {stat['candidate_n']} ad matches. Contextual AI review supports {stat['reviewed_positive_n']}; {stat['unclear_n']} remain unclear and {stat['unreviewed_candidate_n']} candidate matches await review. These counts concern retrieved passages. Unmatched text has not received an exhaustive recall audit; zero detections do not establish absence.",'evidence':[]}
     for ex in examples:
      if ex['role']==r and cb['short_id'] in ex.get('accepted_codes',[]):
       item['evidence'].append({'employer':ex['employer'],'title':ex['title'],'source_url':ex['source_url'],'context':'Analyst paraphrase: '+ex['explanation'],'status':'AI contextual review, not independent human validation'})
      if len(item['evidence'])>=2:break
     branch['skills'].append(item)
    role['branches'].append(branch)
   role['measurement_note']=f"Counts show ads with contextually supported evidence, not complete prevalence. {stats['contextually_reviewed_ads_n']} ads have contextually reviewed passages; {stats['unreviewed_candidate_ads_n']} initial candidate ads await review. Percentages are withheld because the entire cohort has not been reviewed. Open a skill for automated candidates and remaining uncertainty."
  elif r=='marketing':
   code_by={c['short_id']:c for c in mc['competencies']};counts={c['skill_id']:c for c in md['skills']}
   for b in mc['branches']:
    branch={'id':b['id'],'title':b['title'],'skills':[]}
    for sid in b['short_ids']:
     cb=code_by[sid];stat=counts[sid];item={'id':cb['stable_skill_id'],'short_id':sid,'title':cb['title'],'definition':cb['operational_definition'],'count':stat['count'],'n':n,'status':'ai_reviewed','reviewed_n':n,'facets':[],'include_when':aslist(cb['include_when']),'exclude_when':aslist(cb['exclude_when']),'minimum_evidence':aslist(cb['minimum_evidence']),'note':'Retained October marketing full-ad AI-assisted interpretation. '+stat.get('note','')+' Independent human validation remains outstanding. These reviewed counts are not directly comparable to the automated candidate counts in the software engineering map.','evidence':[]}
     for ex in examples:
      if ex['role']==r and sid in ex.get('accepted_codes',[]):
       item['evidence'].append({'employer':ex['employer'],'title':ex['title'],'source_url':ex['source_url'],'context':'Analyst paraphrase: '+ex['explanation'],'status':'Earlier AI-assisted full-ad interpretation'})
      if len(item['evidence'])>=2:break
     branch['skills'].append(item)
    role['branches'].append(branch)
   role['measurement_note']='Counts retain the earlier AI-assisted full-ad marketing review (500 ads), including knowledge and alternative qualifications where explicit. UXR, design and PM show reviewed detections without prevalence percentages; engineering shows automated candidates. Use Compare occupations for the same automated measure across all five; neither view is independently human validated.'
  else:
   public_swe=load(swe/'public_examples.json') if (swe/'public_examples.json').exists() else []
   for b in sc['branches']:
    branch={'id':b['id'],'title':b['title'],'skills':[]}
    for cb in b['skills']:
     sid=cb['short_id'];ai=cb['ai_required'];item={'id':cb['stable_skill_id'],'short_id':sid,'title':cb['title'],'definition':cb['operational_definition'],'count':ss['capability_counts'][sid],'n':n,'status':'candidate','facets':[cb.get('default_ai_facet','product')] if ai else ['foundations'],'ai_required':ai,'ai_linked_candidate_count':ss['ai_linked_capability_counts'][sid],'include_when':aslist(cb['include_when']),'exclude_when':aslist(cb['exclude_when']),'minimum_evidence':aslist(cb['minimum_evidence']),'note':f"Ng-authored category label; study-authored coding rule. {ss['ai_linked_capability_counts'][sid]} candidate ads have explicit AI language in the matched passage. "+('This category requires an AI link.' if ai else 'The headline count includes ordinary software capability. AI language nearby does not establish that AI performs the task.')+' Automated screening, not validated frequency.','evidence':[]}
     for ex in public_swe:
      if sid in ex.get('codes',[]) or sid==ex.get('short_id'):
       item['evidence'].append({'quote':ex.get('excerpt',''),'employer':ex.get('employer',''),'title':ex.get('title',''),'source_url':ex.get('source_url',''),'context':ex.get('rationale',''),'status':'AI excerpt review: '+ex.get('decision','unreviewed')+'. Not a whole-ad adjudication.'})
      if len(item['evidence'])>=2:break
     branch['skills'].append(item)
    role['branches'].append(branch)
   role['measurement_note']='Ng’s four branches include ordinary software fundamentals and product judgment as well as AI-specific work. Cards count candidate capabilities. They do not all measure AI use. Open a category for its AI-linked subset; use Compare occupations for a shared AI screen.'
  roles.append(role)
 capture=load(root/'collection/prospective_2026-10-26/latest_capture_summary.json')
 study={'title':'Changing Work','repository_url':'https://github.com/klukoff/changing-work','release':{'id':'2026-10-exploratory-v1','date':'2026-10-27','source_cutoff':'2026-10-16','baseline_label':'October 2026 baseline','status':'Exploratory release; independent validation pending','notes':'2,846 occupation-ad observations. Known original dates in 2026, with undated ads retained separately. Does not represent all current vacancies.'},'roles':roles,
 'comparison':{'note':'The same rule-based screen (common-ai-signals-2026-10-26-v1.2) is applied to all five full-ad samples. Counts are candidate text signals, not confirmed employee expectations, observed AI use, or a ranking of occupations. Company descriptions can trigger matches. Scope, employer mix, source coverage and unknown dates differ. Earlier reviewed pilot rates are not combined with this screen.','metrics':[{'id':i,'label':l,'description':note,'status':'candidate'} for i,l,note in metric_specs]},
 'methods':{'summary':'A source-bounded study of advertised expectations. We retrieve occupations without an AI keyword requirement, preserve full descriptions privately, and separate explicit role evidence from employer context. This release adds broad automated coding and partial contextual AI review; it does not complete independent human validation.',
 'steps':[{'title':'Retrieve and preserve','description':'Pin the public OpenJobData source revision. Recover the provider’s full description components, retain source identifiers and text hashes, and collapse conservative same-requisition mirrors.'},{'title':'Screen and sample','description':'Use documented occupational and US eligibility rules without selecting on AI. Draw from deterministic randomized candidate queues. Keep closed ads and unknown posting dates visible; do not treat first-seen dates as original posting dates.'},{'title':'Define and code','description':'Maintain operational definitions with inclusion and exclusion examples. Separate AI used in one’s work, AI as the product being built or studied, and enabling others. A mention is not necessarily a requirement, a duty, or hands-on expertise.'},{'title':'Audit and retain uncertainty','description':'Review proposed evidence in context, including negative and ambiguous cases. Record disagreements and missed matches. Independent human coding and a random negative-case audit are still needed before reporting validated prevalence.'}],
 'limitations':['Source-bounded, English-language retained ads; no probability sample of the US labor market.','Known dates are in 2026, but closed ads and unknown original dates are included. Collection date is not posting date.','Automatic rules can confuse employer AI products with role expectations and can miss implicit terminology.','Review coverage differs by occupation. Map candidate rates, reviewed detections and historical pilot rates are different measures.','The retained baseline includes one design ad with explicit non-US location and nine UXR ads with unresolved or conflicting location evidence. See the corroborated-US sensitivity report; these flags have not been silently removed.','Occupations, employers, seniority and specialties differ. Hybrid roles can occur across cohorts; percentages are not an occupation ranking.','Advertisements show advertised expectations, not observed workplace use, productivity, job displacement or causal change.'],
 'links':[{'label':'Full methods and decision history','url':'downloads/methods.html'},{'label':'Monitoring and taxonomy protocol','url':'downloads/monitoring-protocol.html'},{'label':'Quality and sensitivity report','url':'downloads/quality-report.json'}]},
 'downloads':[{'label':'Operational codebook','url':'downloads/codebook.json','description':'99 competencies, definitions and coding boundaries · JSON'},{'label':'Aggregate coding results','url':'downloads/skill-counts.csv','description':'Candidate counts, reviewed detections and denominators · CSV'},{'label':'Review examples','url':'downloads/review-examples.json','description':'Paraphrased positive, negative and ambiguous cases with source links · JSON'},{'label':'Full methods and choices','url':'downloads/methods.html','description':'Study development, sampling, coding and evidence limits'},{'label':'Capture manifest','url':'downloads/prospective-capture.json','description':'Separate October 26 collection, not yet an analyzed cohort'}],
 'sources':[{'label':'Andrew Ng: The AI Engineering Skills Map','url':'https://www.linkedin.com/pulse/ai-engineering-skills-map-andrew-ng-m479c/'},{'label':'Public job-ad source: OpenJobData','url':'https://huggingface.co/datasets/scholarweave/Jobs-Dataset-v2'},{'label':'Study source revision','url':'https://huggingface.co/datasets/scholarweave/Jobs-Dataset-v2/tree/d1c2b9ef39a1090caeec3868183ef578cf24a21a'},{'label':'Prior work on AI in design job advertisements','url':'https://revistas.udd.cl/index.php/BDI/en/article/view/1753'}],
 'monitoring':{'status':'baseline_and_collection_infrastructure','summary':f"One analyzed source snapshot is available. A separate October 26 capture retained {capture['candidate_versions']:,} unscreened title-candidate versions, ready for recovery and eligibility review. This is collection progress, not a second comparable month.",'note':'Keep stable headline categories and a versioned discovery layer. Preserve monthly text versions, separate new postings from updates and closures, and bridge-code category revisions. The new capture also revealed a manifest/event-count discrepancy, recorded in the download; no trend is inferred from it. Monthly automatic publication is not enabled.'}}
 study['overlap']={'note':'An analyst crosswalk of related activities, not a measure of overlap in job ads. Similar activities can serve different purposes. Follow each link for the occupation-specific rule; an empty cell indicates a gap in this working framework, not absence from the profession.','families':[
  {'label':'Build with AI assistance','roles':{'uxr':['R10'],'design':['D01'],'pm':['P10'],'marketing':['M08','M20'],'swe':['S12','S16']}},
  {'label':'Evaluate AI products and experiences','roles':{'uxr':['R13'],'design':['D13'],'pm':['P04','P06'],'marketing':['M07'],'swe':['S04']}},
  {'label':'Set oversight and safeguards','roles':{'uxr':['R06','R17'],'design':['D10','D16'],'pm':['P08','P18'],'marketing':['M17'],'swe':['S13','S14']}},
  {'label':'Create reusable AI tools','roles':{'uxr':['R05'],'design':['D06'],'pm':['P12'],'marketing':['M13'],'swe':['S03','S15']}},
  {'label':'Prepare knowledge and data for AI','roles':{'uxr':['R07'],'design':['D04'],'pm':['P13','P14'],'marketing':['M14'],'swe':['S02']}},
  {'label':'Study or lead AI adoption','roles':{'uxr':['R18'],'design':['D18'],'pm':[],'marketing':['M15','M18'],'swe':[]}}
 ]}
 # Public provenance, no description or private reviewer text.
 metadata=[]
 for r,ads in samples.items():
  for ad in ads:
   x={'role':r}
   for k in ['record_id','posting_id','canonical_posting_id','title','source_url','posted_at','first_seen_at','source_state','source_revision','analysis_text_sha256','prospective_rank','prospective_hash']:
    if k in ad:x[k]=ad[k]
   x['employer']=ad.get('employer') or ad.get('company_name');metadata.append(x)
 total_ids=len({x.get('canonical_posting_id') or x.get('posting_id') for x in metadata})
 study['release']['unique_source_postings']=total_ids
 publiccode={'version':'2026-10-99-competencies-v1','status':'Study-authored operational definitions; not independently human-validated','competencies':[]}
 for role in roles:
  for b in role['branches']:
   for skill in b['skills']:
    publiccode['competencies'].append(dict(role=role['id'],branch_id=b['id'],branch=b['title'],**{k:skill[k] for k in ['id','short_id','title','definition','include_when','exclude_when','minimum_evidence']}))
 assert sum(len(b['skills']) for r in roles for b in r['branches'])==99
 assert sum(r['sample_n'] for r in roles)==2846
 for role in roles:
  for b in role['branches']:
   for sk in b['skills']:assert 0<=sk['count']<=role['sample_n']
 save(out/'data/study.json',study);save(out/'downloads/codebook.json',publiccode);save(out/'downloads/cohort-metadata.json',metadata)
 swe_examples=load(swe/'public_examples.json') if (swe/'public_examples.json').exists() else []
 examples += [{'role':'swe','record_id':x.get('record_id'),'short_id':x.get('short_id'),'employer':x.get('employer'),'title':x.get('title'),'source_url':x.get('source_url'),'decision':x.get('decision'),'explanation':x.get('rationale'),'review_status':'AI excerpt review, not whole-ad adjudication or human validation'} for x in swe_examples]
 save(out/'downloads/review-examples.json',examples);save(out/'downloads/prospective-capture.json',capture)
 with (out/'downloads/skill-counts.csv').open('w',newline='') as f:
  fields=['role','short_id','title','count','denominator','measure','reviewed_positive_count','unreviewed_candidate_count','ai_linked_candidate_count','candidate_count'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for role in roles:
   for b in role['branches']:
    for sk in b['skills']:
     w.writerow(dict(role=role['id'],short_id=sk['short_id'],title=sk['title'],count=sk['count'],denominator=sk['n'],measure='earlier_AI_reviewed_detections' if role['id']=='marketing' else 'automated_candidates' if role['id']=='swe' else 'partial_AI_reviewed_detections',**{k:sk.get(k,'') for k in fields[6:]}))
 # Each common dimension is re-counted from annotations as an integration invariant.
 for role,ads in samples.items():
  for mid,_,_ in metric_specs:
   actual=sum(annotation_index[x['record_id']].get('common_signals',annotation_index[x['record_id']].get('common_dimensions',{}))[mid]['detected'] for x in ads)
   assert actual==next(m['count'] for r in roles if r['id']==role for m in r['metrics'] if m['id']==mid),(role,mid,actual)
 save(out/'downloads/release-validation.json',{'cohort_observations':2846,'unique_source_postings':total_ids,'competencies':99,'common_counts_recomputed':True,'private_full_text_exported':False,'prior_feedback_modified':False,'independent_human_validation':False})
 print(f'Built {len(roles)} occupations, 99 competencies, 2846 cohort observations, {total_ids} distinct source posting IDs.')
if __name__=='__main__':main()
