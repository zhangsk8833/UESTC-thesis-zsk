"""Page count and blank-page gate; inspect page PNGs separately."""
import argparse,json
from pathlib import Path
import fitz

def inspect(path,print_layout=False):
 d=fitz.open(path);blank=[];broken=[]
 for i,page in enumerate(d,1):
  text=page.get_text().strip()
  if not text and not page.get_images():blank.append(i)
  if any(x in text for x in ['Error!','错误!未找到','UEQNUMBER']):broken.append(i)
 return {'pages':len(d),'blank_pages':blank,'broken_field_pages':broken,
 'passed_page_gate':not broken and (print_layout or not blank),'visual_review':'still required'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('pdf');p.add_argument('--print-layout',action='store_true');p.add_argument('--out');a=p.parse_args()
 r=inspect(a.pdf,a.print_layout);s=json.dumps(r,ensure_ascii=False,indent=2)
 if a.out:Path(a.out).write_text(s,encoding='utf-8')
 print(s);raise SystemExit(0 if r['passed_page_gate'] else 1)
