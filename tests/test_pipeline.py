"""Regression: preserve supported objects and fail rather than silently lose content."""
import unittest,tempfile,sys,shutil,json,argparse,os
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'skills/uestc-tex2docx/scripts'))
from convert import main,normalize,transform
from tex_project import expand,strip_comments
from validate_docx import validate
sys.path.insert(0,str(R/'skills/uestc-thesis-writer/scripts'))
from thesis_check import check

class SourceTests(unittest.TestCase):
 def test_nested_include_and_cycle(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'main.tex').write_text(r'\input{a}');(p/'a.tex').write_text('中文',encoding='utf-8')
   inv=[];self.assertIn('中文',expand(p,'main.tex',inventory=inv));self.assertEqual(len(inv),2)
   (p/'a.tex').write_text(r'\input{main}');self.assertRaises(ValueError,expand,p,'main.tex')
 def test_missing_input_fails(self):
  with tempfile.TemporaryDirectory() as tmp:self.assertRaises(FileNotFoundError,expand,tmp,'missing')
 def test_unknown_raw_and_reference_fail(self):
  for text in [r'\unknownmacro{important}',r'\ref{missing}']:
   ast={'blocks':[{'t':'Para','c':[{'t':'RawInline','c':['latex',text]}]}]}
   with self.assertRaises(ValueError):transform(ast)
 def test_complex_structures_fail(self):
  for text in [r'\begin{align}a&=b\end{align}',r'\begin{algorithm}x\end{algorithm}',r'\appendix',r'\tag{3}']:
   with self.assertRaises(ValueError):normalize(text)
 def test_final_rejects_scaffold(self):
  self.assertFalse(check(R/'thesis-template','main.tex',True)['passed'])
 def test_scaffold_draft_has_no_broken_reference(self):
  r=check(R/'thesis-template','main.tex');self.assertTrue(r['passed'],r['findings'])
 def test_duplicate_and_missing_labels(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'main.tex').write_text(r'\label{x}\label{x}\ref{y}\cite{absent}')
   codes={i['code'] for i in check(p,'main.tex')['findings']}
   self.assertTrue({'DUPLICATE_LABEL','MISSING_LABEL','MISSING_CITATION'}<=codes)

class ConversionTests(unittest.TestCase):
 def convert(self,root,out):
  main(argparse.Namespace(root=str(root),main='main.tex',out=str(out),pandoc=os.environ.get('PANDOC','pandoc'),cover=None,spec=None))
 def test_demo_content_and_formula_numbers(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'demo.docx';self.convert(R/'examples/conversion-demo',out)
   report=out.parent/'demo-conversion/report.json';data=json.loads(report.read_text(encoding='utf-8'))
   self.assertEqual(data['labels']['eq:linear'],'1-1');self.assertEqual(data['labels']['eq:cases'],'2-1')
   result=validate(out,report);self.assertTrue(result['passed_static'],result)
   self.assertEqual(result['counts']['math'],len(data['objects']['math']))
 def test_missing_image_fails(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'source';shutil.copytree(R/'examples/conversion-demo',p);(p/'diagram.png').unlink()
   with self.assertRaises(FileNotFoundError):self.convert(p,Path(tmp)/'bad.docx')
 def test_unnumbered_math_stays_unnumbered(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'main.tex').write_text(r'\begin{document}\chapter{Example}\[a=b\]\end{document}')
   (p/'metadata.tex').write_text(r'\newcommand{\ThesisTitle}{Example}')
   self.convert(p,p/'unnum.docx')
   from docx import Document
   d=Document(p/'unnum.docx');self.assertEqual(len(d.element.xpath('.//m:oMath')),1);self.assertEqual(len(d.tables),0)

if __name__=='__main__':unittest.main(verbosity=2)
