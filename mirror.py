#!/usr/bin/env python3
"""Mirror kumaranhospitals.com homepage + assets into C:/kumaran/site as a
self-contained, same-origin deployable folder. Rewrites all absolute
kumaranhospitals.com URLs to root-relative so fonts load without CORS."""
import os, re, sys, urllib.request, urllib.parse, ssl

BASE = "https://kumaranhospitals.com"
HOST = "kumaranhospitals.com"
OUT  = r"C:\kumaran\site"
UA   = "Mrics/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36".replace("Mrics","Mozilla")
CTX  = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE

TEXT_EXT = (".css",)
SKIP_EXT = (".mp4",".webm",".mov")  # large below-the-fold videos: skip
ASSET_RE = re.compile(r'https://kumaranhospitals\.com/[^\s"\'\)\\]+', re.I)
CSSURL_RE = re.compile(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)', re.I)
IMPORT_RE = re.compile(r'@import\s+[\'"]([^\'"]+)[\'"]', re.I)

seen=set(); queued=set()

KIOSK_FIX_CSS = """/* ============================================================
   KIOSK LABEL FIX - the ONLY change vs. the live kumaranhospitals.com
   Keeps the 5 quick-access service labels (Pharmacy / Lab / Ambulance /
   Treatments / Infrastructure) on a single line instead of wrapping.
   Font auto-fits the column width, so it works at any panel size.
   ============================================================ */
.elementor-element-c4f72c1 .elementor-widget-heading {
  width: 100% !important;
  max-width: 100% !important;
}
.elementor-element-c4f72c1 .elementor-heading-title,
.elementor-element-c4f72c1 .elementor-heading-title a {
  display: block !important;
  width: 100% !important;
  white-space: nowrap !important;
  font-size: clamp(11px, 1.9vw, 19px) !important;
  line-height: 1.25 !important;
  letter-spacing: 0 !important;
  text-align: center !important;
  overflow: visible !important;
  text-overflow: clip !important;
}
"""

def sprint(*a):
    print(*[str(x).encode("ascii","replace").decode("ascii") for x in a])

def encode_url(url):
    pr=urllib.parse.urlsplit(url)
    path=urllib.parse.quote(pr.path, safe="/%")
    query=urllib.parse.quote(pr.query, safe="=&%?")
    return urllib.parse.urlunsplit((pr.scheme,pr.netloc,path,query,""))

def fetch(url):
    req=urllib.request.Request(encode_url(url), headers={"User-Agent":UA,"Referer":BASE})
    with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
        return r.read()

def local_path(url):
    p=urllib.parse.urlparse(url).path
    if p.endswith("/") or p=="":
        p+="index.html"
    return p.lstrip("/")

def save(relpath, data):
    dest=os.path.join(OUT, relpath.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest,"wb") as f: f.write(data)

def norm(url):
    url=url.split("#")[0]
    return url

def looks_like_asset(u):
    path=urllib.parse.urlparse(u).path.lower()
    if any(path.endswith(e) for e in SKIP_EXT): return False
    return ("." in os.path.basename(path)) and not path.endswith(".html") and not path.endswith("/")

def process_css(css_text, css_url):
    """download url()/@import targets, rewrite to root-relative."""
    refs=set(CSSURL_RE.findall(css_text))|set(IMPORT_RE.findall(css_text))
    for ref in refs:
        ref=ref.strip()
        if ref.startswith("data:"): continue
        absu=urllib.parse.urljoin(css_url, ref)
        if HOST not in absu: continue
        crawl(norm(absu))
    # rewrite absolute host refs to root-relative
    css_text=css_text.replace("https://"+HOST,"").replace("http://"+HOST,"")
    return css_text

def crawl(url):
    url=norm(url)
    if url in seen: return
    if HOST not in url: return
    seen.add(url)
    path=urllib.parse.urlparse(url).path.lower()
    if any(path.endswith(e) for e in SKIP_EXT):
        return
    try:
        data=fetch(url)
    except Exception as e:
        sprint("  !! fail", url, e); return
    rel=local_path(url)
    if path.endswith(".css"):
        txt=data.decode("utf-8","ignore")
        txt=process_css(txt, url)
        save(rel, txt.encode("utf-8"))
        sprint("  css ", rel)
    else:
        save(rel, data)
        sprint("  bin ", rel, f"({len(data)//1024}k)")

def main():
    os.makedirs(OUT, exist_ok=True)
    sprint("Fetching homepage...")
    html=fetch(BASE).decode("utf-8","ignore")
    # discover assets in HTML
    assets=set(norm(u) for u in ASSET_RE.findall(html) if looks_like_asset(u))
    sprint(f"Found {len(assets)} candidate assets in HTML")
    for a in sorted(assets):
        crawl(a)
    # rewrite HTML: strip domain -> root-relative; keep queries (harmless on static host)
    html2=html.replace("https://"+HOST,"").replace("http://"+HOST,"")
    # also handle escaped JSON form https:\/\/kumaranhospitals.com
    html2=html2.replace("https:\\/\\/"+HOST,"").replace("http:\\/\\/"+HOST,"")
    # --- KIOSK LABEL FIX: keep the 5 service labels on one line ---
    if "kiosk-fix.css" not in html2:
        html2=html2.replace("</head>",
            '<link rel="stylesheet" href="/kiosk-fix.css?v=1" media="all" />\n</head>', 1)
    save("kiosk-fix.css", KIOSK_FIX_CSS.encode("utf-8"))
    save("index.html", html2.encode("utf-8"))
    sprint("Saved index.html + kiosk-fix.css")
    sprint(f"DONE. {len(seen)} assets mirrored into {OUT}")

if __name__=="__main__":
    main()
