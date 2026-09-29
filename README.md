# Perfection Loop

[![skills.sh](https://skills.sh/b/mathofdynamic/perfection-loop)](https://skills.sh/mathofdynamic/perfection-loop)

An evidence-driven verification loop for AI-assisted software work.

Perfection Loop is an Agent Skill that prevents an agent from declaring a frontend or UI task complete before the real result has been captured, inspected, tested, and reviewed. It is designed for responsive interfaces, interactions, animation, accessibility, and any other work where completion must be demonstrated rather than asserted.

## What it does

The skill turns “done” into a repeatable quality gate:

1. Define a concrete contract for the requested change.
2. Reproduce the current behavior when fixing a bug.
3. Run the real application and capture settled browser output.
4. Check multiple viewports, themes, motion modes, states, and flows.
5. Run automated DOM, console, network, and metadata checks.
6. Review the evidence with independent adversarial judges.
7. Log findings, fix root causes, recapture everything, and repeat.

The loop exits only when the final evidence is clean, the ledger has no unresolved defects, and every acceptance criterion has evidence behind it.

## Why it exists

Source code and diffs show what an author intended. They do not prove what a user receives in a browser. Authors are also poor judges of their own work because they already know what the interface is supposed to look like.

Perfection Loop separates implementation from verification and keeps an auditable record of the result. Any change invalidates earlier evidence, so fixes are followed by a complete recapture and review.

## When to use it

Use the skill:

- after any frontend or UI change;
- when changing responsive layout, CSS, interaction, or animation;
- when investigating a visual or UI bug;
- before describing work as polished, production-ready, or complete;
- for non-visual tasks where tests, command output, API responses, or logs must prove completion.

It is deliberately stricter than a build check. A successful build, HTTP 200, or passing unit test does not prove that the rendered interface is usable.

## Quick start

### 1. Install the browser dependencies

The capture helper uses Playwright and Chromium:

```bash
python -m pip install playwright
python -m playwright install chromium
```

On an externally managed Python installation, use the package-management procedure required by that environment.

### 2. Run the application

Start the actual application with its normal development or preview command. The capture helper does not start the application for you.

### 3. Capture a verification round

Run the helper from the application project root, pointing it at the running app:

```bash
python path/to/perfection-loop/scripts/capture.py \
  --url http://localhost:3000 \
  --out .perfection/round-1
```

PowerShell equivalent:

```powershell
python path/to/perfection-loop/scripts/capture.py `
  --url http://localhost:3000 `
  --out .perfection/round-1
```

The command captures the default viewport matrix and writes screenshots plus `report.json`. It exits with code `0` when defects are found because the report is intended for review. Exit code `2` means the capture itself failed.

### 4. Use the skill workflow

Ask the agent to use the `perfection-loop` skill after the change or bug report. The agent should create `.perfection/contract.md`, review the captured evidence, maintain `.perfection/ledger.md`, and repeat the loop after every fix.

## Capture options

The helper supports the following common variations:

```bash
python path/to/perfection-loop/scripts/capture.py \
  --url http://localhost:3000 \
  --out .perfection/round-1 \
  --path / \
  --path /pricing \
  --viewports mobile-375,tablet-768,laptop-1280,desktop-1920 \
  --themes light,dark \
  --reduced-motion \
  --steps steps.json
```

Supported viewport names are:

- `mobile-375` — 375x812
- `tablet-768` — 768x1024
- `laptop-1280` — 1280x800
- `desktop-1920` — 1920x1080

Custom `WIDTHxHEIGHT` values are also accepted. Interaction states can be described in a JSON file:

```json
{
  "steps": [
    {
      "name": "menu-open",
      "viewports": ["mobile-375"],
      "actions": [{ "click": "button[aria-label='Menu']" }]
    },
    {
      "name": "cta-focus",
      "actions": [{ "focus": ".hero .cta" }]
    }
  ]
}
```

Supported actions are `click`, `hover`, `focus`, `fill`, `press`, `wait`, and `scroll`.

## Automated checks

Each capture round records:

- browser console errors and warnings;
- uncaught page errors;
- failed requests and 4xx/5xx responses;
- horizontal page overflow and overflowing elements;
- broken images and missing `alt` attributes;
- undersized interactive targets;
- very small text and clipped text;
- missing `lang`, `title`, or viewport metadata;
- unexpected heading counts.

These checks are a baseline, not a substitute for visual inspection, keyboard testing, screen-reader testing, or real-device testing.

## Review panel

The included judge prompts divide review into independent areas:

| Judge | Responsibility |
| --- | --- |
| A | Requirements and scope |
| B | Layout and responsiveness |
| C | Design craft |
| D | Interaction and UX |
| E | Accessibility |
| F | Motion |
| G | Copy |
| H | Technical evidence |
| I | Regression review from round 2 onward |

Each finding must identify the evidence, explain the user impact, and receive a severity from `P0` to `P3`.

## Evidence layout

Working evidence belongs in the application project under `.perfection/`:

```text
.perfection/
├── contract.md
├── ledger.md
└── round-1/
    ├── mobile-375_light_root_fold.png
    ├── mobile-375_light_root_full.png
    ├── report.json
    └── judge-A.md
```

Keep the same screenshot names across rounds so the regression judge can compare before and after states. Add `.perfection/` to the application’s `.gitignore` when the evidence is temporary or contains sensitive data.

## Exit criteria

The workflow is complete only when:

- the last full recapture was made from the final code;
- the latest judge round reports zero defects;
- the ledger contains no `open` or `fixed` entries;
- every acceptance criterion is marked complete with evidence;
- automated checks are clean;
- unsupported environments are explicitly listed as unverified.

The skill must report limitations honestly. It must not claim real-device, iOS Safari, screen-reader, slow-network, or production-backend verification unless those checks actually happened.

## Package layout

```text
perfection-loop/
├── SKILL.md                 # Agent instructions and routing
├── references/
│   ├── capture.md           # Evidence and capture requirements
│   └── judges.md            # Independent review prompts
├── scripts/
│   └── capture.py           # Playwright capture and automated checks
└── perfection-loop.skill    # Packaged distributable skill archive
```

## Installation from a public repository

The skill can be installed from this public Agent Skills repository with the `skills` CLI:

```bash
npx skills add mathofdynamic/perfection-loop --skill perfection-loop
```

To install it manually, place this directory at `.agents/skills/perfection-loop/` in a project that supports Agent Skills, then start a new agent session.

## Scope boundaries

Perfection Loop is a verification workflow. It does not:

- start, deploy, or modify the application under review;
- replace product requirements or design decisions;
- guarantee correctness outside the evidence matrix;
- replace security review, performance profiling, device testing, or assistive-technology testing;
- treat a screenshot, build, or automated report as proof of anything it did not inspect.

## License

MIT. See [LICENSE](LICENSE).
