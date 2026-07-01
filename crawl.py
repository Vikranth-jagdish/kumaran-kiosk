#!/usr/bin/env python3
"""Full multi-page clone of kumaranhospitals.com into ./site as a
self-contained, same-origin static site (deployable to Vercel/Netlify/etc).

- Crawls internal PAGES (nav, service pages, transplant pages, etc.) so every
  clickable link works offline.
- Downloads ALL assets incl. videos, fonts, css, js, images.
- Rewrites every absolute kumaranhospitals.com URL to root-relative so fonts
  load without CORS and links stay inside the clone.
- Injects kiosk-fix.css (single-line service labels) into every page.
"""
import os, re, ssl, urllib.request, urllib.parse
from collections import deque

BASE="https://kumaranhospitals.com"
HOST="kumaranhospitals.com"
OUT=r"C:\kumaran\site"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
CTX=ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
MAX_PAGES=80

ASSET_RE=re.compile(r'https://kumaranhospitals\.com/[^\s"\'\)\\]+', re.I)
CSSURL_RE=re.compile(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)', re.I)
IMPORT_RE=re.compile(r'@import\s+[\'"]([^\'"]+)[\'"]', re.I)
HREF_RE=re.compile(r'href=["\'](https://kumaranhospitals\.com/[^"\'#?]*)["\']', re.I)

# page paths we never want to crawl
SKIP_PAGE=re.compile(r'(wp-admin|wp-login|wp-json|xmlrpc|/feed/?$|/comments/|/cart|/checkout|'
                     r'/my-account|/page/\d+|/tag/|/category/|/author/|/20\d\d/|\.xml$|\.php$)', re.I)
ASSET_EXT=(".css",".js",".png",".jpg",".jpeg",".gif",".svg",".webp",".ico",
           ".woff",".woff2",".ttf",".eot",".mp4",".webm",".mov",".m4v",".pdf",".mp3")

seen_asset=set(); seen_page=set()

KIOSK_FIX_CSS="""/* ============================================================
   KIOSK LABEL FIX - the ONLY change vs. the live kumaranhospitals.com
   Keeps the 5 quick-access service labels on a single line (no wrapping).
   ============================================================ */
.elementor-element-c4f72c1 .elementor-widget-heading{width:100%!important;max-width:100%!important;}
.elementor-element-c4f72c1 .elementor-heading-title,
.elementor-element-c4f72c1 .elementor-heading-title a{
  display:block!important;width:100%!important;white-space:nowrap!important;
  font-size:clamp(11px,1.9vw,19px)!important;line-height:1.25!important;
  letter-spacing:0!important;text-align:center!important;overflow:visible!important;text-overflow:clip!important;}
"""

def sprint(*a): print(*[str(x).encode("ascii","replace").decode("ascii") for x in a])

def encode_url(u):
    pr=urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit((pr.scheme,pr.netloc,
        urllib.parse.quote(pr.path,safe="/%"),urllib.parse.quote(pr.query,safe="=&%?"),""))

def fetch(u):
    req=urllib.request.Request(encode_url(u),headers={"User-Agent":UA,"Referer":BASE})
    with urllib.request.urlopen(req,context=CTX,timeout=90) as r: return r.read()

def save(rel,data):
    dest=os.path.join(OUT,rel.replace("/",os.sep))
    os.makedirs(os.path.dirname(dest),exist_ok=True)
    with open(dest,"wb") as f: f.write(data)

def asset_local(u):  # keep dir structure
    return urllib.parse.urlparse(u).path.lstrip("/")

def page_local(u):   # /pharmacy/ -> pharmacy/index.html ; / -> index.html
    p=urllib.parse.urlparse(u).path
    if p in ("","/"): return "index.html"
    p=p.strip("/")
    last=p.split("/")[-1]
    if "." in last:  # already a file
        return p
    return p+"/index.html"

def crawl_asset(u):
    u=u.split("#")[0]
    if HOST not in u or u in seen_asset: return
    seen_asset.add(u)
    ext=os.path.splitext(urllib.parse.urlparse(u).path)[1].lower()
    if ext not in ASSET_EXT: return
    rel=asset_local(u)
    dest=os.path.join(OUT,rel.replace("/",os.sep))
    if os.path.exists(dest) and os.path.getsize(dest)>0 and ext!=".css":
        return  # already have it (skip re-download except css which we re-process)
    try: data=fetch(u)
    except Exception as e: sprint("  !!asset",u,e); return
    if ext==".css":
        txt=data.decode("utf-8","ignore")
        for ref in set(CSSURL_RE.findall(txt))|set(IMPORT_RE.findall(txt)):
            ref=ref.strip()
            if ref.startswith("data:"): continue
            crawl_asset(urllib.parse.urljoin(u,ref))
        txt=txt.replace("https://"+HOST,"").replace("http://"+HOST,"")
        save(rel,txt.encode("utf-8")); sprint("  css ",rel)
    else:
        save(rel,data); sprint("  bin ",rel,f"({len(data)//1024}k)")

def rewrite(html):
    for h in ("https://"+HOST,"http://"+HOST,"https:\\/\\/"+HOST,"http:\\/\\/"+HOST):
        html=html.replace(h,"")
    if "kiosk-fix.css" not in html:
        html=html.replace("</head>",'<link rel="stylesheet" href="/kiosk-fix.css?v=2" media="all" />\n</head>',1)
    return html

def crawl_page(u):
    html=fetch(u).decode("utf-8","ignore")
    for a in set(ASSET_RE.findall(html)):
        crawl_asset(a.split("#")[0])
    links=set(HREF_RE.findall(html))
    save(page_local(u),rewrite(html).encode("utf-8"))
    sprint("PAGE",page_local(u))
    return links

def main():
    os.makedirs(OUT,exist_ok=True)
    save("kiosk-fix.css",KIOSK_FIX_CSS.encode("utf-8"))
    q=deque([BASE+"/"]); seen_page.add(BASE+"/")
    n=0
    while q and n<MAX_PAGES:
        url=q.popleft(); n+=1
        try: links=crawl_page(url)
        except Exception as e: sprint("!!page",url,e); continue
        for l in links:
            l=l.rstrip("/")+"/" if "." not in l.split("/")[-1] else l
            if l in seen_page: continue
            if SKIP_PAGE.search(l): continue
            seen_page.add(l); q.append(l)
    sprint(f"DONE. {n} pages, {len(seen_asset)} assets -> {OUT}")

if __name__=="__main__": main()
