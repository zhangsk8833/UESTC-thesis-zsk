"""Static diagnostics. Never an AI detector or a compliance certificate."""
import argparse, json, re
from pathlib import Path
from collections import Counter
from tex_project import expand

def check(root,main,final=False):
    inv=[];text=expand(root,main,inventory=inv);findings=[]
    def add(code,severity,detail):findings.append(dict(code=code,severity=severity,detail=detail))
    labels=re.findall(r'\\label\{([^}]+)\}',text)
    for key,n in Counter(labels).items():
        if n>1:add('DUPLICATE_LABEL','error',key)
    for key in re.findall(r'\\(?:eqref|ref|autoref)\{([^}]+)\}',text):
        if key not in labels:add('MISSING_LABEL','error',key)
    bibkeys=set()
    for group in re.findall(r'\\bibliography\{([^}]+)\}',text):
        for name in group.split(','):
            p=Path(root)/name.strip();p=p if p.suffix else p.with_suffix('.bib')
            if not p.exists():add('MISSING_BIB_FILE','error',str(p));continue
            bibkeys.update(re.findall(r'@\w+\s*\{\s*([^,\s]+)',p.read_text(encoding='utf-8-sig')))
    for keys in re.findall(r'\\cite\w*(?:\[[^]]*\])*\{([^}]+)\}',text):
        for key in keys.split(','):
            if key.strip() not in bibkeys:add('MISSING_CITATION','error',key.strip())
    for p in Path(root).rglob('*.tex'):
        if any(x in p.parts for x in ['build','.git']):continue
        raw=p.read_text(encoding='utf-8-sig')
        for i,line in enumerate(raw.splitlines(),1):
            loc=f'{p.relative_to(root)}:{i}'
            if re.search(r'TODO-EVIDENCE|〔待补|待填|To be completed',line):add('UNFINISHED','error' if final else 'warning',loc)
            if '我们' in strip(line):add('AUTHOR_VOICE','warning',loc+' 校规2.1，结合上下文复核')
            if re.search('显著提升|全面解决|首次提出|填补空白',strip(line)):add('CLAIM_REVIEW','advisory',loc+' 人工检查证据和适用范围，不判定AI来源')
    return {'scope':'static only; no originality or visual compliance claim','inputs':inv,'findings':findings,'passed':not any(v['severity']=='error' for v in findings)}
def strip(s):return s.split('%',1)[0]
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--main',default='main.tex');a.add_argument('--final',action='store_true');a.add_argument('--out',required=True);v=a.parse_args()
    try:r=check(Path(v.root),v.main,v.final)
    except Exception as e:r={'passed':False,'findings':[{'code':'SOURCE_ERROR','detail':str(e)}]}
    p=Path(v.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print('PASS' if r['passed'] else 'FAIL');raise SystemExit(0 if r['passed'] else 1)
