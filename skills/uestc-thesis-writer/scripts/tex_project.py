"""Small source inventory: balanced groups, explicit includes, no silent loss."""
from pathlib import Path
import re, hashlib

def strip_comments(text):
    return re.sub(r'(?m)(?<!\\)%[^\n]*', '', text)

def group(text, pos):
    while pos<len(text) and text[pos].isspace(): pos+=1
    if pos>=len(text) or text[pos]!='{': raise ValueError(f'Expected brace near {text[pos:pos+50]!r}')
    start=pos+1;depth=1;pos+=1
    while pos<len(text):
        if text[pos]=='\\': pos+=2;continue
        if text[pos]=='{':depth+=1
        if text[pos]=='}':
            depth-=1
            if depth==0:return text[start:pos],pos+1
        pos+=1
    raise ValueError('Unclosed brace')

def expand(root, main, stack=None, inventory=None):
    root=Path(root).resolve();p=Path(main)
    if not p.is_absolute():p=root/p
    if not p.suffix:p=p.with_suffix('.tex')
    p=p.resolve();stack=stack or [];inventory=inventory if inventory is not None else []
    if p in stack:raise ValueError('Circular include: '+' -> '.join(str(v) for v in stack+[p]))
    if not p.is_file():raise FileNotFoundError(p)
    raw=p.read_text(encoding='utf-8-sig');inventory.append({'path':str(p.relative_to(root)) if p.is_relative_to(root) else str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    text=strip_comments(raw)
    if re.search(r'\\(?:includeonly|if[a-zA-Z]+)\b',text):
        raise ValueError(f'Conditional/includeonly source requires an explicit export source: {p}')
    def inc(m):
        rel=m.group(1);q=root/rel
        if not q.suffix:q=q.with_suffix('.tex')
        if not q.exists():q=p.parent/rel
        return '\n'+expand(root,q,stack+[p],inventory)+'\n'
    return re.sub(r'\\(?:input|include)\s*\{([^{}]+)\}',inc,text)

def metadata(root):
    p=Path(root)/'metadata.tex'
    if not p.is_file():raise FileNotFoundError('metadata.tex is required; see migration guide')
    s=strip_comments(p.read_text(encoding='utf-8-sig'));data={}
    pat=re.compile(r'\\(?:newcommand|renewcommand)\s*\{\\([A-Za-z]+)\}')
    for m in pat.finditer(s):data[m[1]]=group(s,m.end())[0]
    return data
