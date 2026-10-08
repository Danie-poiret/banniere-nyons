"""Verify shared navigation and analytics consent without sending visits to Google."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse,unquote
import argparse,json,mimetypes,re,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE="https://www.vivreanyons.fr"
ID="G-X0T2SGWSWX"
KEY="vivreanyons:privacy:v1"
PUBLIC=argparse.ArgumentParser()
PUBLIC.add_argument("--public",action="store_true")
args=PUBLIC.parse_args()
def read(url):
    with urlopen(Request(url,headers={"User-Agent":"VivreAnyons-implementation-check/1.0"}),timeout=25) as response:
        assert response.status==200
        return response.read().decode("utf-8")
if args.public:
    for attempt in range(18):
        try:
            source=read(BASE+"/assets/agenda.js?v=google-analytics-20261008-v1")
            home=read(BASE+"/")
            if "const ANALYTICS_ID='"+ID+"'" in source and 'data-nyons-shortcut="hebergement"' in home and "google-analytics-20261008-v1" in home:break
        except Exception:pass
        print("Waiting for shared tag and direct lodging link:",attempt+1,flush=True)
        time.sleep(10)
    else:raise AssertionError("The Google tag and lodging navigation are not deployed")
PREFIXES=("", "/vivreanyons-test", "/banniere-nyons/vivreanyons-test")
for prefix in PREFIXES:
    js=read(BASE+prefix+"/assets/agenda.js?v=google-analytics-20261008-v1") if args.public else (ROOT/(prefix.lstrip("/")+"/assets/agenda.js").lstrip("/")).read_text()
    policy=read(BASE+prefix+"/cookies/") if args.public else (ROOT/(prefix.lstrip("/")+"/cookies/index.html").lstrip("/")).read_text()
    assert js.count("window.gtag('config',ANALYTICS_ID,")==1
    assert "const ANALYTICS_ID='"+ID+"'" in js and 'name="analytics"' in js
    assert "allow_google_signals:false" in js and "allow_ad_personalization_signals:false" in js
    assert "15552000" in js and "cookie_update:false" in js
    assert "Google Analytics "+ID in policy and "180 jours" in policy and "ne contient pas d’outil de mesure" not in policy
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
if args.public:
    google_library=read("https://www.googletagmanager.com/gtag/js?id="+ID)
    check("Google tag library is available for the supplied measurement ID",len(google_library)>1000 and ID in google_library)
def source_path(path):
    clean=unquote(path).lstrip("/")
    target=ROOT/clean
    if path.endswith("/") or not target.suffix:target=target/"index.html"
    return target
with sync_playwright() as p:
    browser=p.chromium.launch()
    def context(saved=None,width=1280):
        ctx=browser.new_context(viewport={"width":width,"height":900})
        calls=[]
        errors=[]
        def route(r):
            u=urlparse(r.request.url)
            if u.hostname=="www.googletagmanager.com" and u.path=="/gtag/js":
                calls.append(r.request.url)
                assert "id="+ID in u.query
                r.fulfill(status=200,content_type="application/javascript",body="window.__tagTestLoads=(window.__tagTestLoads||0)+1;")
            elif u.hostname in ("www.vivreanyons.fr","vivreanyons.fr"):
                if args.public:r.continue_()
                else:
                    target=source_path(u.path)
                    if target.is_file():
                        kind=mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                        r.fulfill(status=200,content_type=kind,body=target.read_bytes())
                    else:r.fulfill(status=404,body="not found")
            elif "google-analytics.com" in (u.hostname or ""):
                raise AssertionError("Verification must never send visits to Analytics")
            elif "raw.githubusercontent.com"==u.hostname:
                if u.path.endswith(".json"):r.fulfill(status=200,content_type="application/json",body='{"events":[]}')
                elif u.path.endswith(".xml"):r.fulfill(status=200,content_type="application/xml",body="<urlset/>")
                else:r.fulfill(status=200,content_type="text/html",body="<html></html>")
            else:r.fulfill(status=200,content_type="text/html",body="<html></html>")
        ctx.route("**/*",route)
        if saved is not None:ctx.add_init_script("localStorage.setItem("+json.dumps(KEY)+","+json.dumps(json.dumps(saved))+");")
        page=ctx.new_page()
        page.on("pageerror",lambda error:errors.append(str(error)))
        return ctx,page,calls,errors
    def visit(page,path="/"):
        page.goto(BASE+path,wait_until="domcontentloaded")
        page.locator("[data-privacy-panel]").wait_for(state="attached")
        page.wait_for_timeout(150)
    def settings(page):
        panel=page.locator("[data-privacy-panel]")
        if panel.is_visible():
            if not page.locator("#privacy-options").is_visible():
                panel.locator('[data-privacy-action="configure"]').click()
        else:
            page.get_by_role("button",name="Gérer mes cookies",exact=True).click()
    def analytics_only(page,enabled=True):
        settings(page)
        for name in ("videos","facebook","maps"):page.locator("input[name="+name+"]").uncheck()
        page.locator('input[name="analytics"]').set_checked(enabled)
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"),"Open cookie controls overflow horizontally"
        page.get_by_role("button",name="Enregistrer mes choix",exact=True).click()
        if enabled and not "/vivreanyons-test" in page.url:page.wait_for_function("window.__tagTestLoads===1")
        page.wait_for_timeout(100)
    def queue(page):
        return page.evaluate("Array.from(window.dataLayer||[], entry=>Array.from(entry))")
    def configs(page):
        return [x for x in queue(page) if x[0]=="config"]
    def no_google(page,calls):
        return not calls and page.locator("script[data-nyons-analytics]").count()==0 and not page.evaluate("document.cookie.includes('_ga=')")
    future=int(time.time()*1000)+3600000
    ctx,page,calls,errors=context()
    visit(page,"/que-faire-nyons/nyons-quand-il-pleut/?test-query=private#test-fragment")
    check("No Google request before a choice",no_google(page,calls))
    check("Analytics is initially unchecked",not page.locator('input[name="analytics"]').is_checked())
    page.get_by_role("button",name="Refuser",exact=True).click()
    check("Rejecting never loads Google",no_google(page,calls))
    page.reload(wait_until="domcontentloaded")
    page.wait_for_timeout(150)
    check("Refusal is remembered",no_google(page,calls) and not page.locator("[data-privacy-panel]").is_visible())
    analytics_only(page)
    config=configs(page)
    check("Analytics-only consent loads one correct tag",len(calls)==1 and len(config)==1 and config[0][1]==ID)
    q=queue(page)
    check("Consent is set before configuration",q[0][:2]==["consent","default"] and q[1][:2]==["consent","update"] and q[0][2]["analytics_storage"]=="denied" and q[1][2]["analytics_storage"]=="granted")
    check("Advertising remains denied",all(q[1][2][k]=="denied" for k in ("ad_storage","ad_user_data","ad_personalization")))
    check("Advertising features are disabled",config[0][2]["allow_google_signals"] is False and config[0][2]["allow_ad_personalization_signals"] is False)
    check("Analytics cookies expire after 180 days",config[0][2]["cookie_expires"]==15552000 and config[0][2]["cookie_update"] is False)
    check("Queries and fragments are not sent as page URLs",config[0][2]["page_location"]==BASE+"/que-faire-nyons/nyons-quand-il-pleut/")
    check("Analytics does not authorize videos or maps",page.evaluate("JSON.parse(localStorage.getItem("+json.dumps(KEY)+")).videos===false&&JSON.parse(localStorage.getItem("+json.dumps(KEY)+")).maps===false&&JSON.parse(localStorage.getItem("+json.dumps(KEY)+")).facebook===false"))
    settings(page)
    page.get_by_role("button",name="Enregistrer mes choix",exact=True).click()
    check("Repeated consent does not duplicate initialization",len(calls)==1 and len(configs(page))==1)
    page.evaluate("document.cookie='_ga=test; path=/; Secure';document.cookie='_ga_X0T2SGWSWX=test; path=/; domain=www.vivreanyons.fr; Secure'")
    analytics_only(page,False)
    check("Withdrawing disables further measurement",page.evaluate("window['ga-disable-"+ID+"']===true"))
    check("Withdrawing removes accessible Analytics cookies",not page.evaluate("document.cookie.includes('_ga=')||document.cookie.includes('_ga_X0T2SGWSWX=')"))
    analytics_only(page,True)
    check("Reaccepting does not duplicate this page",len(calls)==1 and len(configs(page))==1)
    page2=ctx.new_page()
    visit(page2,"/que-faire-nyons/nyons-avec-des-enfants/")
    page2.wait_for_function("window.__tagTestLoads===1")
    check("Consent is remembered on another article",len(calls)==2 and len(configs(page2))==1)
    analytics_only(page,False)
    page2.wait_for_function("window['ga-disable-"+ID+"']===true")
    check("Withdrawal is propagated to another tab",page2.evaluate("window['ga-disable-"+ID+"']===true"))
    check("No JavaScript runtime errors",not errors)
    ctx.close()
    old={"version":1,"videos":True,"maps":True,"facebook":False,"expires":future}
    ctx,page,calls,errors=context(old)
    visit(page,"/que-faire-nyons/nyons-quand-il-pleut/")
    check("Old video consent does not grant Analytics",no_google(page,calls))
    check("Old preferences trigger a new Analytics choice",page.locator("[data-privacy-panel]").is_visible())
    settings(page)
    check("Previous video and map choices are preserved",page.locator('input[name="videos"]').is_checked() and page.locator('input[name="maps"]').is_checked() and not page.locator('input[name="analytics"]').is_checked())
    ctx.close()
    expired={**old,"analytics":True,"expires":int(time.time()*1000)-1000}
    ctx,page,calls,errors=context(expired)
    visit(page)
    check("Expired consent does not load Google",no_google(page,calls))
    ctx.close()
    for path in ("/","/que-faire-nyons/visiter-nyons/","/meteo-nyons/","/sante-nyons/teleassistance-nyons/"):
        ctx,page,calls,errors=context(width=390)
        visit(page,path)
        check("Direct lodging menu exists: "+path,page.locator("header .navlinks > a[data-nyons-shortcut=hebergement]").count()==1)
        check("Lodging destination is correct: "+path,page.locator("header .navlinks > a[data-nyons-shortcut=hebergement]").get_attribute("href").endswith("/ou-dormir-a-nyons/"))
        analytics_only(page)
        check("One Analytics initialization: "+path,len(calls)==1 and len(configs(page))==1)
        check("Cookie form fits on mobile: "+path,page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
        check("No runtime error: "+path,not errors)
        ctx.close()
    for prefix in PREFIXES[1:]:
        ctx,page,calls,errors=context()
        visit(page,prefix+"/")
        analytics_only(page)
        check("Preview is not measured: "+prefix,no_google(page,calls))
        check("Preview lodging link exists: "+prefix,page.locator("header .navlinks > a[data-nyons-shortcut=hebergement]").count()==1)
        ctx.close()
    for prefix in PREFIXES:
        for path in ("/","/que-faire-nyons/nyons-quand-il-pleut/","/cookies/"):
            html=read(BASE+prefix+path) if args.public else source_path(prefix+path).read_text()
            check("Static lodging navigation: "+prefix+path,'data-nyons-shortcut="hebergement"' in html)
            check("Shared script cache version: "+prefix+path,"google-analytics-20261008-v1" in html)
    browser.close()
print("GOOGLE_TAG_AUDIT_BEGIN")
print(json.dumps({"mode":"public" if args.public else "before-publication","measurementId":ID,"googleRequestsMocked":True,"testVisitsSentToAnalytics":False,"passedChecks":len(checks),"checks":checks},ensure_ascii=False,indent=2))
print("GOOGLE_TAG_AUDIT_END")
