#!/usr/bin/env python3
"""Capture a screenshot matrix plus automated checks for the perfection-loop skill.

Usage:
  python capture.py --url http://localhost:3000 --out .perfection/round-1
  python capture.py --url http://localhost:3000 --path /pricing --path /login \
      --viewports mobile-375,laptop-1280 --themes light,dark --steps steps.json

Setup: pip install playwright --break-system-packages && playwright install chromium
Writes PNGs plus report.json into --out. Exit code 0 even when defects are found;
the judges read report.json. Exit code 2 means the capture itself failed.
"""
import argparse
import json
import pathlib
import sys

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright is not installed. Run: pip install playwright --break-system-packages "
          "&& playwright install chromium", file=sys.stderr)
    sys.exit(2)

VIEWPORTS = {
    "mobile-375": (375, 812),
    "tablet-768": (768, 1024),
    "laptop-1280": (1280, 800),
    "desktop-1920": (1920, 1080),
}

CHECKS_JS = r"""
() => {
  const de = document.documentElement;
  const vw = de.clientWidth;
  const sel = (el) => {
    if (el.id) return '#' + el.id;
    let s = el.tagName.toLowerCase();
    if (el.classList.length) s += '.' + [...el.classList].slice(0, 2).join('.');
    return s;
  };
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden';
  };
  const out = {
    horizontalScroll: de.scrollWidth > vw + 1,
    scrollWidth: de.scrollWidth, clientWidth: vw,
    overflowingElements: [], smallTargets: [], brokenImages: [], missingAlt: [],
    tinyText: [], clippedText: [],
    meta: {
      lang: de.getAttribute('lang') || null,
      title: document.title || null,
      viewportMeta: !!document.querySelector('meta[name=viewport]'),
      h1Count: document.querySelectorAll('h1').length,
    },
  };
  const seenText = new Set();
  for (const el of document.querySelectorAll('body *')) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (r.right > vw + 1 && cs.position !== 'fixed' && out.overflowingElements.length < 25)
      out.overflowingElements.push({ el: sel(el), right: Math.round(r.right) });
    if (el.matches('a[href],button,input:not([type=hidden]),select,textarea,[role=button],[role=link],[tabindex]:not([tabindex="-1"])')) {
      if ((r.width < 24 || r.height < 24) && out.smallTargets.length < 25)
        out.smallTargets.push({ el: sel(el), w: Math.round(r.width), h: Math.round(r.height), severity: 'below-24px' });
      else if ((r.width < 44 || r.height < 44) && vw <= 500 && out.smallTargets.length < 25)
        out.smallTargets.push({ el: sel(el), w: Math.round(r.width), h: Math.round(r.height), severity: 'below-44px-touch' });
    }
    if (el.tagName === 'IMG') {
      if (el.complete && el.naturalWidth === 0) out.brokenImages.push(el.currentSrc || el.src);
      if (!el.hasAttribute('alt')) out.missingAlt.push(el.currentSrc || el.src);
    }
    const hasOwnText = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (hasOwnText) {
      const fs = parseFloat(cs.fontSize);
      if (fs < 12 && out.tinyText.length < 15) out.tinyText.push({ el: sel(el), px: fs });
      const clips = ['hidden', 'clip'].includes(cs.overflowX);
      if (clips && el.scrollWidth > el.clientWidth + 1 && cs.textOverflow !== 'ellipsis'
          && out.clippedText.length < 15 && !seenText.has(sel(el))) {
        seenText.add(sel(el));
        out.clippedText.push({ el: sel(el), scrollWidth: el.scrollWidth, clientWidth: el.clientWidth });
      }
    }
  }
  return out;
}
"""


def settle(page, extra_ms=400):
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    try:
        page.evaluate("document.fonts && document.fonts.ready")
    except Exception:
        pass
    page.wait_for_timeout(extra_ms)


def scroll_through(page):
    """Trigger scroll-based reveals and lazy images, then return to top."""
    page.evaluate(
        """async () => {
          const step = Math.max(window.innerHeight * 0.8, 300);
          for (let y = 0; y < document.body.scrollHeight; y += step) {
            window.scrollTo(0, y);
            await new Promise(r => setTimeout(r, 120));
          }
          window.scrollTo(0, 0);
        }"""
    )
    page.wait_for_timeout(300)


def run_actions(page, actions):
    for a in actions:
        if "click" in a:
            page.click(a["click"], timeout=5000)
        elif "hover" in a:
            page.hover(a["hover"], timeout=5000)
        elif "focus" in a:
            page.focus(a["focus"], timeout=5000)
        elif "fill" in a:
            page.fill(a["fill"][0], a["fill"][1], timeout=5000)
        elif "press" in a:
            page.keyboard.press(a["press"])
        elif "wait" in a:
            page.wait_for_timeout(int(a["wait"]))
        elif "scroll" in a:
            page.evaluate(f"window.scrollTo(0, {int(a['scroll'])})")
    page.wait_for_timeout(300)


