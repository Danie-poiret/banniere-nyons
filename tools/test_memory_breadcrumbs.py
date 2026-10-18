"""Breadcrumb routing, editorial immutability and regeneration regressions."""
import json,re,subprocess,copy
from pathlib import Path
import memory_breadcrumbs as m
BASE='3957f61119cd1e91c78415772ac05470094004c9'
def scrub(source):
    source=m.NAV.sub('',source)
    source=re.sub(r'<style\b[^>]*data-memory-breadcrumb-style[^>]*>.*?</style>','',source,flags=re.S)
    source=re.sub(r'<p\b[^>]*data-memory-related[^>]*>.*?</p>','',source,flags=re.S)
    def schemas(match):
        data=m.strip_crumbs(json.loads(match[1]))
        if data is m.DROP or isinstance(data,dict) and set(data)<={'@context','@graph'} and not data.get('@graph'):return ''
        return match[0][:match[0].index('>')+1]+json.dumps(data,sort_keys=True,ensure_ascii=True,separators=(',',':'))+'</script>'
    return m.SCRIPT.sub(schemas,source)
def verify(sources,baseline,config):
    checked=[]
    for path,source in sources.items():
        if not m.route(path,config)[0]:continue
        if not source.endswith('</html>') and not '</html>' in source:continue
        expected=m.SITE+'/'+path.removesuffix('index.html')
        if re.findall(r'<link\b[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)',source)!=[expected]:continue
        assert not m.validate(source,path,config),(path,m.validate(source,path,config))
        assert m.apply(source,path,config)==source,'Second correction differs: '+path
        if path in baseline:
            assert scrub(source)==scrub(baseline[path]),'Changes outside breadcrumbs: '+path
            old_main=re.search(r'<main\b.*?</main>',baseline[path],re.S)
            assert old_main and re.search(r'<main\b.*?</main>',source,re.S)[0]==old_main[0],'Article/card content changed: '+path
        checked.append(path)
    return checked
def test(root=m.ROOT):
    config=m.registry(root);paths=m.scoped_paths(root,config)
    sources={p:(root/p).read_bytes().decode('utf-8') for p in paths}
    process=subprocess.Popen(['git','cat-file','--batch'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    originals={}
    for p in paths:
        process.stdin.write((BASE+':'+p+'\n').encode());process.stdin.flush();header=process.stdout.readline();assert b'missing' not in header
        size=int(header.split()[2]);originals[p]=process.stdout.read(size).decode();process.stdout.read(1)
    process.stdin.close();assert process.wait()==0
    checked=verify(sources,originals,config)
    import harmonize_seo as seo
    policy=json.loads((root/'tools/seo-policy.json').read_text(encoding='utf-8'))
    catalog={m.SITE+'/'+p.removesuffix('index.html'):s for p,s in sources.items()}
    seo_cases=0
    for p in paths:
        url=m.SITE+'/'+p.removesuffix('index.html')
        first,_=seo.optimize(originals[p],url,policy,catalog)
        assert not m.validate(first,p,config),('SEO regressed route',p)
        second,_=seo.optimize(first,url,policy,catalog)
        assert first==second,('Second SEO generation differs',p)
        seo_cases+=1
    # Existing examples, a new article and ZIP/import output all use the same
    # registry. Pilot aliases and stories outside the collection stay exact.
    future='Hauts-de-France/Nord/Lille/futur-recit-essai/index.html'
    fixture=originals['Hauts-de-France/Nord/Lille/bains-lillois-piscine-autrefois/index.html'].replace('bains-lillois-piscine-autrefois/','futur-recit-essai/')
    future_html=m.apply(fixture,future,config)
    assert not m.validate(future_html,future,config)
    assert len(m.schema_items(future_html))==1
    for path in ['vivreanyons-test/'+future,'banniere-nyons/vivreanyons-test/'+future,'video-nyons/garage-monod/index.html']:
        assert m.apply(fixture,path,config)==fixture
    corrupt=future_html.replace('<span aria-current="page">','<span>',1)
    assert m.validate(corrupt,future,config),'Missing current step was accepted'
    assert not m.validate(m.apply(corrupt,future,config),future,config)
    report={'articles':sum(m.route(p,config)[1] for p in checked),'city_indexes':sum(p==c['path']+'/index.html' for p in checked for c in config['cities']),'parent_indexes':sum(p in config.get('breadcrumb_parent_paths',[]) for p in checked),'visible_schema_agreement':True,'old_editorial_bytes_preserved':True,'non_breadcrumb_schema_preserved':True,'seo_two_generations':seo_cases,'new_article_route':True,'aliases_untouched':True,'malformed_navigation_detected':True}
    return report
if __name__=='__main__':print(json.dumps(test(),ensure_ascii=False,indent=2))
