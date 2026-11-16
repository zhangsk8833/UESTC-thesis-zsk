"""Content + parameter checks. Visual inspection is a separate mandatory gate."""
import argparse,json,re,zipfile
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn

def validate(path,report=None):
    d=Document(path);issues=[];root=d.element
    def fail(code,detail):issues.append({'code':code,'detail':detail})
    alltext=''.join(n.text or '' for n in root.xpath('.//w:t'))
    if re.search(r'UEQNUMBER|\\(?:frac|begin|label|ref|cite)\b',alltext):fail('RAW_TEX','Unconverted LaTeX or equation marker')
    if 'Error! Reference source not found' in alltext or '错误!未找到' in alltext:fail('BROKEN_FIELD','Broken Word field')
    math=root.xpath('.//m:oMath');images=root.xpath('.//w:drawing//a:blip');tables=d.tables
    if report:
        source=json.loads(Path(report).read_text(encoding='utf-8'))
        expected=len(source.get('objects',{}).get('math',[]))
        if len(math)<expected:fail('MATH_LOSS',f'Expected >= {expected} math objects, got {len(math)}')
        expected_images=len(source.get('objects',{}).get('images',[]))
        if len(images)<expected_images:fail('IMAGE_LOSS',f'Expected >= {expected_images} images')
        for key,num in source.get('labels',{}).items():
            if num not in alltext:fail('NUMBER_LOSS',key+': '+num)
    for i,s in enumerate(d.sections):
        if abs(s.page_width.mm-210)>1 or abs(s.page_height.mm-297)>1:fail('PAPER',str(i))
        # Original fixed cover pages are not forced through body paragraph settings.
        if i and any(abs(v.mm-30)>0.6 for v in [s.top_margin,s.bottom_margin,s.left_margin,s.right_margin]):fail('MARGINS',str(i))
    if not d.settings.odd_and_even_pages_header_footer:
        conditional=any('MOD(' in ''.join(s.header._element.itertext()) for s in d.sections)
        if not conditional:fail('ODD_EVEN','Neither separate headers nor electronic conditional headers found')
    for name in ['UESTC Normal','Normal']:
        if name in d.styles:
            st=d.styles[name]
            size=st.font.size.pt if st.font.size is not None else None
            parent=st.base_style
            while size is None and parent is not None:
                size=parent.font.size.pt if parent.font.size is not None else None;parent=parent.base_style
            if size is None:
                default=d.styles.element.find('w:docDefaults/w:rPrDefault/w:rPr/w:sz',namespaces=d.styles.element.nsmap)
                if default is not None:size=int(default.get(qn('w:val')))/2
            if size is None or abs(size-12)>0.1:fail('BODY_SIZE',name)
            if st.paragraph_format.line_spacing is None or abs(st.paragraph_format.line_spacing.pt-20)>0.1:fail('BODY_SPACING',name)
            break
    for table in tables:
        cap=table._tbl.tblPr.find(qn('w:tblCaption'))
        if cap is not None and cap.get(qn('w:val'))=='UESTC equation layout':
            if len(table.columns)!=3 or not table.cell(0,1)._tc.xpath('.//m:oMath'):fail('EQUATION_LAYOUT','No editable formula in middle cell')
            if not re.fullmatch(r'\(\d+-\d+\)',table.cell(0,2).text):fail('EQUATION_NUMBER',table.cell(0,2).text)
    for p in d.paragraphs:
        if 'Heading' in p.style.name and p.paragraph_format.keep_with_next is False:fail('HEADING_KEEP',p.text)
    result={'passed_static':not issues,'issues':issues,'counts':{'math':len(math),'images':len(images),'tables':len(tables),'sections':len(d.sections)},'visual_status':'not assessed by this script','not_checked':['semantic equivalence of formulas','caption wrapping','table continuation captions','actual page fields','all-page visual review']}
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--docx',required=True);p.add_argument('--report');p.add_argument('--out');a=p.parse_args();r=validate(a.docx,a.report)
    s=json.dumps(r,ensure_ascii=False,indent=2)
    if a.out:Path(a.out).write_text(s,encoding='utf-8')
    print(s);raise SystemExit(0 if r['passed_static'] else 1)
