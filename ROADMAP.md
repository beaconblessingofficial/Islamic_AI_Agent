# Islamic_AI_Agent — Production Roadmap

> Companion to `TODO.md` (which is the source of truth for granular tasks). This document adds the **prioritization**, **sequencing**, and **judgment** that the granular list doesn't carry. It is a strategic view, not a task list — the tasks are in `TODO.md`.

---

## 0. Strategic Frame

### What "fully autonomous Islamic media agent" actually means

For a system to qualify as autonomous in the way `prompt.txt` describes, it must do **all six** of these, daily, without intervention:

| # | Capability | Failure mode if missing |
|---|---|---|
| 1 | **Schedule** — wake up N times per day on its own | Manual cron, breaks the first time you forget |
| 2 | **Select** — pick a verse that satisfies the variety guards (no recent repeats, no same-theme twice, no same-nasheed twice) | Audience sees the same verse three days in a row, unsubscribes |
| 3 | **Render** — produce a clean image, a clean reel, and a clean caption, every time, no human QA | A misaligned Arabic glyph ships; reputation damage |
| 4 | **Publish** — post to N platforms with platform-specific caption formatting | Only posts to one channel; growth stalls |
| 5 | **Recover** — handle every transient failure (network, API rate-limit, OOM) without human intervention | One bad day, the agent goes silent for a week |
| 6 | **Audit** — log every run with inputs/outputs/costs; keep a scholar-reviewable trail | You can't defend the content when challenged |

Anything short of all six is "automated Instagram poster," not "autonomous media agent."

### The principle

**Ship the smallest thing that satisfies all six with the smallest possible surface area, then expand.** Concretely: one platform, one account, English-only, rule-based captions, manual scholar review, 50-verse corpus, one nasheed pool. Prove the loop runs unattended for 14 days. Then add surface area. The alternative — building every feature in parallel — is the path to a project that does 80% of everything and 0% reliably.

---

## 1. What the Existing `TODO.md` Gets Right

The roadmap you wrote is unusually good. The things I'd preserve verbatim:

- **6-phase structure** — housekeep → image → reel → caption → publish → polish. This is the right order.
- **Phase 0 is load-bearing** — the "do not skip ahead" rule is correct. Everything downstream depends on the `image_gen.py` bugs being fixed first.
- **Granular tasks with `verify:` clauses** — every TODO item has a concrete acceptance test. This is rare and valuable.
- **Scholar review as a hard gate** — Phase 6.1 is the *most important* Phase 6 task, and you correctly called it out. Reputational risk is the biggest risk in this project; everything else is mechanical.
- **Public APIs only (X-07)** — no `instagrapi` scraping. Correct call; scraping accounts get banned.
- **Pydantic for boundaries** — every adapter has a typed contract. Good.

---

## 2. Where I'd Push Back

Five concrete disagreements with the existing plan. Each is an *edit* to `TODO.md`, not a contradiction of it.

### 2.1 The "≥200 verses" target should be staged

200 verses at 3 posts/day gives ~67 days of unique content before any repeat. With the variety guards (no theme repeat, no verse repeat in 30 days, no nasheed repeat in 7 days), the effective content space is smaller — closer to 40-50 days. That's a quarter, not a year.

I'd stage it:

| Stage | Target | Daily cadence | Repeat cycle | What it unlocks |
|---|---|---|---|---|
| Smoke | 50 | 1/day | ~7 weeks | "Autonomy works" demo |
| MVP | 200 | 1/day | ~7 months | First paying-month subscription |
| Quarterly | 500 | 2/day | ~3 months | Two-posts-per-day cadence |
| Year 1 | 1,100 | 3/day | ~12 months | Full year of 3/day, no repeats |

`TODO 1.1.2` says "≥200." I'd add a `1.1.6` saying: "Curation target for 1.1.2 is 200. 500 is the year-1 stretch goal; defer to Phase 6 if shipping a one-quarter agent first."

### 2.2 Phase 4 should run in parallel with the human-facing OAuth paperwork

`TODO 4.2.1` says "Document setup in docs/instagram_setup.md ... Do not script this." That's right — but the rest of Phase 4 is *blocked on the doc*, which is wrong. The doc can be written in week 1. The publisher code can be written and tested with `--dry-run` in week 2. The first real publish can wait for the human to finish the Facebook app review in week 3-4. A senior engineer parallelizes: the human paperwork and the code work are independent.