def slug(text):
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in text).strip("-") or "root"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="Base URL of the running app")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--path", action="append", default=None, help="Path to capture (repeatable). Default: /")
    ap.add_argument("--viewports", default=",".join(VIEWPORTS), help="Comma list of names or WxH")
    ap.add_argument("--themes", default="light", help="Comma list: light,dark")
    ap.add_argument("--reduced-motion", action="store_true", help="Also capture with reduced motion")
    ap.add_argument("--steps", help="JSON file describing interaction states")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    paths = args.path or ["/"]
    themes = [t.strip() for t in args.themes.split(",") if t.strip()]

    vps = {}
    for v in [x.strip() for x in args.viewports.split(",") if x.strip()]:
        if v in VIEWPORTS:
            vps[v] = VIEWPORTS[v]
        elif "x" in v:
            w, h = v.split("x")
            vps[v] = (int(w), int(h))
        else:
            print(f"Unknown viewport {v}", file=sys.stderr)
            sys.exit(2)

    steps = []
    if args.steps:
        steps = json.loads(pathlib.Path(args.steps).read_text()).get("steps", [])

    motion_modes = [("normal", "no-preference")]
    if args.reduced_motion:
        motion_modes.append(("reduced", "reduce"))

    report = {"url": args.url, "captures": [], "console": [], "pageErrors": [],
              "failedRequests": [], "badResponses": [], "checks": {}, "stepErrors": []}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for vp_name, (w, h) in vps.items():
            for theme in themes:
                for motion_name, motion in motion_modes:
                    ctx = browser.new_context(
                        viewport={"width": w, "height": h},
                        color_scheme=theme,
                        reduced_motion=motion,
                        has_touch=w <= 500,
                        is_mobile=w <= 500,
                    )
                    page = ctx.new_page()
                    tag = f"{vp_name}_{theme}" + ("" if motion_name == "normal" else f"_{motion_name}")
                    page.on("console", lambda m, t=tag: report["console"].append(
                        {"ctx": t, "type": m.type, "text": m.text}) if m.type in ("error", "warning") else None)
                    page.on("pageerror", lambda e, t=tag: report["pageErrors"].append({"ctx": t, "error": str(e)}))
                    page.on("requestfailed", lambda r, t=tag: report["failedRequests"].append(
                        {"ctx": t, "url": r.url, "failure": r.failure}))
                    page.on("response", lambda r, t=tag: report["badResponses"].append(
                        {"ctx": t, "url": r.url, "status": r.status}) if r.status >= 400 else None)

                    for path in paths:
                        base = f"{tag}_{slug(path)}"
                        try:
                            page.goto(args.url.rstrip("/") + path, wait_until="domcontentloaded", timeout=30000)
                        except Exception as e:
                            print(f"FAILED to load {path} at {tag}: {e}", file=sys.stderr)
                            sys.exit(2)
                        settle(page)
                        page.screenshot(path=str(out / f"{base}_fold.png"))
                        scroll_through(page)
                        settle(page, 200)
                        page.screenshot(path=str(out / f"{base}_full.png"), full_page=True)
                        report["captures"].append(f"{base}_fold.png")
                        report["captures"].append(f"{base}_full.png")
                        report["checks"][base] = page.evaluate(CHECKS_JS)

                        for step in steps:
                            if step.get("viewports") and vp_name not in step["viewports"]:
                                continue
                            try:
                                page.goto(args.url.rstrip("/") + path, wait_until="domcontentloaded", timeout=30000)
                                settle(page, 200)
                                run_actions(page, step.get("actions", []))
                                name = f"{base}_{slug(step['name'])}.png"
                                page.screenshot(path=str(out / name))
                                report["captures"].append(name)
                            except Exception as e:
                                report["stepErrors"].append({"ctx": base, "step": step.get("name"), "error": str(e)})
                    ctx.close()
        browser.close()

    (out / "report.json").write_text(json.dumps(report, indent=2))

    # Human-readable summary
    issues = 0
    print(f"Captured {len(report['captures'])} screenshots into {out}")
    for k, c in report["checks"].items():
        found = []
        if c["horizontalScroll"]:
            found.append(f"horizontal scroll ({c['scrollWidth']}>{c['clientWidth']})")
        for key in ("overflowingElements", "smallTargets", "brokenImages", "missingAlt", "tinyText", "clippedText"):
            if c[key]:
                found.append(f"{key}: {len(c[key])}")
        m = c["meta"]
        if not m["lang"]:
            found.append("missing <html lang>")
        if not m["title"]:
            found.append("missing <title>")
        if not m["viewportMeta"]:
            found.append("missing viewport meta")
        if m["h1Count"] != 1:
            found.append(f"h1 count = {m['h1Count']}")
        if found:
            issues += len(found)
            print(f"  [{k}] " + "; ".join(found))
    for label, key in (("console errors/warnings", "console"), ("page errors", "pageErrors"),
                       ("failed requests", "failedRequests"), ("4xx/5xx responses", "badResponses"),
                       ("step errors", "stepErrors")):
        if report[key]:
            issues += len(report[key])
            print(f"  {label}: {len(report[key])} (see report.json)")
    print("Automated checks: " + ("CLEAN" if issues == 0 else f"{issues} finding(s), give report.json to the Technical judge"))


if __name__ == "__main__":
    main()
