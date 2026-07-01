# Kumaran Hospitals — Kiosk Site (full clone)

A **complete, self-contained clone** of kumaranhospitals.com built for the lobby
kiosk (**LedArt 3568V**, Android 11, top web region **1080 × 965**).

It is byte-for-byte the real website — every page, all CSS/JS, fonts, icons,
images **and videos** — with **one single change**: the 5 home-page service
labels (Pharmacy · Lab · Ambulance · Treatments · Infrastructure) are forced
onto a single line instead of wrapping. See [`site/kiosk-fix.css`](site/kiosk-fix.css).

## Contents
```
site/            <- the deployable static site (79 pages, all assets + videos)
  index.html       home page (+ the 1-line label fix)
  kiosk-fix.css    the ONLY custom file (single-line service labels)
  <page>/index.html   every internal page (pharmacy, lab, about-us, transplants, blog, ...)
  wp-content/ ...  exact copy of the site's css, js, fonts, images, videos
crawl.py         re-run to re-clone the whole site (pages + videos) and re-apply the fix
mirror.py        older single-page mirror (kept for reference)
```
Everything loads from within `site/` (no calls back to kumaranhospitals.com), so
fonts and icons render on any host with no cross-origin (CORS) issues.

Large videos are stored via **Git LFS** (`*.mp4`) because two exceed GitHub's
100 MB per-file limit.

---

## 1) Push to GitHub (public repo)

Create an **empty** public repo on GitHub named e.g. `kumaran-kiosk` (no README/…).
Then, from this folder (`C:\kumaran`):

```bash
git add .
git commit -m "Kumaran Hospitals kiosk site clone"
git remote add origin https://github.com/<your-username>/kumaran-kiosk.git
git push -u origin main
```
Git LFS uploads the videos automatically (git-lfs is already configured here).

## 2) Deploy on Vercel (connect the repo)

1. Go to <https://vercel.com/new>
2. **Import** the `kumaran-kiosk` GitHub repo (authorize Vercel for GitHub if asked)
3. On the configure screen, set **Root Directory → `site`** (click *Edit* next to
   Root Directory and pick the `site` folder). Framework preset: **Other**. No build command.
4. Click **Deploy** → you get a URL like `https://kumaran-kiosk.vercel.app`

Every future `git push` to `main` auto-redeploys.

## 3) Point the kiosk at it
In the LedArt editor, edit the top web region (`0,0  1080×965`) and replace
`kumaranhospitals.com` with your Vercel URL, then publish the program.

---

## Refreshing the clone (when the live site changes)
This is a static snapshot; it does not auto-update. To refresh:
```bash
python crawl.py        # re-clones site/ (pages + videos) and re-applies the fix
git add . && git commit -m "refresh clone" && git push
```

## Notes
- **Git LFS bandwidth:** GitHub's free LFS tier is 1 GB storage + 1 GB/month
  bandwidth. The videos (~310 MB) fit in storage; a handful of deploys stay under
  the bandwidth cap. End users stream video from Vercel's CDN, not GitHub LFS.
- If you'd rather shrink the repo, the two big testimonial videos
  (`testimonial.mp4` 206 MB, `Melasekarvideo1.mp4` 104 MB) can be compressed —
  ask and I'll do it (needs ffmpeg).

## Local preview
```bash
python -m http.server 3210 --directory site
```
then open <http://localhost:3210> in a window sized to 1080×965.