I'd add a Phase 4.0 task: "Write all three platform setup docs (`docs/instagram_setup.md`, `docs/facebook_setup.md`, `docs/youtube_setup.md`) in the first 3 days. These are independent of code." Then everything from 4.1 onward can ship without blocking on real credentials.

### 2.3 The Phase 6 polish is large; an MVP can ship at end of Phase 5

Phase 6 has 10 sub-phases. Some of them (6.1 scholar review, 6.4 cost caps, 6.5 backup) are *production* — must-have. Others (6.6 multi-language, 6.7 thumbnails, 6.8 A/B testing, 6.9 Sentry) are *polish* — nice-to-have, defer past MVP.

I'd re-categorize Phase 6:

- **6.A — Required for MVP:** 6.1 scholar review, 6.2 licensing log, 6.3 translation source audit, 6.4 cost cap.
- **6.B — Defer to "after first 1000 posts":** 6.5 backup automation, 6.7 thumbnails, 6.8 A/B testing.
- **6.C — Defer to "after year 1":** 6.6 multi-language, 6.9 Sentry.

Re-numbering `TODO 6.x` to match would make the priority clear.

### 2.4 Missing: rate-limit handling and ban-avoidance

The TODO has a `NetworkError` retry story (5.7.3) but no `429 Too Many Requests` handling, no `Retry-After` honoring, no backoff across multiple posts, and no shadowban-avoidance posture (e.g., varying hashtags day-to-day, not using the same 30 hashtags every post, watching for engagement cliffs). These are *real risks* for an autonomous agent on Instagram and YouTube.

I'd add a new section, say `5.13 — Platform rate limits and account health`:

- 5.13.1: Honor `Retry-After` headers on every 429.
- 5.13.2: Per-platform daily post cap (Instagram: 25/day; YouTube Shorts: 15/day; Facebook: 50/day) — the orchestrator refuses to exceed.
- 5.13.3: Hashtag rotation — never post the same 30-tag set twice in 14 days.
- 5.13.4: Engagement cliff detection — if a post's engagement drops 50% vs. the previous 7-day average for that theme, mark the theme "watch" in the report.

### 2.5 Missing: time-zone-per-audience

The TODO has `TIMEZONE=UTC` and a single `SCHEDULE_TIMES=08:00,13:00,20:00`. For a media company posting to a global Muslim audience, the *audience's* 8 AM matters more than the agent's 8 AM. A user in Karachi sees the 8 AM UTC post at 1 PM their time — fine. A user in London sees it at 9 AM — borderline. A user in California sees it at midnight — wrong.

For MVP: keep UTC. For multi-account / multi-region: each account has its own `TIMEZONE` and `SCHEDULE_TIMES` in the config. Add a `5.14 — Per-account scheduling` task that defers this to month 2+.

---

## 3. The Critical Path

These are the 10 tasks (or task groups) that, in order, unlock "agent runs unattended daily, posts to one platform, recovers from errors, keeps a scholar-reviewable trail." Everything else is *important* but not critical-path.

| # | Task | Origin | Effort | Blocks |
|---|---|---|---|---|
| 1 | Phase 0 housekeeping (0.1, 0.2) | TODO 0.1, 0.2 | 4-6 hours | Everything |
| 2 | Expand corpus to 50 (smoke), 200 (MVP) | TODO 1.1 | 8-20 hours | Phase 2-3 |
| 3 | SQLite history DB | TODO 2.2 | 4-6 hours | Orchestrator, publishers, analytics |
| 4 | Reel generator | TODO 2.3-2.9 | 12-18 hours | Phase 4 |
| 5 | Caption generator (rule-based only) | TODO 3.1-3.6 | 6-10 hours | Phase 4 |
| 6 | One publisher (Instagram, with `--dry-run`) | TODO 4.1-4.2, 4.6 | 8-12 hours | Live posting |
| 7 | Orchestrator with variety guards | TODO 5.1-5.3 | 6-10 hours | Scheduling, live posting |
| 8 | Scheduling (APScheduler) + kill switch + retry | TODO 5.4-5.8 | 4-6 hours | Unattended operation |
| 9 | Logging + run manifests | TODO 5.6 | 2-4 hours | Auditing, debugging |
| 10 | Scholar review queue | TODO 6.1 | 6-10 hours | Live publish to real audience |

