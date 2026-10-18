"""Regression checks for protected URLs, city membership and future publication."""
import hashlib,json,subprocess,sys,copy
from pathlib import Path
from lxml import html
import update_memory_cities as m

ROOT=Path(__file__).resolve().parents[1]
BASE='3c6e736195d28c0a53ea6df6d11ae7125d73a2df'

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)

def inventory():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in git('ls-files','-z').decode().split('\0') if p and (ROOT/p).is_file()}

def test():
    config=json.loads((ROOT/m.CONFIG).read_text(encoding='utf-8'))
    before=inventory();runs=[]
    for i in (1,2):
        changes,records=m.plan(ROOT);runs.append({'generation':i,'changes':sorted(changes)})
        assert not changes,'Committed city indexes differ from generator plan'
    assert inventory()==before
    nav={
        'memoire-de-france/index.html','Auvergne-Rhone-Alpes/index.html','Auvergne-Rhone-Alpes/Drome/index.html','Auvergne-Rhone-Alpes/Rhone/index.html',
        'Provence-Alpes-Cote-dAzur/index.html','Provence-Alpes-Cote-dAzur/Vaucluse/index.html','Provence-Alpes-Cote-dAzur/Bouches-du-Rhone/index.html',
        'Hauts-de-France/index.html','Hauts-de-France/Nord/index.html'}
    oldpaths=git('ls-tree','-r','--name-only',BASE).decode().splitlines()
    protected=[p for p in oldpaths if p.endswith('.html') and p not in nav]
    changed=set(git('diff','--name-only',BASE,'HEAD').decode().splitlines())
    # Check URL/canonical permanence, while allowing later, explicitly edited
    # article bodies. Generator immutability is checked by inventory() above.
    modified_protected=changed.intersection(protected)
    batch=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for path in (p for p in oldpaths if p.endswith('.html')):
        assert (ROOT/path).is_file(), 'An old URL disappeared: '+path
        batch.stdin.write((BASE+':'+path+'\n').encode());batch.stdin.flush()
        header=batch.stdout.readline();size=int(header.split()[2]);original=batch.stdout.read(size).decode('utf-8');batch.stdout.read(1)
        old_canonical=html.fromstring(original).xpath('//link[@rel="canonical"]/@href')
        current=html.fromstring((ROOT/path).read_text(encoding='utf-8')).xpath('//link[@rel="canonical"]/@href')
        assert current==old_canonical,'An old canonical changed: '+path
    batch.stdin.close();assert batch.wait()==0
    new_html=[p for p in changed if p.endswith('.html') and p not in oldpaths]
    expected_cities={c['path']+'/index.html' for c in config['cities'] if not c['existing']}
    def classify_new(paths):
        assert expected_cities<=set(paths), 'A required city index is missing'
        articles=set(paths)-expected_cities
        for path in articles:
            assert any(path.startswith(c['path']+'/') and len(path.split('/'))==5 for c in config['cities']), 'New HTML outside a city: '+path
        return articles
    new_articles=classify_new(new_html)
    counts=[]
    for c in config['cities']:
        page=html.fromstring((ROOT/(c['path']+'/index.html')).read_text(encoding='utf-8'))
        assert len(page.xpath('//h1'))==1
        canonical=page.xpath('//link[@rel="canonical"]/@href')
        assert canonical==[m.SITE+'/'+c['path']+'/']
        refs=set(page.xpath('//main//article[contains(concat(" ",normalize-space(@class)," ")," card ")]//a/@href'))
        expected={m.url(p['path']) for p in c['legacy']}
        assert expected<=refs,(c['name'],expected-refs)
        counts.append({'name':c['name'],'path':'/'+c['path']+'/','existing':c['existing'],'legacy_articles':len(c['legacy'])})
    image='/assets/photos/dames-souvenirs-20261016.webp'
    def fixture(path):
        address=m.SITE+'/'+path.removesuffix('index.html')
        return '<!doctype html><html lang="fr"><head><title>Essai technique non publié</title><meta name="description" content="Récit technique réservé à la simulation."><link rel="canonical" href="'+address+'"><script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@type':'Article','headline':'Essai technique non publié','datePublished':'2026-10-18','url':address})+'</script></head><body><h1>Essai technique non publié</h1><main><img src="'+image+'" alt="Photographie existante utilisée pour le test" width="100" height="100"><p>Récit réservé au test local.</p></main></body></html>'
    target='Provence-Alpes-Cote-dAzur/Vaucluse/Avignon/place-de-l-horloge-essai/index.html'
    updates,future=m.prepare_article(ROOT,config,'avignon','place-de-l-horloge-essai',fixture(target))
    assert classify_new(new_html+[target])==new_articles|{target}
    assert updates[target]==fixture(target)
    assert m.url(target) in updates['Provence-Alpes-Cote-dAzur/Vaucluse/Avignon/index.html']
    assert m.SITE+m.url(target) in updates['sitemap.xml']
    assert not set(updates).intersection(protected)
    c={'id':'ville-essai','name':'Ville essai','path':'Provence-Alpes-Cote-dAzur/Vaucluse/Ville-Essai','department':'Vaucluse','region':'Provence-Alpes-Côte d’Azur',
       'title':'Ville essai : carnet technique','description':'Une description réservée au test.','intro':'Introduction réservée au test et jamais publiée.'}
    target2=c['path']+'/premier-recit/index.html'
    updates2,records2=m.prepare_article(ROOT,config,c['id'],'premier-recit',fixture(target2),c)
    assert c['path']+'/index.html' in updates2 and m.CONFIG in updates2
    assert all(m.url(c['path']+'/index.html') in updates2[p] for p in ('memoire-de-france/index.html','Provence-Alpes-Cote-dAzur/index.html','Provence-Alpes-Cote-dAzur/Vaucluse/index.html'))
    assert not set(updates2).intersection(protected)
    try:m.prepare_article(ROOT,config,'avignon','../ancien',fixture(target));raise AssertionError('Traversal accepted')
    except AssertionError as error:assert 'Use a lowercase' in str(error)
    try:m.prepare_article(ROOT,config,'avignon','nouvel-article',fixture(target));raise AssertionError('Canonical mismatch accepted')
    except AssertionError as error:assert 'Canonical mismatch' in str(error)
    assert inventory()==before,'In-memory future-publication tests wrote files'
    report={'base':BASE,'protected_html_unchanged':len(protected)-len(modified_protected),'protected_html_modified_since_reference':sorted(modified_protected),'navigation_pages_changed':len(nav),'new_city_pages':len(expected_cities),'new_article_pages':len(new_articles),
            'runs':runs,'cities':counts,'future_article_routing':True,'future_city_first_article':True,'canonical_mismatch_refused':True,'path_traversal_refused':True,
            'public_deployment':False,'note':'Future articles are tested in memory only, not written or published.'}
    out=ROOT/'memory-city-evidence';out.mkdir(exist_ok=True)
    (out/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':test()
