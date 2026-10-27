"""Transparent candidate screening, not semantic validation or measured adoption.
All offsets refer to the unchanged Unicode source string. No network dependencies.
"""
import re
VERSION = 'common-ai-signals-2026-10-26-v1.1'
AI = re.compile(r'\b(?:AI|A\.I\.|ML|LLMs?|GenAI|GPT[- ]?\d*|ChatGPT|Claude|Copilot|Cursor|Midjourney|DALL[- ]?E|Lovable|Bolt\.new|v0|Figma Make)\b|artificial intelligence|machine learning|generative (?:AI|artificial)|large language model|vibe[- ]cod', re.I)
ACTIVITY = re.compile(r'prototyp|cod(?:e|ing)|develop|implement|test(?:ing)?|debug|review|research|synthes|analy[sz]|insight|interview|survey|content|copy|creativ|campaign|design|document|specification|PRD\b|brief|localiz|segment|report|visualiz|forecast|experiment|workflow|automat|prompt|refactor|scaffold',re.I)
OWN = re.compile(r'\b(?:us(?:e|ing)|leverag\w*|appl\w*|utiliz\w*|incorporat\w*|integrat\w*|adopt\w*|experiment\w* with)\b.{0,95}(?:AI|LLM|ChatGPT|Claude|Copilot|Cursor|Midjourney|Lovable|v0\b|Figma Make)|(?:AI|LLM|Claude|Copilot|Cursor|ChatGPT|Lovable|Figma Make).{0,60}(?:assist|augment|accelerat|enhanc|streamlin|supercharg)|(?:assist|augment|accelerat|streamlin|automate).{0,70}(?:with|using|through|via).{0,25}(?:AI|LLM|Claude|Copilot|Cursor)|vibe[- ]cod|AI[- ]assisted|AI[- ]augmented|AI tools',re.I)
PRODUCT = re.compile(r'\b(?:design|build|develop|deliver|launch|own|lead|manag|evaluat|research|improv|defin|specif|shape|creat|deploy|architect)\w*\b.{0,100}(?:AI[- ](?:powered|enabled|driven|native)|AI (?:product|feature|system|experience|agent|model|application|platform)|LLM|machine learning|generative AI|conversational AI)|(?:AI|LLM|machine learning|generative).{0,45}(?:product|feature|system|experience|agent|model|application|platform).{0,70}\b(?:design|build|develop|evaluat|research|launch|roadmap|ownership)\w*',re.I)
ENABLE = re.compile(r'\b(?:train|coach|mentor|enable|educat|upskill|democratiz|teach|govern|standard|adoption|rollout)\w*|self[- ]serv|across (?:the |our )?(?:team|org)|other (?:teams|employees|people)|team.{0,30}(?:AI|agent)',re.I)
ENV = re.compile(r'generative engine optimi[sz]ation|answer engine optimi[sz]ation|AI[- ](?:search|discovery)|AI (?:search|answer) engines?|(?:GEO|AEO).{0,40}(?:AI|search|discovery)|(?:ChatGPT|Perplexity|AI Overviews).{0,80}(?:visibility|discovery|search|rank|optimi)',re.I)
ROLE = re.compile(r'\byou(?:r|\b)|responsibilit|qualificat|experience|proficien|familiar|understand|abilit|knowledge|\b(?:use|build|design|develop|lead|manage|own|evaluate|conduct|create|define|implement|support|partner|collaborate|drive|apply|leverage|ensure|optimize|deliver)\b',re.I)
RECRUIT = re.compile(r'AI.{0,90}(?:hiring process|application process|assess candidates|interview process)|(?:hiring process|application process|candidate assessment).{0,90}AI|AI[- ]generated (?:application|resume|cover letter)',re.I)

def segments(text):
    """Paragraph-level evidence units, splitting oversized paragraphs at sentence boundaries."""
    for m in re.finditer(r'[^\n]+',text):
        a,b=m.span(); raw=m.group()
        if len(raw)<1100:
            left=len(raw)-len(raw.lstrip()); right=len(raw.rstrip())
            if right>left:yield a+left,a+right,text[a+left:a+right]
        else:
            for sm in re.finditer(r'[^.!?]+(?:[.!?]+(?=\s|$)|$)',raw):
                x,y=a+sm.start(),a+sm.end(); s=text[x:y]; l=len(s)-len(s.lstrip()); rr=len(s.rstrip())
                if rr>l: yield x+l,x+rr,text[x+l:x+rr]

def common_dimensions(text):
    """High-recall relation candidates. A hit is not a confirmed expectation."""
    axes={k:[] for k in ['any_ai_reference','workflow','product','enablement','environment','recruitment_context']}
    for a,b,s in segments(text):
        if not AI.search(s) and not ENV.search(s):continue
        e={'quote':s,'start':a,'end':b,'text_field':'analysis_text'}
        axes['any_ai_reference'].append(e)
        if RECRUIT.search(s):axes['recruitment_context'].append(e);continue
        if not ROLE.search(s):continue
        if OWN.search(s) and ACTIVITY.search(s):axes['workflow'].append(e)
        if PRODUCT.search(s):axes['product'].append(e)
        if ENABLE.search(s) and (AI.search(s) or ENV.search(s)):axes['enablement'].append(e)
        if ENV.search(s):axes['environment'].append(e)
    return {k:{'detected':bool(v),'review_status':'automatic_candidate_screen','evidence':v,'interpretation':'Rule-based text signal; contextual accuracy and recall not independently validated.'} for k,v in axes.items()}
