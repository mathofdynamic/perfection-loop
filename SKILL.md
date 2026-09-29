---
name: perfection-loop
description: A relentless verify-and-fix loop that proves work is actually finished instead of just delivered. Use this skill after making ANY change to a frontend or UI (web page, app screen, component, CSS, layout, animation, responsive behavior) and BEFORE telling the user it is done. Also use it whenever the user reports a visual or UI bug, attaches a screenshot of something wrong, or says things like "make sure it's perfect", "verify it", "double check", "polish", "production ready", "no issues", or "why is it still broken". Captures the real running result, sends independent adversarial judge sub-agents to inspect it, logs every defect, fixes them, and repeats until a fresh full review finds zero defects. Use it even when the change looks small, because small changes are where regressions hide. Also applies to any non-UI task where "done" must be proven with evidence (tests, command output, API responses) rather than asserted.
---

# Perfection Loop

Your job here is not to deliver. It is to finish.

The failure this skill exists to prevent: you write code, you believe it is correct, you never look at what it actually produced, and you announce "done". Even when you do look, you are the worst possible judge of your own work, because you know what you *meant* and your eyes fill it in. A fresh reviewer with a screenshot and a hostile mindset finds problems in seconds that the author swore were not there.

So the rule is simple: **nothing is done until independent judges have looked at the real running result and found nothing wrong.** "Good enough" is not a state this skill recognizes. Production means no known defects.

## Principles (and why they exist)

1. **Never trust code you have not seen run.** Reading a diff tells you what you wrote. Only the rendered result tells you what the user gets.
2. **The author is a biased judge.** Judges are separate, start with fresh context, and never see your reasoning or your claim that it is fine. Anchoring on the author's confidence is how defects survive.
3. **Evidence or it did not happen.** Every defect cites a screenshot and a location. Every "pass" cites what was inspected. A judge that cannot point at pixels does not get to report.
4. **Any change invalidates every earlier pass.** A fix in one place breaks another. After every change, recapture everything and review again. The final clean review must be on the final code.
5. **Perfect means zero open defects, not zero effort.** Keep going until the ledger is empty. But if you are stuck, stop and say so. Never claim perfection you have not proven.
6. **Fix defects against intent; do not redesign.** The user's brief and existing design decisions win over your taste. Judges find what is broken, not what they would have done differently.

## The loop at a glance

```
0. CONTRACT     write down what "perfect" means for this task
1. REPRODUCE    (bug fixes) see the user's problem with your own eyes first
2. BUILD / FIX  make the change
3. CAPTURE      screenshot the real running result across the full matrix + automated checks
4. JUDGE        parallel independent judges review the evidence
5. TRIAGE       verify each finding is real, log it in the ledger
6. FIX          root-cause fixes, then go back to 3 (full recapture, never partial)
7. EXIT         only when the exit criteria below are all true, then report honestly
```

Keep working files in `.perfection/` at the project root (add it to `.gitignore` if the project has one, and mention it to the user once). Contents: `contract.md`, `ledger.md`, `round-N/` folders of screenshots and judge reports.

## Step 0: Contract

Before touching anything, write `.perfection/contract.md`. Judges are only as good as the standard they are held to, and "make it good" is not checkable. Include:

- **Goal**: one sentence.
- **Acceptance criteria**: concrete, checkable statements. Derive them from the request, from any screenshot the user sent, and from the existing design system in the codebase. "The Save button is fully visible and not clipped at 375px width" is checkable. "Looks nice" is not.
- **Do-not-change list**: what is out of scope and must stay identical.
- **Verification matrix**: viewports, states, themes, and flows that matter here (see `references/capture.md` for defaults).
- **Design mode**: pick one (from Impeccable). *Persuade* (landing pages, marketing: earn attention), *Operate* (app UI, dashboards, tools: scanability and consistency outrank expression), *Read* (docs, articles: comprehension first), *Experience* (portfolios, showcases: the artifact leads). Judges weigh things differently per mode.
- **Locked decisions**: choices already made and accepted (the user approved the palette, the layout is intentional). Judges may not reopen these. This is what stops the loop from oscillating.

If the user attached a screenshot of a problem, describe precisely what is wrong in it and make "that specific thing is gone, in that same view" acceptance criterion #1. The user's own reports are never disputable.

## Step 1: Reproduce (for bug fixes)

Capture the broken view yourself before fixing anything, at the same viewport and state as the user's screenshot if you can infer it. If you cannot reproduce it, say so and ask for the viewport, browser, or steps. Do not "fix" a problem you have not seen; you will fix the wrong thing and declare victory.

## Step 3: Capture

Follow `references/capture.md`. The essentials:

- Run the real app (dev server or built output) and drive a real browser. Not the code, not your mental model.
- Capture the full matrix from the contract: multiple viewports, relevant states (hover, focus, open menus, empty, loading, error, long content), light and dark if supported, reduced motion.
- Run the automated checks (`scripts/capture.py` does console errors, failed requests, horizontal overflow, broken images, small tap targets, missing alt/lang/title).
- **Look at the screenshots yourself** with the image viewer. Before judging, write two or three plain sentences per key screenshot describing what is literally visible. This forces real looking instead of assumed looking.
- If you truly cannot run a browser, say so explicitly, do the strongest verification you can (build, typecheck, tests, DOM inspection), and tell the user visual verification did not happen. Never imply it did.

## Step 4: Judge

Dispatch the judge panel **in parallel as separate sub-agents**. The full prompts live in `references/judges.md`; read that file now and use them verbatim, filling in the placeholders.