**Total critical path:** 60-100 hours of focused work, ~6-10 weeks at 10-15 hours/week.

If you only have 30 hours, you can stop after tasks 1-3 and have a system that *generates* content correctly but doesn't post. If you have 60 hours, you can stop after tasks 1-5 and have local-only content (no scheduling, no publishing). If you have 100 hours, you have the full critical path.

---

## 4. Roadmap in 4 Horizons

### Horizon 1 — Stabilize (1-2 weeks, 15-25 hours)

**Goal:** clean, package-discoverable, tests-runnable code that produces a correct image on demand.

**Tasks (in order):**

| Priority | Task | Time | Why first |
|---|---|---|---|
| P0 | 0.2.12 — Add `.gitignore` | 5 min | Prevents future secret leaks |
| P0 | 0.2.11 — Add `.env.example` | 10 min | Establishes config schema |
| P0 | 0.2.1 — Add `scripts/__init__.py` | 1 min | Enables `python -m scripts.…` |
| P0 | 0.2.2-0.2.4 — Move 17 diagnostic scripts to `scripts/_legacy/` | 15 min | 50% noise reduction |
| P0 | 0.2.5-0.2.6 — Move `test_*.py` to `tests/`, drop `sys.path.insert` | 20 min | Real test directory exists |
| P0 | 0.2.7-0.2.8 — Delete `-2` duplicates after manual hash check | 10 min | Cleanup |
| P1 | 0.1.1-0.1.7 — Fix image rendering bugs | 2-3 hours | The headline defects |
| P1 | 0.2.13-0.2.15 — Create `scripts/make_post.py`, delete `gen_single.py` | 1 hour | Canonical entry point |
| P2 | 0.2.9 — Move diagnostic PNGs to `output/_archive/` | 15 min | Output folder cleanliness |
| P2 | 0.2.10 — Rewrite `requirements.txt` with full dependency set | 15 min | New contributors can `pip install` |
| P3 | 6.A.1 — Scholar review SOP document (just the doc, not the code) | 1-2 hours | Parallel work; needed before any real publish |

**Exit criterion:** `python -m scripts.make_post --count 5 --theme Guidance` from a fresh venv produces 5 images with no boxes, no overlap, no duplicates, in under 30 seconds. `python -m pytest tests/` discovers and runs both test files. `output/` contains only `post_*.png` files.

**What you can defer:** anything in Phase 1-6 that isn't listed above.

### Horizon 2 — Local MVP (2-4 weeks after H1, 40-60 hours)

**Goal:** a complete content-generation pipeline that runs end-to-end locally, no network calls, no scheduling.

**Tasks (in order):**

| Priority | Task | Time | Why |
|---|---|---|---|
| P0 | 1.1.1-1.1.5 — Audit + expand corpus to 50 verses (smoke target) | 8-12 hours | Unblocks reel/caption gen |
| P0 | 1.2.1-1.2.3 — Convert themes to JSON, expand to 10-15 themes | 3-4 hours | Drives theme-aware everything |
| P0 | 1.3.1-1.3.10 — Promote data layer (`database/dao.py` already exists; add methods, write tests) | 4-6 hours | Clean DAO for orchestrator |
| P0 | 1.4.1 — Concurrency-safe used-verse writes (file lock) | 2 hours | One parallel run, no double-pick |
| P0 | 1.5.1-1.5.5 — Theme-aware image gen + `--theme`/`--count` flags | 4-6 hours | The "theme-driven" capability |
| P0 | 2.2.1-2.2.4 — SQLite history DB | 4-6 hours | Every later phase writes here |
| P0 | 2.3-2.7 — Reel generator (full pipeline) | 12-18 hours | The "reel" capability |
| P0 | 2.8-2.10 — `make_reel.py` entry point + smoke tests | 2-3 hours | CLI for reels |
| P0 | 3.1-3.5 — Caption generator (rule-based only) | 6-10 hours | The "caption" capability |
| P0 | 3.6 — `make_caption.py` + tests | 2-3 hours | CLI for captions |
| P0 | 5.1-5.3 — Orchestrator with variety guards (dry-run only) | 6-10 hours | Glues it all together |
| P0 | 5.6 — Logging + run manifests | 2-4 hours | Auditing |
| P0 | Write `README.md` (basic; H4 will polish) | 2 hours | Onboarding |
| P2 | 1.1.2 stretch — Push corpus to 200 | 8-10 hours | If time, do it now; else defer to H3 |

