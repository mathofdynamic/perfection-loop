# Capturing Evidence

The judges are only as good as what they can see. Bad or partial evidence produces a false PASS, which is the exact failure this skill exists to stop.

## Rules

1. **Capture the real running app**, not a mock and not the code. Start the dev server or serve the build.
2. **Recapture everything after every change.** Never just the thing you touched.
3. **Wait for the page to settle**: network idle, fonts loaded, entrance animations finished. Screenshots taken mid-load produce phantom defects and hide real ones.
4. **Name files so rounds can be paired**: `.perfection/round-N/<viewport>_<state>.png`. Keep the same names every round so the regression judge can compare.
5. **You look too.** Open the key screenshots with the image viewer yourself before dispatching judges.

## Default matrix

Adjust to the contract. Drop what is irrelevant, add what matters.

| Axis | Defaults |
|---|---|
| Viewports | 375x812 (phone), 768x1024 (tablet), 1280x800 (laptop), 1920x1080 (large). Add an in-between width such as 1024 or 900 when the layout has breakpoints. |
| Shots per viewport | Above-the-fold and full-page |
| Themes | Light, dark if the app supports it |
| Motion | Normal, and `prefers-reduced-motion: reduce` |
| States | Default, hover on primary controls, keyboard focus on primary controls, open menus/modals/drawers, empty, loading, error, success, long content, many items |
| Flows | The primary user journey, one screenshot per step |

Bug fixes: also capture the exact view from the user's screenshot, before and after.

## Automated script

`scripts/capture.py` captures the matrix and runs DOM checks (console errors, failed requests, horizontal overflow, broken images, missing alt, small targets, tiny text, missing lang/title/viewport meta).

Setup, once:

```bash
pip install playwright --break-system-packages
playwright install chromium
```

Basic run:

```bash
python <skill-dir>/scripts/capture.py --url http://localhost:3000 --out .perfection/round-1
```

Common options: `--viewports mobile-375,laptop-1280`, `--themes light,dark`, `--reduced-motion`, `--path /pricing` (repeatable), `--steps steps.json`.

### Interaction states with `--steps`

A JSON file describing states to reach and photograph:

```json
{
  "steps": [
    { "name": "menu-open", "viewports": ["mobile-375"],
      "actions": [ { "click": "button[aria-label='Menu']" } ] },
    { "name": "login-error",
      "actions": [
        { "fill": ["#email", "not-an-email"] },
        { "press": "Tab" },
        { "click": "button[type=submit]" },
        { "wait": 300 }
      ] },
    { "name": "cta-hover",
      "actions": [ { "hover": ".hero .cta" } ] },
    { "name": "cta-focus",
      "actions": [ { "focus": ".hero .cta" } ] }
  ]
}
```

Supported actions: `click`, `hover`, `focus`, `fill` (`[selector, value]`), `press`, `wait` (ms), `scroll` (y pixels).

The script gives you a sturdy baseline. Anything it cannot reach (multi-step flows with auth, drag interactions, real data) you capture with whatever browser tooling the environment provides.

## Other browser tooling

If the environment already has a browser tool (Playwright MCP, Chrome DevTools MCP, a built-in preview, Claude in Chrome), use it for the same matrix. The requirements are identical: real app, full matrix, settled page, consistent filenames.

## Motion evidence

Static screenshots cannot show motion. For animated UI, capture a frame sequence after the trigger (about 0, 100, 200, 400 ms) or record video, and give the Motion judge both the frames and the source files. Slow the animation to 2-5x in devtools when you need to see timing problems.

## When you cannot run a browser

Say so in the final report, prominently. Then verify what you can (build, typecheck, lint, unit tests, DOM structure through a headless render or an HTML snapshot) and tell the user visual verification did not happen. Do not fill the gap with confident language.

## Things that cause false results

- Screenshotting before fonts load, so fallback fonts appear or shifts happen after capture.
- Cached builds. Confirm the served page reflects your latest change.
- Cookie banners, dev overlays, or hot-reload toasts covering content. Dismiss or disable them before capture.
- Scroll-triggered reveals never firing in a full-page shot. Scroll through the page first, then capture.
- Testing only the viewport you develop on.
