---
name: evidence-video-kit
description: Turn real business evidence - Excel/spreadsheet exports, Power BI/PDF reports, real email or Outlook screenshots, real internal HTML tools/dashboards, and live public APIs (GitHub/npm stats) - into board-deck-ready or launch-ready HyperFrames video assets. Four patterns it knows: (1) animated data/stat visuals with count-up numbers and chart reveals sourced from actual spreadsheet or dashboard data, (2) mockup "typing" animations of real email/document correspondence with narration-friendly pacing and highlighter-marker emphasis on key figures, (3) continuous-scroll "product tour" walkthroughs of real internal tools/dashboards (actual HTML platforms, not slide decks) using one virtual-camera pass instead of scene-cuts, (4) quick-hit cards - one-sentence stat cards with live-fetched date-stamped numbers, staggered list cards, and reusable parameterized series/intro cards - as full-frame MP4 or transparent alpha overlays for placing on footage. Use this whenever Evyatar needs to turn client or business proof - ROI numbers, adoption stats, real tool screenshots, real correspondence - into presentation video evidence for board decks, investor updates, client case studies, ROI reports, workshop deliverables, or sales enablement. Trigger on Hebrew: "תעשה מזה אנימציה", "תהפוך את הדאטה לוידאו", "אנימציה לדשבורד", "וידאו הוכחה", "תדגים את הפלטפורמה", "סיור וידאו בכלי", "אנימציית מייל", "תנפיש את האקסל הזה"; English: "animate this spreadsheet", "turn this dashboard into a video", "product tour of our tool", "email typing animation", "data video from this report", "board deck animations", "proof video from real data". Skip when the ask is a generic branded launch teaser/opener with no real data or tool to recreate (use hyperframes-launch-video instead), raw recorded footage needs trimming or captioning (use agent-video-editor), or the deliverable is a slide deck file rather than a video (use presentation-from-content or slideshow-from-photos).
---

# Evidence Video Kit — Real Data to HyperFrames Proof

> Born from the a client board-deck project (2026-07-12): 16 HyperFrames videos built from a client's real PPTX screenshots, Excel exports, and internal HTML tools. Everything below is a hard-earned lesson from that build, not theory.

The job this skill does: someone has real proof that something worked - a spreadsheet of adoption numbers, a screenshot of an email where a colleague says "this saved me three days," a real internal dashboard - and it needs to become a short, polished video for a presentation. The proof already exists. The work is turning it into motion without losing its authenticity, and without inventing anything that isn't real.

This is a **recipe skill** on top of the core HyperFrames skills. Read `/hyperframes` first if you haven't already - it routes to `hyperframes-core` (the composition contract), `hyperframes-animation` (motion patterns), and `hyperframes-cli` (the render loop). This skill tells you *which* patterns to reach for and what actually goes wrong when you build these three specific kinds of videos, so read this alongside those, not instead of them.

---

## The rule above all the other rules: never invent

Every number, name, quote, and screenshot in these videos has to trace back to something real the client gave you. Before writing a single line of composition HTML:

- **Unzip PPTX files** (`unzip deck.pptx -d out/`) and read the embedded images in `ppt/media/` directly - old decks often have the exact screenshots (emails, dashboards) you need, already cropped and ready.
- **Read Excel/PDF exports with the actual tool** (`xlsx` skill, `pdf` skill, or `openpyxl`) rather than trusting a summary someone wrote about them.
- **If a real HTML tool exists, read the whole file**, not just the visible top. Grep for section markers, tab IDs, or scroll past the first `Read` truncation - dashboards routinely have 3-4x more real content below the fold than what's visible in a screenshot. Missing this is the single most common complaint this skill exists to prevent.
- **When two sources disagree slightly** (a hand-computed spreadsheet stat vs. an already-published dashboard screenshot of the same number), prefer whichever one is already "approved" and consistent with numbers used elsewhere in the deck, and note the discrepancy rather than silently picking one. Don't spend an hour reconciling raw data when a polished, client-approved screenshot of the same metric already exists.
- **If a decision is genuinely ambiguous** (which of two similar screenshots to use, how to phrase something not explicitly given), make the most reasonable call, write it down in a short notes file next to the output, and keep moving. Don't stall a real deliverable on a question that has an obvious-enough answer.
- **Public data counts as real data - go get it.** If the number lives in a public API (GitHub stars, npm downloads, a public dashboard), fetch it live at build time instead of typing it from memory or asking for it. Then **date-stamp the graphic** ("as of 13.07.2026", or the date range on the chart) so it stays honest after the number moves on.
- **Let the data veto the headline.** If the framing someone asked for ("trend up!") isn't what the real data shows, change the framing, not the data - lead with the number that IS true (a total, a peak day) and say so in the notes.