**Exit criterion:** `python -m agent --once --dry-run` produces image + reel + caption + manifest, in under 90 seconds, with zero network calls. `python -m scripts.report --days 1` shows the run. `git log` is clean, no secrets, no `-2` duplicates.

**What you can defer:** any publisher code, any LLM caption code, scheduling, scholar review queue, anything in Phase 6.

### Horizon 3 — First Online (2-4 weeks after H2, 20-30 hours of code + 4-8 hours of human setup)

**Goal:** one real platform, real publishing, daily schedule, scholar review gate, cost cap, license audit.

**Human-facing work in parallel (do this in week 1 of H3, in parallel with code):**

| Task | Time | Notes |
|---|---|---|
| Set up Facebook app | 1 hour | developers.facebook.com |
| Submit app for Instagram Basic Display / Graph API review | 1 hour + 5-10 business days wait | **Start this first; it gates everything** |
| Create Instagram Business account | 30 min | If not already |
| Get long-lived access token | 30 min | After app review |
| Document the entire flow in `docs/instagram_setup.md` | 1 hour | Per TODO 4.2.1 |
| License audit for all 4 nasheeds | 2-4 hours | Search each source; record in `licensing.csv` |
| License audit for the 200-verse corpus's translations | 2-4 hours | Pick a translation source per verse |
| Define which themes require manual review (the "high-risk" list) | 1-2 hours | Per TODO 6.1.5 |

**Code work (in order):**

| Priority | Task | Time | Why |
|---|---|---|---|
| P0 | 4.1.1-4.1.4 — Publisher interface + Engagement Pydantic | 2-3 hours | The abstraction all publishers use |
| P0 | 4.2.1-4.2.5 — Instagram publisher with `--dry-run` | 6-8 hours | First real platform |
| P0 | 4.5.1-4.5.3 — Cross-platform dispatch | 2-3 hours | Multi-platform later |
| P0 | 4.6.1-4.6.2 — `publish.py` entry point | 1-2 hours | CLI |
| P0 | 5.4-5.5 — Scheduling (APScheduler) | 3-4 hours | Daily 8 AM, 1 PM, 8 PM |
| P0 | 5.7 — Failure handling (typed errors, retries, exponential backoff) | 2-3 hours | Self-healing |
| P0 | 5.8 — Kill switch (`STOP.flag`) | 1 hour | Human override |
| P0 | 5.10 — Reporting | 2-3 hours | Operational visibility |
| P0 | 6.1.1-6.1.6 — Scholar review queue | 6-10 hours | Reputational safety |
| P0 | 6.2.1-6.2.3 — Licensing log | 2-3 hours | Compliance |
| P0 | 6.3.1-6.3.4 — Translation source audit | 1-2 hours | Compliance |
| P0 | 6.4.1-6.4.4 — Cost cap (`LLM_DAILY_BUDGET_USD`) | 2-3 hours | Budget safety |
| P0 | 5.13.1-5.13.4 — Rate-limit handling (new) | 2-3 hours | Account health |
| P1 | 4.7.1-4.7.3 — Publisher tests with mocks | 3-4 hours | Confidence |
| P1 | 5.11.1-5.11.3 — Orchestrator tests | 3-4 hours | Confidence |
| P2 | 5.12.1-5.12.3 — 7-day stability test | 1 week of waiting | Real-world validation |

**Exit criterion:** the agent runs daily at 8 AM for 7 consecutive days, posts to Instagram after a human `--approve` on each post, has zero uncaught exceptions, every post is documented in `licensing.csv`, total LLM cost < $5.

### Horizon 4 — Production (4-8 weeks after H3, 60-100 hours)

**Goal:** second platform, multi-language (Arabic captions), backups, A/B testing, multi-account, full polish.

This is where you should now be ready to look at:
- Phase 4.3 / 4.4 — second platform (YouTube or Facebook)
- Phase 6.5 / 6.7 / 6.8 — backup, thumbnails, A/B
- Phase 6.6 — multi-language (start with `ar` for captions since you already have the Arabic text)
- 5.14 — per-account timezone scheduling (when you have ≥2 accounts)
- 5.9 — engagement polling
- Full README, troubleshooting guide
- 30-day unattended run

