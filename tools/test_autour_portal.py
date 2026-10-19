"""Focused conservation, discovery and failure tests; never edit real articles."""
from pathlib import Path
import tempfile,json,shutil,hashlib
import update_autour_portal as portal
ROOT=Path(__file__).resolve().parents[1]
def digest(root):
 return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
cfg=json.loads((ROOT/'tools/autour-nyons.json').read_text(encoding='utf8'))
with tempfile.TemporaryDirectory() as folder:
 root=Path(folder)
 for name in ['tools/autour-nyons.json','tools/templates/autour-nyons.html.tpl','a-faire-autour-de-Nyons/index.html']:
  target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
 for e in cfg['entries']:
  target=root/e['url'].lstrip('/')/'index.html';target.parent.mkdir(parents=True,exist_ok=True);target.write_text('<h1>Fixture</h1>',encoding='utf8')
 (root/'sitemap.xml').write_text('<urlset/>',encoding='utf8')
 assert len(portal.update(root))==49
 before=digest(root);portal.update(root);portal.update(root,True);assert digest(root)==before,'Second generation changed files'
 url=cfg['portal']+'nouvelle-sortie-fixture/'
 target=root/url.lstrip('/')/'index.html';target.parent.mkdir(parents=True);target.write_text('<h1>Une nouvelle randonnée</h1><link rel="canonical" href="'+portal.SITE+url+'"><meta name="description" content="Préparer une balade">',encoding='utf8')
 (root/'sitemap.xml').write_text('<urlset><url><loc>'+portal.SITE+url+'</loc></url></urlset>',encoding='utf8')
 before=digest(root);entries=portal.update(root);after=digest(root)
 assert [p for p in before if before[p]!=after[p]]==['a-faire-autour-de-Nyons/index.html'],'Generator changed another page'
 assert len(entries)==50 and entries[-1]['url']==url and entries[-1]['seasons']==[]
 assert entries[-1]['group']=='nature'
 portal.update(root,True)
 target.write_text(target.read_text(encoding='utf8')+'<meta name="robots" content="noindex">',encoding='utf8');assert len(portal.update(root))==49
 curated=portal.file_for(root,cfg['entries'][0]['url']);curated.unlink()
 try:portal.update(root)
 except ValueError as e:assert 'Missing article' in str(e)
 else:raise AssertionError('Missing original article must stop generation')
print('PASS: 47 original URLs, 49 unique guides, stable double generation, new article discovery, noindex exclusion, fail-closed and portal-only writes.')
