import json,shutil,tempfile,unittest,html
from pathlib import Path
from unittest.mock import patch
from update_loto_nyons import refresh,ROOT,PAGE

class LotoRefreshTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  for name in [PAGE,'assets/loto-nyons.js']:
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
  self.fixture=self.root/'feed.json'
  self.fixture.write_text(json.dumps({'updated_at':'2026-11-17T09:00:00Z','events':[{'title':'Loto de test','start_date':'2026-11-22','end_date':'2026-11-22','start_time':'14:00','end_time':'17:00','page_url':'https://agenda.vivreanyons.fr/evenements/loto-test-2026-11-22/','url':'https://www.nyons.com/agenda/loto/','practical':{'location_name':'Maison de Pays'}}]}),encoding='utf8')
 def page(self):return (self.root/PAGE).read_text(encoding='utf8')
 def test_snapshot_is_stable_and_article_is_preserved(self):
  original=self.page();refresh(self.root,self.fixture,'2026-11-17T12:00:00+01:00');first=self.page()
  refresh(self.root,self.fixture,'2026-11-17T12:00:00+01:00');self.assertEqual(first,self.page())
  self.assertIn('Loto de test',first)
  for phrase in ["Les lots ont beaucoup changé.","Les dates de l'édition 2027 restent à confirmer par l'association."]:
   self.assertIn(phrase,html.unescape(first))
  self.assertIn('<time datetime="2026-11-17">17 novembre 2026</time>',first)
 def test_finished_event_disappears_from_html_and_next_answer(self):
  refresh(self.root,self.fixture,'2026-11-22T17:01:00+01:00');page=self.page()
  self.assertNotIn('Loto de test',page);self.assertIn('Aucun prochain loto',page)
 def test_source_failure_removes_past_dates_and_displays_a_warning(self):
  refresh(self.root,self.fixture,'2026-11-17T12:00:00+01:00')
  with patch('update_loto_nyons.urlopen',side_effect=OSError('offline')):
   refresh(self.root,at='2026-11-23T12:00:00+01:00')
  page=self.page();self.assertNotIn('Loto de test',page);self.assertIn('momentanément indisponible',page)

if __name__=='__main__':unittest.main()