**Exit criterion:** agent runs unattended for 30 days, posts to ≥2 platforms, never publishes unapproved content, every failure mode has a documented recovery in the runbook, total LLM cost < $30/month, engagement polling works for every post.

---

## 5. Parallel Tracks (work that doesn't block the critical path)

| Track | Effort | Owner | What it produces |
|---|---|---|---|
| **Brand asset production** | 4-8 hours | Designer (you?) | New logo, color palette, font pairing; replaces the current `templates/logo.png` |
| **Nasheed sourcing & licensing** | 4-6 hours | You | 10-20 nasheeds with documented licenses; matches the 10-15 themes |
| **Translation source licensing** | 2-4 hours | You | Per-verse license map; "Sahih International" / "Pickthall" / etc. annotations |
| **Verse corpus curation** | 20-40 hours | You + 1 scholar | 200+ verses, full tashkeel, valid translations, categorized by theme |
| **Scholar review SOP** | 2-4 hours | You + 1 scholar | Document: what to look for, how to approve, escalation paths |
| **Account & API paperwork** | 4-8 hours | You | Facebook app, Instagram business, YouTube channel, Graph API tokens |
| **README + onboarding** | 2-3 hours | You | Quickstart, env vars, schedule install, troubleshooting |
| **Backup strategy** | 2-4 hours | You | Where to back up `database/post_history.sqlite`, `licensing.csv`, run manifests; how to restore |

These can all run alongside the critical path. The longest is corpus curation — start it in week 1 of H2.

---

## 6. Explicit Cuts / Deferrals

Things I would **not** do in the first 3 months. Each is a real feature in `TODO.md`; each is also a real time-sink that doesn't unlock autonomy. Defer, don't skip.

| Feature | Why defer | When to revisit |
|---|---|---|
| Multi-language (Urdu, Indonesian, Turkish, etc.) | English + Arabic captions (which you already have source text for) covers 80% of the audience. The 4 new languages add weeks of translation work, native-speaker review, and theme-prompt rewrites | After 1,000 posts published in English; pick the highest-engagement non-English audience and add *one* language |
| A/B testing | You need 30+ posts per variant to read signal. You don't have 30 posts at H3 exit. | After 100 published posts |
| Sentry | Manual log reading is enough at MVP scale. Sentry costs $0-26/month and adds a dependency. | When you have 2+ weeks of unattended runs and want to know about errors faster |
| Thumbnails (6.7) | YouTube auto-picks a frame; Instagram uses the reel's first frame; Facebook allows a custom cover. Nice-to-have, not blocking | When you're optimizing for click-through, not just reach |
| Multi-account | One Instagram + one Facebook page is enough to start. Multi-account adds 2-3 days of per-account config | When one account proves out and you want geographic or topical separation |
| TikTok / X / Telegram | Only after 2 platforms proven. Each has a different API, different content norms, different failure modes | After YouTube or Facebook is stable for 60 days |
| Per-account timezone scheduling | UTC works for a global audience. Per-account is a configuration story, not a code story | When you have ≥2 accounts in different timezones |
| Custom themes (beyond the initial 10-15) | Themes 1-15 cover the high-traffic categories. Custom themes are mostly a caption-prompt exercise | When 10 themes all have 30+ posts and you want to expand |
| Backup automation (6.5) | Manual `cp post_history.sqlite backups/$(date).sqlite` once a week is fine for 90 days | When you can't afford to lose a week's history |
| Pydantic 2 for the publisher response models | Simple dataclasses work. Upgrade when you have a real reason | When you need validation on responses |
| Custom LLM providers (Qwen, Gemma, Ollama) | OpenAI + Anthropic cover 95% of users. Ollama is "if you want self-hosting" — separate workstream | If you decide to self-host for cost/privacy reasons |
| RAG (per `prompt.txt`) | Not needed for caption generation. The themes.json + corpus are the entire context. | If you want to add hadith/tafsir context to captions |
| Multi-agent architecture | The orchestrator + adapters *is* an agent architecture. Don't add a second one. | If the orchestrator becomes unmaintainable (it's ~500 lines; that won't happen for 1+ year) |

