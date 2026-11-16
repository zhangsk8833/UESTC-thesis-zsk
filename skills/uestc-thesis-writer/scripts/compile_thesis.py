import argparse, subprocess, shutil, os, re, json
from pathlib import Path

def compile_project(root,main='main.tex',engine='xelatex',allow_legacy=False):
    root=Path(root).resolve();exe=shutil.which(engine) or engine
    version=subprocess.run([exe,'--version'],capture_output=True,text=True,errors='replace',check=True).stdout
    year=re.search(r'TeX Live (\d{4})',version)
    if year and int(year[1])<2024 and not allow_legacy:raise RuntimeError('Upstream requires TeX Live >=2024; choose --engine explicitly. --allow-legacy is diagnostic only.')
    env=os.environ.copy();env['PATH']=str(Path(exe).parent)+os.pathsep+env['PATH'];logdir=root/'build';logdir.mkdir(exist_ok=True)
    stem=Path(main).stem;commands=[]
    def run(cmd):
        r=subprocess.run(cmd,cwd=root,env=env,capture_output=True,text=True,errors='replace',timeout=240)
        (logdir/f'pass-{len(commands)+1}.txt').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8');commands.append(cmd)
        if r.returncode:raise RuntimeError(f'Build failed ({r.returncode}): {cmd}; see build logs')
    args=[exe,'-interaction=nonstopmode','-halt-on-error','-file-line-error',main]
    run(args)
    aux=(root/f'{stem}.aux').read_text(encoding='utf-8',errors='replace')
    if r'\citation{' in aux:
        bib=shutil.which('bibtex',path=env['PATH']);run([bib,stem])
    nlo=root/f'{stem}.nlo'
    if nlo.exists() and nlo.stat().st_size:
        idx=shutil.which('makeindex',path=env['PATH']);run([idx,str(nlo.name),'-s','nomencl.ist','-o',stem+'.nls'])
    for _ in range(3):run(args)
    log=(root/f'{stem}.log').read_text(encoding='utf-8',errors='replace')
    problems=[x for x in log.splitlines() if re.search(r'undefined|Missing character|multiply defined|Overfull',x,re.I)]
    result={'engine':version.splitlines()[0],'legacy_diagnostic':bool(year and int(year[1])<2024),'commands':commands,'issues':problems,'pdf':stem+'.pdf','visual_review':'required'}
    (logdir/'compile-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if any(re.search(r'undefined|Missing character|multiply defined',s,re.I) for s in problems):raise RuntimeError('Unresolved references/glyphs; see compile-report.json')
    return result
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--main',default='main.tex');a.add_argument('--engine',default='xelatex');a.add_argument('--allow-legacy',action='store_true');v=a.parse_args()
    try:print(json.dumps(compile_project(v.root,v.main,v.engine,v.allow_legacy),ensure_ascii=False,indent=2))
    except Exception as e:print(str(e));raise SystemExit(1)