Each judge receives only: the contract, the paths to evidence (screenshots, automated report, relevant source files where its rubric says so), its rubric, and the output schema. Each judge must **not** receive: your reasoning, your opinion of the work, what you intended, or other judges' findings. Anchoring on any of these makes them agreeable, and agreeable judges are useless.

**The panel:**

| Judge | Owns |
|---|---|
| A. Requirements | Contract compliance, the user's original complaint, scope creep, silently dropped requirements |
| B. Layout | Spacing, alignment, overflow, clipping, responsiveness, imagery |
| C. Design craft | Hierarchy, typography, color, consistency, distinctiveness |
| D. Interaction & UX | States, feedback, flows, forms, dead ends |
| E. Accessibility | Contrast, focus, keyboard, semantics, touch targets |
| F. Motion | Animation purpose, easing, duration, performance, reduced motion |
| G. Copy | Microcopy, labels, errors, empty states, invented content |
| H. Technical | Console, network, build, lint, layout shift, automated report |
| I. Regression | Before/after comparison. Round 2 onward. |

**Scale the panel to the change, but never to your confidence:**
- *Light* (a CSS tweak, one bug fix): A, B, H, I, plus any judge whose area the change touches.
- *Full* (new component, new page, redesign, anything with interaction or motion): the whole panel.
- When unsure, go Full. Under-reviewing is the failure mode; over-reviewing only costs tokens.

**No sub-agents available?** Run each judge as its own sequential pass. Between passes, discard your build intent: re-open the screenshots fresh, read only that judge's rubric, and write its report to `.perfection/round-N/judge-X.md` before starting the next. This is weaker than true independence because you still carry the bias, so compensate by being harsher and by making the evidence rule strict.

## Step 5: Triage

1. **Verify each finding is real.** Open the cited screenshot region and look. Judges hallucinate sometimes. A finding you cannot see is a false positive: mark it `disputed` with what you saw instead. Only evidence can dispute a finding, never "I think it is fine".
2. **Merge duplicates** across judges into one ledger entry.
3. **Log everything** in `.perfection/ledger.md`:

```
| ID | Sev | Status | Round found | Where (screenshot @ viewport/state) | Observed | Fix attempts |
```

Statuses: `open`, `fixed` (fixed and awaiting re-review), `verified` (a later clean review confirmed it), `disputed` (with evidence, re-checked by next round), `waived` (P3 only, with a written reason).

**Severity:**
- **P0** Broken. Crash, blocked flow, unreadable, content missing, the reported bug still present.
- **P1** Clearly wrong. Visible layout break, overlap, clipping, contrast failure, broken state, console error.
- **P2** Noticeably off. Inconsistent spacing, weak hierarchy, awkward wrap, missing state, jarring motion.
- **P3** Fine detail. 1-2px misalignment, minor copy tweak, subtle polish.

## Step 6: Fix

- Find the **root cause**, not the symptom. If a button is clipped, ask why, then check whether the same cause clips other things.
- Make the smallest change that fixes it. Do not touch what is not broken.
- Respect locked decisions and the do-not-change list.
- After fixing, **look at the result yourself first**, then return to Step 3 with a **full recapture**. Never re-check only the thing you fixed.
- Watch for CSS traps: selector specificity cancelling out padding or margin between sections, `transition: all`, fixed pixel widths, z-index wars, missing `min-width: 0` on flex children, `100vh` on mobile.

## Exit criteria

Stop only when **all** are true:

1. The last full recapture happened on the final code, with no edits since.
2. The most recent judge round returned **zero** defects, and every zero-finding report lists what it inspected.
3. The ledger has no `open` or `fixed` entries. Every `P3` is `verified` or `waived` with a reason.
4. Every acceptance criterion in the contract is ticked with a pointer to the screenshot that proves it.
5. The automated checks are clean.

If a round finds even one defect, you are not done. Fix, recapture, rejudge.

## Being stubborn without thrashing

Loops fail two ways: quitting early, and spinning forever. Guard against both.

- **Per-defect stall**: if the same defect survives 3 fix attempts, stop patching. Re-read the relevant code end to end, question your diagnosis, and try a structurally different approach (simplify, remove the competing rule, rebuild the component). Log what you learned.
- **Whole-loop stall**: if two consecutive rounds do not reduce the open-defect count, or you are at round 8, stop looping. Something is wrong with the approach or the judges are oscillating.
- **Oscillation**: if a fix for judge X breaks judge Y's criterion, that is a real tension. Do not keep trading. Pick the option that satisfies the contract, record it as a locked decision, and tell the user about the trade-off.
- **When stopped**: report honestly what remains, what you tried, and your best recommendation. An honest "3 issues remain, here is why" beats a false "perfect".

## Non-visual work

The same loop applies anywhere "done" can be faked. Swap the evidence: run the tests, execute the CLI, call the endpoint, read the logs, diff the output against the expectation. Judges then read real output instead of screenshots. Rule 1 still holds: never report success on something you did not execute.

## Final report

Keep it short and honest. The user does not want a victory lap, they want to know what is true.

```
Verified: <what, across which viewports/states/themes>
Rounds: <n>   Defects found: <n>   Fixed: <n>   Waived: <n> (reasons)
Evidence: .perfection/round-<last>/ (screenshots), .perfection/ledger.md
Not verified: <e.g. real iOS Safari, screen reader, slow network, real device>
Open issues: <none, or list with what was tried>
```

Never write "perfect" or "no issues" unless the exit criteria are literally met. Always list what you did not or could not verify.