---

## Pattern 1 — Animated data/stat visuals

Spreadsheet or BI-report data becomes a short (6-10s) motion graphic: a hero number counting up, one dominant chart, a one-line caption underneath. This is squarely `/motion-graphics` territory ("stat count-up", "chart hit") - use that workflow, but apply these specifics:

- **One hero per beat.** Don't cram three charts into one slide because the source dashboard had them side by side. Pick the number that matters most and let everything else be secondary or cut.
- **Brand palette discipline.** Data/info slides in a formal deck usually want a calmer, lighter treatment than a title slide's full brand expression - confirm which palette/mood applies to "data slides" specifically before building four of them the wrong way.
- **Reserve the logo zone, don't fake the logo.** If the deck's logo gets placed manually afterward (common - Evyatar embeds real client logos himself), leave the exact negative-space rectangle empty; don't draw a placeholder mark there. But if this video represents an *official branded report itself* (e.g. it's a recreation of a real Power BI report that already has the company's logo baked into its own screenshots), use the real logo PNG asset - copy it into the project and `<img>` it in, never recreate a real company's logo from CSS/SVG shapes. Ask which situation you're in if it's not obvious from the brief.
- **The label carries the why.** When a chart highlights a data point, a bare number reads as random ("122,341" - so what?). Make the callout say why it's flagged: "PEAK DAY · JUN 21". Same for any hero stat - the one-line caption under it is where the meaning lives.
- **Measure alignment, don't eyeball it.** "This still looks off-center" is the most common revision request on these slides, and guessing at pixel offsets from a screenshot wastes a whole revision round. Instead: load the actual rendered composition in headless Chrome (Puppeteer), seek the GSAP timeline to a settled frame (pass `seek(t, false)` - the default `suppressEvents: true` will skip `onUpdate` callbacks and give you stale/zeroed values), and read the real `getBoundingClientRect()` for every element in question. Pick ONE consistent content bounding box for the slide (usually: from the leftmost real element to the rightmost real element in the row above) and align every other element - cards, captions, callouts - to that same box's left/right/center, not to the full frame width. Re-measure after the fix to confirm the numbers actually match before re-rendering.

---

## Pattern 2 — Mockup typing/correspondence animations