---

## 7. Risk Register

The 9 things most likely to derail this project, ranked by likelihood × impact.

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **Arabic rendering regresses** | Medium | High (visible to every viewer) | Phase 0.1 fixes; add a smoke test that renders Al-Kahf 18:10 and fails if the output contains boxes or null glyphs |
| 2 | **Corpus quality is below bar** (partial tashkeel, mistranslations) | High | High (every post) | 1.1.4 `has_full_tashkeel=true` validation; scholar review per verse before publish; never publish a verse that hasn't been scholar-approved |
| 3 | **Facebook/Instagram Graph API app review delays** (5-10 business days, can be rejected) | High | Medium (delays H3) | Start the human paperwork in H1, in parallel with code. Have a `--dry-run` ready so the agent works without real credentials |
| 4 | **YouTube OAuth scope tightening** | Medium | Medium | Pin scopes; document them; re-auth quarterly |
| 5 | **LLM cost overruns** (`$5/day` × 30 days = $150/month) | Medium | Medium | Default to `RuleBasedProvider`; only opt into LLM on high-priority content; `cost_usd` in every manifest |
| 6 | **Instagram shadowban** (sudden engagement drop, account warning) | Medium | High | Vary hashtags; never post the same set twice in 14 days; respect rate limits; never use scraped content |
| 7 | **Nasheed licensing violation** | Medium | High (DMCA takedown) | `licensing.csv` enforced; `audit_licensing.py` runs daily; never use a nasheed without documented rights |
| 8 | **Translation attribution missing** | High | Medium (legal/factual) | `translation_source` and `translation_attribution` columns required; 6.3.3 bulk-edit |
| 9 | **Scholar review becomes the bottleneck** | Medium | High (autonomy) | 6.1.5: `--auto-approve-after 24h` for low-risk themes; rotate the scholar; have a backup reviewer |

---

## 8. Decision Points (places I need your call before proceeding)

The plan above makes assumptions. The following are real decisions where I shouldn't choose for you.

