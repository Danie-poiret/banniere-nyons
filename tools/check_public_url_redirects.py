"""Read-only live verification for the Nyons home nursing article and original photos."""
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from html.parser import HTMLParser
import json, re, struct
BASE="https://www.vivreanyons.fr/"
SLUG="sante-nyons/infirmiere-domicile-nyons/"
PREFIXES=["","vivreanyons-test/","banniere-nyons/vivreanyons-test/"]
PHOTOS={"examen-au-stethoscope.png":(203,203),"mesure-tension-a-domicile.png":(165,140),"accompagnement-patiente-agee.png":(170,168)}
URLS=[]
for prefix in PREFIXES:
    URLS += [BASE+prefix+SLUG, BASE+prefix, BASE+prefix+"sante-nyons/", BASE+prefix+"toutes-les-pages/"]
    URLS += [BASE+prefix+"assets/photos/infirmiere-domicile-nyons/"+p for p in PHOTOS]
class Parse(HTMLParser):
    def __init__(self,s):
        super().__init__(convert_charrefs=True); self.canonical=None; self.robots=None; self.images=[]; self.scripts=[]; self.capture=False; self.buf=[]; self.feed(s)
    def handle_starttag(self,t,a):
        a=dict(a)
        if t=="link" and a.get("rel")=="canonical": self.canonical=a.get("href")
        if t=="meta" and a.get("name")=="robots": self.robots=a.get("content")
        if t=="img": self.images.append(a)
        if t=="script" and a.get("type")=="application/ld+json": self.capture=True; self.buf=[]
    def handle_data(self,s):
        if self.capture: self.buf.append(s)
    def handle_endtag(self,t):
        if t=="script" and self.capture:
            self.scripts.append(json.loads("".join(self.buf))); self.capture=False
def inspect(url):
    try:
        with urlopen(Request(url,headers={"User-Agent":"VivreAnyons-publication-check/1.0","Cache-Control":"no-cache"}),timeout=25) as r:
            data=r.read(2500000); status=r.status; final=r.url
        result={"url":url,"status":status,"final_url":final}
        if url.endswith(".png"):
            name=url.rsplit("/",1)[-1]; signature=data[:8]==b"\x89PNG\r\n\x1a\n"
            dims=struct.unpack(">II",data[16:24]) if signature else None
            result.update(png=signature,dimensions=list(dims) if dims else None)
            result["ok"]=status==200 and final==url and dims==PHOTOS[name]
            return result
        s=data.decode("utf-8"); p=Parse(s)
        result.update(canonical=p.canonical,robots=p.robots)
        prefix=next((x for x in reversed(PREFIXES) if url.startswith(BASE+x)), "")
        if url==BASE+prefix+SLUG:
            graph=p.scripts[0]["@graph"]
            article=next(x for x in graph if x["@type"]=="Article")
            faq=next(x for x in graph if x["@type"]=="FAQPage")
            photos=[x for x in p.images if "/infirmiere-domicile-nyons/" in x.get("src","")]
            result.update(faq_questions=len(faq["mainEntity"]),visible_answers=s.count("<details><summary>"),photos=len(photos),published=article["datePublished"],sunday_rule="un jour sur deux pendant quinze jours" in s,reader_questions_removed='id="questions-aux-lecteurs"' not in s and "Avez-vous déjà eu besoin de soins infirmiers" not in s,sources='id="sources-et-liens-utiles"' in s,source_count=16 if s.count('<ul class="nurse-sources">')==1 and s.split('<ul class="nurse-sources">')[1].split("</ul>")[0].count("<li>")==16 else 0)
            result["contact_frames"]=s.count('data-nurse-contact="')
            result["contact_phones"]=all('href="tel:'+t+'"' in s for t in ["+33475266141","+33681650571","+33780456862","+33475270264","+33475262186"])
            result["ok"]=(result["contact_frames"]==5 and result["contact_phones"] and status==200 and final==url and p.canonical==BASE+SLUG and p.robots==("noindex,nofollow" if prefix else "index,follow") and len(faq["mainEntity"])==8 and s.count("<details><summary>")==8 and len(photos)==3 and article["datePublished"]=="2026-10-09" and result["sunday_rule"] and result["reader_questions_removed"] and result["sources"] and result["source_count"]==16)
        elif url==BASE+prefix:
            match=re.search(r'<section class="new-article"[\s\S]*?</section>',s)
            card=match.group(0) if match else ""
            result.update(featured=('data-latest-article="/'+SLUG+'"' in card),image=('/'+prefix+'assets/photos/infirmiere-domicile-nyons/examen-au-stethoscope.png' in card),title_link=('href="/'+prefix+SLUG+'"' in card))
            result["ok"]=status==200 and result["featured"] and result["image"] and result["title_link"]
        else:
            result["article_link"]='href="/'+prefix+SLUG+'"' in s
            result["ok"]=status==200 and result["article_link"]
            if url.endswith("sante-nyons/"):
                result["alzheimer_preserved"]="memoire-aidants" in s and "Alzheimer-Nyons/" in s
                result["ok"]=result["ok"] and result["alzheimer_preserved"]
        return result
    except Exception as e:
        return {"url":url,"ok":False,"error":str(e)}
def main():
    with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(inspect,URLS))
    print("PUBLIC_URL_AUDIT_BEGIN")
    print(json.dumps({"article":BASE+SLUG,"success":all(x["ok"] for x in results),"results":results},ensure_ascii=True,indent=2))
    print("PUBLIC_URL_AUDIT_END")
    raise SystemExit(0 if all(x["ok"] for x in results) else 1)
if __name__=="__main__": main()
