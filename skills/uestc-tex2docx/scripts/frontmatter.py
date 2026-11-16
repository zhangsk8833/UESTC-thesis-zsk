"""Fill a retained UESTC professional-master cover without recreating its layout."""
import copy
from docx import Document
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn

def clean_notes(doc):
    # Word stores the same shape in Choice/Fallback; remove both representations.
    for el in list(doc.element.xpath('.//w:txbxContent')):
        text=''.join(el.itertext())
        parent=el
        while parent.getparent() is not None and parent.tag not in [qn('w:pict'),qn('w:drawing')]:parent=parent.getparent()
        if parent.getparent() is not None:parent.getparent().remove(parent)
    for el in list(doc.element.xpath('.//w:commentRangeStart|.//w:commentRangeEnd|.//w:commentReference')):
        el.getparent().remove(el)

def prepare_cover(path,meta,spec=None):
    doc=Document(path);clean_notes(doc)
    m=lambda k:meta.get(k,'')
    replacements={
        '5G移动通信基站天线关键技术及其':m('ThesisTitle'),
        '5G移动通信基站天线关键技术及其 ':m('ThesisTitle'),
        '特征模分析方法研究':'',
        '电子信息':m('DegreeCategory'),
        '2017XXXXXXXX':m('StudentID'),
        '张　某':m('StudentName'),'张某':m('StudentName'),
        '李某某':m('SupervisorName'),'教　授':m('SupervisorTitle'),
        '电子科学与工程学院':m('SchoolName'),
        'TN828.6':m('Classification'),'621.39':m('UDCValue'),
        '公开':m('SecurityLevel'),
        '通信工程（此行根据实际情况保留或删除）':m('DegreeField'),
        '2021年3月20日':m('SubmitDate'),'2021年5月20日':m('DefenseDate'),
        '2021年6月':m('GrantDate'),'章某某':m('CommitteeChair'),
        '赵某、王某某、李某、刘某、戴某某':m('Reviewers'),
        'Key Technologies and Characteristic Mode':m('ThesisTitleEn'),
        'Analysis Methods for 5G Base Station Antennas':'',
        'Electromagnetic Field and':m('DegreeCategoryEn'),'Microwave Technology':'',
        'Zhang Mou':m('StudentNameEn'),'Prof. Li Moumou':m('SupervisorEn'),
        'School of Electronic Science and Engineering':m('SchoolNameEn')}
    for p in doc.element.xpath('.//w:p'):
        ts=p.xpath('.//w:t');old=''.join(t.text or '' for t in ts);new=old
        for a,b in sorted(replacements.items(),key=lambda kv:len(kv[0]),reverse=True):new=new.replace(a,b)
        # Dates in school form may contain spaces between components.
        if '2021' in new:
            import re
            for pat,key in [(r'2021\s*年\s*3\s*月\s*20\s*日','SubmitDate'),(r'2021\s*年\s*5\s*月\s*20\s*日','DefenseDate'),(r'2021\s*年\s*6\s*月','GrantDate')]:new=re.sub(pat,m(key),new)
        if old!=new and ts:
            ts[0].text=new
            for t in ts[1:]:t.text=''
    if not m('DegreeField'):
        for row in list(doc.element.xpath('.//w:tr')):
            if '专业学位领域' in ''.join(row.itertext()):row.getparent().remove(row)
    if spec:
        declaration=Document(spec);clean_notes(declaration)
        doc.add_section(WD_SECTION.NEW_PAGE)
        elements=[]
        for el in declaration.element.body:
            text=''.join(t.text or '' for t in el.xpath('.//w:t'))
            if text.strip().replace('　','')=='摘要':break
            if el.tag==qn('w:sectPr'):break
            el=copy.deepcopy(el)
            for sect in el.xpath('.//w:sectPr'):sect.getparent().remove(sect)
            # All elements before abstract belong to the protected declaration page.
            elements.append(el)
        while elements and not ''.join(t.text or '' for t in elements[-1].xpath('.//w:t')).strip():elements.pop()
        for el in elements:
            for br in el.xpath('.//w:br[@w:type="page"]'):br.getparent().remove(br)
            doc.element.body.insert(len(doc.element.body)-1,el)
    for s in doc.sections:
        for h in [s.header,s.even_page_header,s.first_page_header,s.footer,s.even_page_footer,s.first_page_footer]:
            h.is_linked_to_previous=False
            for p in h.paragraphs:p.text=''
    return doc