| # | Question | My recommendation | Alternatives |
|---|---|---|---|
| 1 | **Which platform first?** | Instagram (largest reach for visual Quran content; Graph API is the most mature; scholar review fits the format) | YouTube (better discovery, but stricter content policies for religious material); Facebook (broadest demographic in Islamic markets, but lower engagement) |
| 2 | **One account or multi-account from day 1?** | One. The configuration story for multi-account is non-trivial and premature | Multi from day 1, if you already have multiple accounts ready |
| 3 | **LLM captions from day 1, or rule-based only?** | Rule-based only for H2-H3. LLM is opt-in via `CAPTION_PROVIDER=openai` in `.env`. LLM is a quality enhancement, not a correctness requirement | LLM from day 1, if you have a working budget and a tested prompt |
| 4 | **Acceptance bar for "fully autonomous"?** | "Runs unattended for 30 days, with scholar review per post, no other human action." That's 6/6 capabilities | "No human at all" — requires the scholar-review step to be automated, which is not safe. Defer to year 2. |
| 5 | **English-only or bilingual captions from day 1?** | English captions + Arabic source text. The Arabic text is already there; the transliteration is Arabic script. | Bilingual (English + Arabic) captions from H3 — small extra work, large audience reach |
| 6 | **Storage for run manifests and SQLite backups?** | Local `backups/` directory + manual weekly copy to OneDrive/Dropbox | Cloud (S3 / R2) from day 1 — costs ~$1/month, but adds an AWS dependency |
| 7 | **Where does the agent run?** | A Windows machine you already have (you're on Win 10), scheduled via Task Scheduler, in the foreground as a console | A $5/month Linux VPS, scheduled via cron or systemd timer, in the background |
| 8 | **How do you back up the database?** | Manual `cp` for H1-H3; automate in H4 with weekly APScheduler job | SQLite + Litestream (continuous replication to S3) — more reliable, more setup |
| 9 | **Translation source for the corpus?** | Sahih International (free with attribution, widely accepted) | Pickthall (public domain) or Yusuf Ali (public domain with notice) — older English; or split per-verse |
| 10 | **One nasheed pool or per-theme pools?** | One pool of 10-20 nasheeds, picked by theme. Simpler to start. | Per-theme pools (defined in `themes.json → themes[theme].nasheed_pool[]`) — more variety, more curation work |

---

## 9. The Very First Session (90 minutes, max value)

If you give me 90 minutes of your time, here's the highest-leverage use of it. Every step is mechanical, low-risk, and directly visible.

| # | Action | Time | Why |
|---|---|---|---|
| 1 | Confirm the `-2` files are byte-identical to their non-`-2` counterparts (run `Get-FileHash` on each pair) | 5 min | Pre-condition for the deletes |
| 2 | Add `scripts/__init__.py` (empty) | 1 min | Enables `python -m scripts.…` |
| 3 | Add `tests/__init__.py` (empty) | 1 min | Enables `python -m pytest tests/` |
| 4 | Add `.gitignore` (TODO 0.2.12) | 5 min | Future-proofs against secret leaks |
| 5 | Add `.env.example` (TODO 0.2.11) | 5 min | Documents the env schema |
| 6 | `mkdir scripts/_legacy` | 1 min | Destination for retired scripts |
| 7 | Move 16 diagnostic scripts to `scripts/_legacy/` (TODO 0.2.4) | 5 min | Removes 75% of `scripts/` noise |
| 8 | Move `scripts/create_post.py` to `scripts/_legacy/create_post.py` (TODO 0.2.3) | 1 min | Removes the second poster |
| 9 | Move `scripts/test_verse_db.py` and `scripts/test_image_gen.py` to `tests/` (TODO 0.2.5) | 2 min | Real test directory |
| 10 | Drop the `sys.path.insert` lines from the moved test files; update imports to `from database.dao import VerseDB` (TODO 0.2.6) | 5 min | Test isolation |
| 11 | Delete the 3 `-2` data files and 6 `-2` font files (after step 1 confirmed duplicates) (TODO 0.2.7-0.2.8) | 2 min | Cleanup |
| 12 | Fix the 3 `print()` debug lines in `paths.py` (remove them) | 1 min | No more stdout noise on import |
| 13 | Verify: `python -m scripts.make_post` runs (or fails cleanly because `make_post.py` doesn't exist yet — that's expected) | 2 min | Sanity check |
| 14 | Verify: `python -m pytest tests/` discovers both test files | 2 min | Sanity check |
| 15 | Update `requirements.txt` per TODO 0.2.10 | 5 min | Dependency manifest |
| 16 | Update `PROJECT_MAP.md` to reflect the new layout | 5 min | Doc stays in sync |
| 17 | Save this roadmap as `ROADMAP.md` at the repo root | 2 min | Persistence |

Total: ~50 minutes of execution. 40 minutes of buffer for the inevitable "wait, the `__pycache__` for `database/` is for Python 3.12 but the venv is 3.14" debugging. You'll exit the session with a repo that has 30% fewer files, a real `tests/` directory, a real `.gitignore`, and a clean canonical layout. **The next session can start on the image rendering bugs (0.1.1-0.1.6) with a clean foundation.**

---

## 10. What I'd Watch For in the First 30 Days

Once you're past H1, three things will tell you whether the project is on track:

1. **Day 7:** Have you generated 50+ unique images without overlap or duplicate verses? If no, the variety guards aren't working.
2. **Day 14:** Has a 30-second reel been generated end-to-end with audio, ken-burns, and timed cards? If no, Phase 2 has a bug to fix before H3.
3. **Day 30:** Has the agent published 1 post to Instagram after scholar review? If no, either the API token isn't set up, the app review is pending, or the publisher has a bug. Any of these is fixable in a day.

If all three are yes at the 30-day mark, you have an MVP. The polish (H4) is *additive*, not *blocking*.

---

## 11. One Sentence Summary

**Build the smallest possible system that runs the variety-guarded verse-to-reel-to-caption loop end-to-end, locally, with a real run manifest and a scholar-review gate, *before* you write a single line of publisher code — and don't ship a daily schedule until the system has produced 50 clean images and 10 clean reels without human intervention.**

---

## Companion Documents

- `TODO.md` — granular task list, source of truth for individual work items
- `PROJECT_MAP.md` — current repo layout (will need an update after H1)
- `prompt.txt` — original system brief
- `output/vocalization_audit.csv` — corpus tashkeel audit (0/25 fully vocalized; drives 1.1.4)
- `output/quran_posts_arabic_audit.txt` — per-verse codepoint audit