A real email, Slack message, or document gets "typed out" on screen to dramatize someone using a tool in the moment - usually to prove "AI helped write this in minutes." Build this as a custom `/general-video` composition (or a lighter `/motion-graphics` piece if it's very short):

- **Readable pace, not a speed-typing flex.** These get talked over live. Default to a pace where a viewer can actually read along - if the first cut plays too fast, extend the total runtime rather than compressing the text. There is no fixed "correct" WPM; when in doubt, err slower and let feedback correct you.
- **Highlight the payoff, don't just type prose.** Add a yellow highlighter-marker sweep (semi-transparent, slightly rough marker-style edge, not a clean rectangle) over the 1-2 phrases that carry the actual value - a dollar figure, a time-savings comparison, a standout quote - animated in as a quick sweep right after that line finishes appearing. This is what makes the clip land in three seconds of screen time during a live talk instead of requiring the presenter to read the whole paragraph aloud.
- **Recreate the real UI chrome when it's visible in the source.** If the original screenshot shows Outlook's ribbon/avatar/reply buttons, rebuild that chrome faithfully - it reads as authentic evidence, not a generic mockup. If the source is a plain webmail compose view, a simpler recreation is correct and matches.
- **Keep the original language.** If the real correspondence is in Hebrew (or whatever language the business actually operates in), keep it in that language even if the rest of the deck's on-screen copy is in English - this is dramatized real evidence, not deck copy, and translating it breaks the "this really happened" effect.

---

## Pattern 3 — Product tour walkthroughs of real tools

A real internal HTML dashboard/tool (not a slide, an actual working page) needs to look like it's being demonstrated live - think a SaaS product-demo video, but of software that already exists and has real data in it. This is a `/general-video` build; the technique matters more than the workflow choice:

- **One continuous camera, not scene-cuts.** Lay the entire real page out at true scale/colors as one tall "world," and drive a single GSAP object's `x`/`y`/`scale` down through it - panning and zooming to highlight specific numbers or cards, then pulling back and continuing - rather than cutting between discrete cropped scenes. A scene-cut version reliably gets the feedback "this only shows the top part" even when every section was technically included, because cuts don't communicate continuity or completeness the way a single scroll does. Reserve discrete cuts for genuine tab switches (with an honest cursor-click transition), not for moving between sections of the same view.
- **Cover the real page end to end.** Read the *entire* source file first (see "never invent" above) and list every real section before deciding what to include - don't build off a partial read and discover the gap from a revision request.
- **Represent stubs and empty states honestly.** If a tab or section in the real tool genuinely has placeholder/fallback content ("data not available in this context"), show that as-is rather than inventing a fuller chart to fill the space. It's more credible, not less.
- **The closing beat is ambiguous by default - ask, or offer both.** "Add a summary at the end" can mean either (a) a consolidated stats recap pulling the headline numbers together, or (b) a literal mosaic/grid of the real screens already built, shown together at a glance. These are genuinely different deliverables. If it's not specified, build the mosaic first (it's cheaper - screenshot your own already-built scenes via `hyperframes snapshot` and lay them into a grid, don't re-author content) and mention the stats-recap as an easy add-on if wanted.

---

## Pattern 4 - Quick-hit cards and reusable brand moments

The floor for a motion graphic is one sentence with one real fact in it. No file, no design reference, no data export needed. Three card shapes cover almost every "small but worth posting/presenting" moment:

- **The stat card** (~5s): one number that matters - signups, downloads, a milestone - slams in and counts up. If the number is public, fetch it live and date-stamp the card (see the never-invent rules). This is the cheapest possible win; reach for it before assuming a video needs to be a bigger production.
- **The list card set** (~5-8s): when the update is three facts, not one, a bullet list dies in the feed - three cards that stagger in one at a time get read in order, at your chosen pacing. The brief should specify the *sequence and pacing* ("cards arrive one at a time, each number pops a beat after its card lands"), never a named effect.
- **The reusable series/intro card**: a brand moment built once and re-rendered forever - a "Day N" cold-open, an episode number, a weekly-recap header. Parameterize the one thing that changes (the number, the date) so the next instance is a one-line edit and a re-render, not a rebuild. If a card like this is being built for the second time, that's the signal to stop and parameterize it.

Two production notes that apply across all card shapes:

- **Transparent overlay output is an option, not just full-frame MP4.** HyperFrames renders alpha WebM/MOV overlays - use that when the moment should sit ON footage (a badge, a lower-third, a count-up in the corner of a screen recording) rather than be its own standalone card. Say which one the deliverable is in the brief.
- **Figma brand files are already animation-ready.** If the logo/lockup lives in Figma, the `/figma` integration pulls it as separate vector pieces (marks, wordmark, individual letters) - which means each piece can animate independently (marks fly in, wordmark builds letter by letter) with zero redrawing. Prefer that over animating a flattened PNG whenever a Figma source exists; and respect the brand's own composition rules when animating (if the guidelines say two marks never touch, they land apart).

## Briefing the motion: describe the outcome, not the effect

This applies to every pattern above, and doubly when dispatching sub-agents: never name easing curves, effects, or transitions in a brief ("elastic bounce", "cross-dissolve"). Describe what the viewer should understand and in what order ("the density is the message - names flood in fast then settle into a readable grid", "the peak day should be the one thing you remember"). The motion design is the builder's job; the communication goal is the brief's job. Briefs written this way survive being handed to a different agent, a different tool, or a future version of HyperFrames - effect-name briefs don't.

## Pacing for live narration

Every video built with this skill has one specific job that differs from a typical social clip: **someone will be talking over it live**, in a boardroom or a meeting, at the same time the audience is trying to read it. That changes the default pacing math:

- Bias toward slower, fully-legible holds over snappy short-form pacing. A 7-second stat clip and a 45-second full product tour are both fine outputs of this skill depending on how much real content there is - don't compress a tour to hit an arbitrary "short video" instinct.
- When asked to slow something down, **extend hold/dwell time first** (the pause once content has finished revealing) rather than the reveal/travel animation itself - viewers need static reading time more than they need a slower reveal.
- When asked to speed something up slightly, do the reverse - trim hold time before touching the choreography.
- A "little slower" request means a ~10-20% runtime nudge, not a doubling. If a request is ambiguous about degree, make a modest change and say what you changed - it's cheap to nudge again.

---

## Verification before calling it done

Every clip, before it's reported as finished:

1. `npx hyperframes lint` and `npx hyperframes check` (or `validate`/`inspect` on older CLI versions) - zero errors, including WCAG contrast checks on text.
2. A `hyperframes snapshot` pass at a few key timestamps, actually looked at (via the Read tool on the snapshot images), not assumed correct from the compiled HTML.
3. After rendering: `ffprobe` to confirm real duration, resolution, codec, and that there's no unexpected audio track. Report the actual measured numbers, not the target you were aiming for.

---

## Orchestrating a multi-asset project

A real deliverable is rarely one video - it's five, ten, sometimes fifteen independent clips for one presentation. Two things make this tractable:

- **Dispatch one background agent per independent asset**, each with a fully self-contained brief: the real extracted content inlined directly in the prompt (don't make the agent re-discover source files you already found), the exact output filename and shared destination folder, and the specific pattern (1/2/3 above) to follow. Launch them together so they render in parallel rather than one at a time.
- **Revisions go to the specific agent that built the file, by resuming it**, not by re-briefing from scratch or spawning a fresh one that has to rediscover context. When feedback comes in on one file, relay it precisely (quote what's wrong, point at the real coordinates/content if you have them) to that agent's existing thread.
- **If feedback reveals your own instruction was ambiguous** (this will happen - "add a summary slide" is a classic case that can mean two very different things), say so plainly when relaying the correction rather than treating it as the agent's mistake, and give the sharper instruction.

---

## House style carries into on-screen text too

Any on-screen caption or label text is still Evyatar's content and follows his house style rules even though it's rendered inside a video, not a document - most importantly: never use an em dash (—); use a regular hyphen with spaces (` - `) instead. Check `C-core/voice-dna.md` for anything else that applies to on-screen copy specifically.

---

## Related skills

- `/hyperframes` - always the entry point; routes to the domain skills below
- `/hyperframes-core` - the composition contract (data-* timing, clips, tracks) - read before writing any composition HTML
- `/hyperframes-animation` - motion patterns, count-ups, reveals, camera/viewport techniques
- `/hyperframes-cli` - the init/lint/check/render loop
- `/motion-graphics` - the right workflow for short, self-contained Pattern-1-style stat/chart/map pieces
- `/general-video` - the right workflow for the more custom Pattern-2 and Pattern-3 builds
- `hyperframes-launch-video` (this GenOS library) - use instead when there's no real data/tool to recreate, just a brand concept and a generic launch/opener feel
- `agent-video-editor` (this GenOS library) - use instead when the input is raw recorded footage that needs trimming/captioning, not a data source or a live HTML tool
