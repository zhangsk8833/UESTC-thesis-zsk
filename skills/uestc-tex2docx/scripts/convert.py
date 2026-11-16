"""UESTC source -> Pandoc AST -> editable DOCX. Fails on unsupported raw content."""
import argparse, copy, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from io import BytesIO
from docx import Document
from docx.shared import Mm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from tex_project import expand, metadata

HERE=Path(__file__).resolve().parent; SKILL=HERE.parent
def node(t,c=None):return {'t':t,**({'c':c} if c is not None else {})}
def string(s):return node('Str',s)
def text_of(x):
    if isinstance(x,list):return ''.join(text_of(i) for i in x)
    if not isinstance(x,dict):return ''
    if x.get('t')=='Str':return x['c']
    if x.get('t') in ['Space','SoftBreak','LineBreak']:return ' '
    return text_of(x.get('c',[]))
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def run(cmd, cwd=None):
    p=subprocess.run([str(v) for v in cmd],cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    if p.returncode:raise RuntimeError(p.stderr or p.stdout)
    return p.stdout,p.stderr

def normalize(tex):
    unsupported=re.search(r'\\begin\{(align\*?|gather\*?|multline\*?|subequations|algorithm\*?|algorithmic|tikzpicture|subfigure|longtable)\}|\\(?:appendix|tag|notag|nonumber)\b',tex)
    if unsupported:raise ValueError('Structure needs a reviewed adapter: '+unsupported[0])
    # Covers are assembled separately from metadata + retained school template.
    match=re.search(r'\\zhabstract\b',tex)
    if match:tex=tex[match.start():]
    else:
        m=re.search(r'\\begin\{document\}',tex)
        if m:tex=tex[m.end():]
    tex=tex.replace(r'\end{document}','')
    for command,title in [('zhabstract','摘要'),('enabstract','ABSTRACT'),('tableofcontents','目录'),('acknowledgement','致谢')]:
        tex=re.sub(r'\\'+command+r'\b',lambda m:r'\chapter*{'+title+'}',tex)
    for command,title in [('zhkeywords','关键词：'),('enkeywords','Keywords: ')]:
        tex=re.sub(r'\\'+command+r'\{([^{}]*)\}',lambda m:'\n\n'+title+m[1]+'\n\n',tex)
    tex=re.sub(r'\\bibliography\{([^{}]+)\}',r'\\chapter*{参考文献}\n',tex)
    tex=re.sub(r'\\bibliographystyle\{[^{}]*\}','',tex)
    tex=re.sub(r'\\centering\b','',tex)
    tex=tex.replace(r'\begin{equation}',r'\begin{equation}\UESTCnumbered{}')
    return tex

def transform(ast):
    labels={};chapter=0;sections=[0,0,0];counts={'eq':0,'fig':0,'tab':0};inventory={'math':[],'images':[],'citations':[]};warnings=[]
    front={'摘要','ABSTRACT','目录'};back={'致谢','参考文献','攻读硕士学位期间取得的成果'}
    def bind(key,value):
        if key:
            if key in labels:raise ValueError('Duplicate label: '+key)
            labels[key]=value
    def scan(x):
        nonlocal chapter,sections,counts
        if isinstance(x,list):
            for y in x:scan(y)
            return
        if not isinstance(x,dict):return
        t=x.get('t');c=x.get('c')
        if t=='Header':
            level,attr,title=c;name=text_of(title)
            if level==1:
                if 'unnumbered' not in attr[1] and name not in front|back:
                    chapter+=1;sections=[0,0,0];counts={'eq':0,'fig':0,'tab':0}
                    title[:]=[string('第'+cn(chapter)+'章 '+name)];bind(attr[0],str(chapter))
            elif chapter:
                if level>4:raise ValueError('School supports at most four heading levels')
                sections[level-2]+=1
                for i in range(level-1,3):sections[i]=0
                num='.'.join(map(str,[chapter]+sections[:level-1]));bind(attr[0],num);title[:]=[string(num+' '+name)]
            return
        if t=='Math':
            kind,s=c;inventory['math'].append(s)
            if kind['t']=='DisplayMath':
                if r'\UESTCnumbered{}' not in s:
                    if r'\label{' in s:raise ValueError('Label on unnumbered formula needs explicit handling')
                    x['_eq']=None;return
                s=s.replace(r'\UESTCnumbered{}','')
                counts['eq']+=1;number=f'{chapter}-{counts["eq"]}'
                for lab in re.findall(r'\\label\{([^}]+)\}',s):bind(lab,number)
                c[1]=re.sub(r'\\label\{[^}]+\}','',s)
                x['_eq']=number
            return
        if t=='Figure':
            counts['fig']+=1;n=f'{chapter}-{counts["fig"]}';bind(c[0][0],n)
            cap=c[1][1]
            if cap and cap[0]['t'] in ['Plain','Para']:cap[0]['c'][:0]=[string('图'+n+' ')]
        if t=='Div' and c[1] and c[1][0].get('t')=='Table':
            # Attach the source table label to Table itself.
            c[1][0]['c'][0][0]=c[0][0];c[0][0]=''
        if t=='Table':
            counts['tab']+=1;n=f'{chapter}-{counts["tab"]}';bind(c[0][0],n)
            cap=c[1][1]
            if cap and cap[0]['t'] in ['Plain','Para']:cap[0]['c'][:0]=[string('表'+n+' ')]
        if t=='Image':inventory['images'].append(c[2][0])
        if t=='Cite':
            inventory['citations'].extend(y['citationId'] for y in c[0]);return
        if isinstance(c,(list,dict)):scan(c)
    scan(ast['blocks'])
    def convert(x):
        if isinstance(x,list):return [convert(y) for y in x]
        if not isinstance(x,dict):return x
        t=x.get('t');c=x.get('c')
        if t=='Cite':return x # citeproc consumes original raw command
        if t in ['RawInline','RawBlock']:
            m=re.fullmatch(r'\\(eqref|ref|autoref)\{([^}]+)\}',c[1].strip())
            if m:
                if m[2] not in labels:raise ValueError('Undefined reference: '+m[2])
                val=labels[m[2]];return string('('+val+')' if m[1]=='eqref' else val)
            if c[1].strip() in [r'\centering',r'\clearpage',r'\newpage',r'\appendix',r'\noindent']:
                return node('RawInline' if t=='RawInline' else 'RawBlock',['openxml',''])
            raise ValueError('Unsupported LaTeX node; add an explicit adapter: '+c[1][:180])
        if 'c' in x:x['c']=convert(c)
        return x
    ast['blocks']=convert(ast['blocks'])
    # A display formula becomes its own paragraph; preserve formula order and prose.
    def split_blocks(blocks):
        out=[]
        for b in blocks:
            if b['t']=='Para':
                buf=[]
                for v in b['c']:
                    if v.get('t')=='Math' and v['c'][0]['t']=='DisplayMath':
                        if buf:out.append(node('Para',buf));buf=[]
                        number=v.pop('_eq');out.append(node('Para',[v]+([string('UEQNUMBER'+number+'END')] if number else [])))
                    else:buf.append(v)
                if buf:out.append(node('Para',buf))
            else:out.append(b)
        return out
    ast['blocks']=split_blocks(ast['blocks'])
    return ast,labels,inventory,warnings

def cn(n):
    chars='零一二三四五六七八九'
    if n<10:return chars[n]
    if n<20:return '十'+(chars[n%10] if n%10 else '')
    return chars[n//10]+'十'+(chars[n%10] if n%10 else '')

def attr(parent,tag,values):
    e=parent.find(qn(tag))
    if e is None:e=OxmlElement(tag);parent.append(e)
    for k,v in values.items():e.set(qn(k),str(v))
    return e
def style_font(style,cnfont='宋体',size=12,bold=False):
    style.font.name='Times New Roman';style.font.size=Pt(size);style.font.bold=bold
    style.font.italic=False;style.font.color.rgb=RGBColor(0,0,0)
    fonts=attr(style.element.get_or_add_rPr(),'w:rFonts',{'w:eastAsia':cnfont,'w:ascii':'Times New Roman','w:hAnsi':'Times New Roman'})
    for k in list(fonts.attrib):
        if k.endswith('Theme'):del fonts.attrib[k]
def field(p,instruction,cached='更新域后显示'):
    r=OxmlElement('w:r');f=OxmlElement('w:fldChar');f.set(qn('w:fldCharType'),'begin');r.append(f);p._p.append(r)
    r=OxmlElement('w:r');i=OxmlElement('w:instrText');i.set(qn('xml:space'),'preserve');i.text=' '+instruction+' ';r.append(i);p._p.append(r)
    r=OxmlElement('w:r');f=OxmlElement('w:fldChar');f.set(qn('w:fldCharType'),'separate');r.append(f);p._p.append(r)
    p.add_run(cached)
    r=OxmlElement('w:r');f=OxmlElement('w:fldChar');f.set(qn('w:fldCharType'),'end');r.append(f);p._p.append(r)

def electronic_headers(doc):
    """Equivalent alternating text without Word's parity-forced blank pages."""
    doc.settings.odd_and_even_pages_header_footer=False
    def part(p,kind,text=None):
        r=OxmlElement('w:r');el=OxmlElement('w:'+('instrText' if kind=='text' else 'fldChar'))
        if kind=='text':el.text=text;el.set(qn('xml:space'),'preserve')
        else:el.set(qn('w:fldCharType'),kind)
        r.append(el);p._p.append(r)
    for s in doc.sections:
        pg=s._sectPr.find(qn('w:pgNumType'))
        if pg is None or pg.get(qn('w:fmt'))!='decimal':continue
        p=s.header.paragraphs[0];title=p.text.replace('"','');p.text=''
        part(p,'begin');part(p,'text',' IF ')
        part(p,'begin');part(p,'text',' = MOD(')
        field(p,'PAGE','1');part(p,'text',',2) ');part(p,'separate');p.add_run('1');part(p,'end')
        part(p,'text',' = 0 "电子科技大学硕士学位论文" "'+title+'" ')
        part(p,'separate');p.add_run(title);part(p,'end')
        for r in p.runs:r.font.size=Pt(10.5)

def footnote_layout(doc):
    from lxml import etree
    for rel in doc.part.rels.values():
        if not rel.reltype.endswith('/footnotes'):continue
        root=etree.fromstring(rel.target_part.blob)
        for note in root:
            if note.get(qn('w:type')):continue
            for p in note.findall('.//'+qn('w:p')):
                pp=attr(p,'w:pPr',{});attr(pp,'w:spacing',{'w:line':240,'w:lineRule':'auto'})
                attr(pp,'w:ind',{'w:left':270,'w:hanging':270,'w:firstLineChars':0});attr(pp,'w:jc',{'w:val':'both'})
                for r in p.findall(qn('w:r')):
                    rp=attr(r,'w:rPr',{});attr(rp,'w:sz',{'w:val':18});attr(rp,'w:vertAlign',{'w:val':'baseline'})
                    attr(rp,'w:rFonts',{'w:eastAsia':'宋体','w:ascii':'Times New Roman','w:hAnsi':'Times New Roman'})
        rel.target_part._blob=etree.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
def set_section(s,title,fmt,start=None,body=False):
    s.start_type=WD_SECTION.NEW_PAGE
    s.page_width=Mm(210);s.page_height=Mm(297)
    s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Mm(30)
    s.header_distance=s.footer_distance=Mm(20);s.different_first_page_header_footer=False
    values={'w:fmt':fmt}
    if start is not None:values['w:start']=start
    else:
        old=s._sectPr.find(qn('w:pgNumType'))
        if old is not None:old.attrib.pop(qn('w:start'),None)
    attr(s._sectPr,'w:pgNumType',values)
    if body:
        for old in s._sectPr.findall(qn('w:footnotePr')):s._sectPr.remove(old)
        notes=OxmlElement('w:footnotePr');s._sectPr.insert(0,notes)
        attr(notes,'w:numFmt',{'w:val':'decimalEnclosedCircle'});attr(notes,'w:numRestart',{'w:val':'eachPage'})
    for header,value in [(s.header,title),(s.even_page_header,'电子科技大学硕士学位论文' if body else title)]:
        header.is_linked_to_previous=False;p=header.paragraphs[0];p.text=value;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent=Pt(0)
        for run_ in p.runs:run_.font.size=Pt(10.5)
        border=attr(p._p.get_or_add_pPr(),'w:pBdr',{});attr(border,'w:bottom',{'w:val':'single','w:sz':6,'w:space':1,'w:color':'000000'})
    for footer in [s.footer,s.even_page_footer]:
        footer.is_linked_to_previous=False;p=footer.paragraphs[0];p.text='';p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Pt(0);field(p,'PAGE','1')
        for run_ in p.runs:run_.font.size=Pt(9)

def format_doc(doc,profile):
    normal=doc.styles['Normal'];style_font(normal)
    pf=normal.paragraph_format;pf.line_spacing=Pt(20);pf.first_line_indent=Pt(24);pf.space_before=pf.space_after=Pt(0);pf.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    for name in ['Body Text','First Paragraph','Compact']:
        if name in doc.styles:
            st=doc.styles[name];style_font(st);st.paragraph_format.line_spacing=Pt(20);st.paragraph_format.first_line_indent=Pt(24);st.paragraph_format.space_after=Pt(0)
    for n in range(1,5):
        st=doc.styles[f'Heading {n}'];r=profile['headings'][str(n)];style_font(st,'黑体',r['pt']);p=st.paragraph_format
        p.space_before=Pt(r['before']);p.space_after=Pt(r['after']);p.first_line_indent=Pt(0);p.line_spacing=Pt(20);p.keep_with_next=True;p.page_break_before=False;p.alignment=WD_ALIGN_PARAGRAPH.CENTER if n==1 else WD_ALIGN_PARAGRAPH.LEFT
    for name in ['Caption','Image Caption','Table Caption','Bibliography']:
        if name in doc.styles:style_font(doc.styles[name],size=10.5)
    doc.settings.odd_and_even_pages_header_footer=True
    for s in doc.sections:set_section(s,'摘要','upperRoman',1)
    # Assign section boundaries by moving newly created sectPr paragraphs to headings.
    headings=[p for p in doc.paragraphs if p.style.name=='Heading 1'];body_started=False;last_title='摘要';first=True
    for p in headings:
        title=p.text
        if not first:
            s=doc.add_section(WD_SECTION.NEW_PAGE);br=doc.element.body[-2];p._p.addprevious(br)
        first=False
        if title.startswith('第一章'):body_started=True
        last_title=title
    # Each section's properties live at its end; sections now appear in document order.
    for s,p in zip(doc.sections,headings):
        title=p.text;body=title not in ['摘要','ABSTRACT','目录'];start=1 if title in ['摘要'] or title.startswith('第一章') else None
        set_section(s,title,'decimal' if body else 'upperRoman',start,body)
    # front headings must not enter TOC; ordinary headings are already numbered.
    from docx.enum.style import WD_STYLE_TYPE
    if 'Front Heading' not in doc.styles:
        st=doc.styles.add_style('Front Heading',WD_STYLE_TYPE.PARAGRAPH);st.base_style=doc.styles['Heading 1'];attr(st.element.get_or_add_pPr(),'w:outlineLvl',{'w:val':9})
    for p in doc.paragraphs:
        if p.text in ['摘要','ABSTRACT','目录']:
            p.style=doc.styles['Front Heading']
            if p.text=='目录':
                q=doc.add_paragraph();p._p.addnext(q._p);field(q,'TOC \\o "1-3" \\h \\z \\u')
        if p.text.startswith(('关键词：','Keywords:')):p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(20)
        if p.text.startswith('式中'):p.paragraph_format.first_line_indent=Pt(0)
        if p.style.name in ['Image Caption','Table Caption','Caption']:
            p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1;p.paragraph_format.keep_together=True
            # Exact wrapping is reviewed after Word pagination; this is a conservative estimate.
            long=sum(2 if ord(c)>127 else 1 for c in p.text)>80
            p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY if long else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.left_indent=p.paragraph_format.right_indent=Pt(42) if long else Pt(0)
            is_table=p.text.startswith('表');p.paragraph_format.space_before=Pt(12 if is_table else 6);p.paragraph_format.space_after=Pt(6 if is_table else 12);p.paragraph_format.keep_with_next=is_table
        if p._p.xpath('.//w:drawing'):
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=True
        if p.style.name=='Bibliography':
            p.paragraph_format.left_indent=Pt(21);p.paragraph_format.first_line_indent=Pt(-21);p.paragraph_format.keep_together=True;p.paragraph_format.line_spacing=Pt(20)
        if p.style.name.startswith('Heading'):
            prev=p._p.getprevious()
            if prev is not None and prev.tag==qn('w:p'):
                st=prev.find('w:pPr/w:pStyle',namespaces=prev.nsmap)
                if st is not None and st.get(qn('w:val'),'').startswith('Heading'):p.paragraph_format.space_before=Pt(0)
    for table in doc.tables:
        table.autofit=False
        borders=attr(table._tbl.tblPr,'w:tblBorders',{})
        if table._tbl.xpath('.//w:drawing'):
            for side in ['top','bottom','left','right','insideH','insideV']:attr(borders,'w:'+side,{'w:val':'nil'})
            for p in table._tbl.xpath('.//w:p'):
                pp=attr(p,'w:pPr',{});attr(pp,'w:ind',{'w:firstLine':0});attr(pp,'w:jc',{'w:val':'center'})
                attr(pp,'w:spacing',{'w:line':240,'w:lineRule':'auto'})
            continue
        for side in ['top','bottom']:attr(borders,'w:'+side,{'w:val':'single','w:sz':12,'w:color':'000000'})
        for side in ['left','right','insideH','insideV']:attr(borders,'w:'+side,{'w:val':'nil'})
        if table.rows:
            attr(table.rows[0]._tr.get_or_add_trPr(),'w:tblHeader',{'w:val':'true'})
            for cell in table.rows[0].cells:attr(attr(cell._tc.get_or_add_tcPr(),'w:tcBorders',{}),'w:bottom',{'w:val':'single','w:sz':6})
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1
                    for r in p.runs:r.font.size=Pt(10.5)
    # Convert display formula paragraphs into a fixed-width borderless layout.
    for p in list(doc.paragraphs):
        m=re.search(r'UEQNUMBER([\d-]+)END',p.text)
        if not m:continue
        math=p._p.xpath('.//m:oMath');formula_p=p._p
        if not math:
            previous=p._p.getprevious()
            if previous is not None and previous.tag==qn('w:p'):
                math=previous.xpath('.//m:oMath');formula_p=previous
        if not math:raise ValueError('Formula did not become OMML: '+m[1])
        table=doc.add_table(rows=1,cols=3);table.autofit=False
        attr(table._tbl.tblPr,'w:tblCaption',{'w:val':'UESTC equation layout'})
        borders=attr(table._tbl.tblPr,'w:tblBorders',{})
        for side in ['top','bottom','left','right','insideH','insideV']:attr(borders,'w:'+side,{'w:val':'nil'})
        for i,width in enumerate([20,110,20]):table.columns[i].width=Mm(width);table.cell(0,i).width=Mm(width)
        mid=table.cell(0,1).paragraphs[0];mid.alignment=WD_ALIGN_PARAGRAPH.CENTER;mid.paragraph_format.first_line_indent=Pt(0);mid.paragraph_format.line_spacing=1
        for mo in math:mid._p.append(copy.deepcopy(mo))
        num=table.cell(0,2).paragraphs[0];num.text='('+m[1]+')';num.alignment=WD_ALIGN_PARAGRAPH.RIGHT;num.paragraph_format.first_line_indent=Pt(0)
        for cell in table.rows[0].cells:
            from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cb=attr(cell._tc.get_or_add_tcPr(),'w:tcBorders',{})
            for side in ['top','bottom','left','right']:attr(cb,'w:'+side,{'w:val':'nil'})
            for para in cell.paragraphs:
                para.style=doc.styles['Normal'];para.paragraph_format.line_spacing=1
                attr(para._p.get_or_add_pPr(),'w:ind',{'w:left':0,'w:right':0,'w:firstLine':0,'w:firstLineChars':0})
        formula_p.addprevious(table._tbl)
        if formula_p is not p._p:formula_p.getparent().remove(formula_p)
        p._p.getparent().remove(p._p)
    attr(doc.settings.element,'w:updateFields',{'w:val':'true'})

def merge_body(base, incoming):
    """Compose with isolated body styles; recreate section furniture after import."""
    from docxcompose.composer import Composer
    section_specs=[]
    for section in incoming.sections:
        pg=section._sectPr.find(qn('w:pgNumType'))
        section_specs.append((section.header.paragraphs[0].text,
            pg.get(qn('w:fmt')),pg.get(qn('w:start'))))
    # Prevent the cover's Normal/Heading styles from changing body typography,
    # and prevent body styles from changing the protected school cover.
    mapping={st.style_id:'UESTC'+st.style_id for st in incoming.styles}
    for p in incoming.element.xpath('.//w:p'):
        if p.find('w:pPr/w:pStyle',namespaces=p.nsmap) is None:
            attr(attr(p,'w:pPr',{}),'w:pStyle',{'w:val':'Normal'})
    for st in incoming.styles:
        st.element.attrib.pop(qn('w:default'),None)
        st.element.set(qn('w:styleId'),mapping[st.style_id])
        name=st.element.find(qn('w:name'))
        if name is not None:name.set(qn('w:val'),'UESTC '+name.get(qn('w:val')))
    for root in [incoming.styles.element,incoming.element,incoming.part.numbering_part.element]:
        for el in root.iter():
            if el.tag in [qn('w:'+t) for t in ['basedOn','next','link','pStyle','rStyle','tblStyle']]:
                val=el.get(qn('w:val'))
                if val in mapping:el.set(qn('w:val'),mapping[val])
    prefix_count=len(base.sections)
    base.add_section(WD_SECTION.NEW_PAGE)
    composer=Composer(base);composer.append(incoming)
    body_sections=list(base.sections)[prefix_count:]
    if len(body_sections)!=len(section_specs):
        raise ValueError('Section count changed during composition')
    for section,(title,fmt,start) in zip(body_sections,section_specs):
        set_section(section,title,fmt,start,fmt=='decimal')
    base.settings.odd_and_even_pages_header_footer=True
    attr(base.settings.element,'w:updateFields',{'w:val':'true'})
    notes=attr(base.settings.element,'w:footnotePr',{})
    attr(notes,'w:numFmt',{'w:val':'decimalEnclosedCircle'});attr(notes,'w:numRestart',{'w:val':'eachPage'})
    return base

def main(args):
    root=Path(args.root).resolve();out=Path(args.out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    report={'status':'failed','source':args.main,'limitations':[]};work=out.parent/(out.stem+'-conversion');work.mkdir(exist_ok=True)
    try:
        inventory=[];tex=expand(root,args.main,inventory=inventory);meta=metadata(root)
        normalized=normalize(tex)
        macros=(root/'macros.tex').read_text(encoding='utf-8-sig') if (root/'macros.tex').exists() else ''
        (work/'normalized.tex').write_text(macros+'\n'+normalized,encoding='utf-8')
        pandoc=shutil.which(args.pandoc) or args.pandoc
        s,warn=run([pandoc,'-f','latex+raw_tex','-t','json',work/'normalized.tex'],root);ast=json.loads(s)
        ast,labels,objects,warnings=transform(ast)
        (work/'semantic.json').write_text(json.dumps(ast,ensure_ascii=False),encoding='utf-8')
        # Explicitly resolve image paths; missing resources are fatal, not placeholder images.
        for n in walk(ast):
            if n.get('t')=='Image':
                source=n['c'][2][0];p=root/source
                candidates=[p,root/'fig'/source,root/'figures'/source]
                if not p.suffix:candidates=[q.with_suffix(ext) for q in candidates for ext in ['.png','.jpg','.jpeg','.pdf','.svg']]
                found=next((q for q in candidates if q.is_file()),None)
                if not found:raise FileNotFoundError('Missing image: '+source)
                if found.suffix.lower()=='.pdf':
                    import fitz
                    pdf=fitz.open(found);image=work/(found.stem+'.png');pdf[0].get_pixmap(matrix=fitz.Matrix(3,3)).save(image);found=image
                    warnings.append('PDF figure rasterized at 216 dpi: '+source)
                n['c'][2][0]=str(found.resolve())
        (work/'semantic.json').write_text(json.dumps(ast,ensure_ascii=False),encoding='utf-8')
        cmd=[pandoc,work/'semantic.json','-f','json','-t','docx','-o',work/'body.docx','--standalone']
        if objects['citations']:
            bibs=re.findall(r'\\bibliography\{([^}]+)\}',tex)
            if not bibs:raise ValueError('Citations require bibliography source')
            for entry in bibs:
                for file in entry.split(','):
                    p=root/file.strip();p=p if p.suffix else p.with_suffix('.bib')
                    if not p.is_file():raise FileNotFoundError(p)
                    cmd+=['--bibliography',p]
            cmd+=['--citeproc','--csl',SKILL/'assets/gb7714-2015.csl']
        _,stderr=run(cmd,root)
        if re.search(r'not found|Could not|Couldn.t|not convert|missing',stderr,re.I):raise ValueError('Pandoc warning needs attention: '+stderr)
        warnings.extend([v for v in [warn,stderr] if v.strip()])
        doc=Document(work/'body.docx');profile=json.loads((SKILL/'references/school-profile/rules.json').read_text(encoding='utf-8'))
        format_doc(doc,profile)
        if args.cover:
            from frontmatter import prepare_cover
            cover=prepare_cover(Path(args.cover),meta,Path(args.spec) if args.spec else None)
            doc=merge_body(cover,doc)
        else:report['limitations'].append('No school cover supplied: body-only output')
        if not getattr(args,'print_layout',False):electronic_headers(doc)
        footnote_layout(doc)
        report['layout']='print' if getattr(args,'print_layout',False) else 'electronic-conditional-headers'
        doc.save(out)
        report.update(status='generated-needs-visual-review',source_inventory=inventory,source_metadata=meta,labels=labels,objects=objects,warnings=warnings,profile_version=profile['version'])
        report['limitations']+=['Word fields must be refreshed and all pages inspected','Long captions and continuation-table captions need pagination review','Cross-references are resolved static numbers; edit LaTeX and re-export','Print blank-backside handling is not automatic; electronic DOCX only']
    except Exception as e:
        report['error']=str(e);raise
    finally:
        (work/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--main',default='main.tex');p.add_argument('--out',required=True);p.add_argument('--pandoc',default='pandoc');p.add_argument('--cover');p.add_argument('--spec');p.add_argument('--print-layout',action='store_true');a=p.parse_args()
    try:main(a)
    except Exception as e:print('Conversion failed: '+str(e),file=sys.stderr);sys.exit(1)
