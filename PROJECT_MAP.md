# Islamic_AI_Agent — PROJECT_MAP

A guided tour of every folder and every Python file in the repository, what each one does today, what it should do in the finished agent, and which tasks in `TODO.md` it belongs to.

> **Reading guide:** the project is roughly in two states right now — a working *image generator* (the `verse_db` + `image_gen` core) and a thicket of *diagnostic one-off scripts* that were used to debug Arabic shaping and font loading. The map below calls out which is which.

---

## Repository tree (top level)

```
D:\Islamic_AI_Agent\
├── database\           # Verse corpus, theme metadata, used-verse ledger
├── fonts\              # Local TTF font packages + auto-extracted copies
├── nasheeds\           # Royalty-free background audio (4 MP3s, 2 styles × 2 takes)
├── output\             # All generated images (today) and reels (Phase 2+)
├── scripts\            # All Python source
├── templates\          # Static visual assets: background, logo, separator
├── venv\               # Local virtualenv (do not edit / not committed)
├── requirements.txt    # Pinned dependency list (currently incomplete — see P0-09)
└── TODO.md             # Phased task list (P0 → P6 + cross-cutting)
```

---

## `database/` — content + state

| File | Purpose | Status |
|---|---|---|
| `quran_posts.csv` | Primary verse corpus. 25 rows, columns: `id, surah, ayah, theme, arabic, transliteration, translation, caption_topic`. | Active, but **too small** (P1-01: expand to ≥200). |
| `quran_posts-2.csv` | Byte-identical duplicate of `quran_posts.csv`. | **Junk** — delete (P0-07). |
| `themes.csv` | Theme → hashtag string. 5 themes: Guidance, Forgiveness, Patience, Knowledge, Family. | Active, but **will be replaced by `themes.json`** in P1-03. |
| `themes-2.csv` | Duplicate of `themes.csv`. | **Junk** — delete (P0-07). |
| `used_verses.txt` | Line-per-id ledger of verses already posted. Drives the no-repeat logic in `VerseDB`. | Active; will move into SQLite in P1-08. |
| `used_verses-2.txt` | Duplicate of `used_verses.txt`. | **Junk** — delete (P0-07). |

> **Planned (Phase 1):** `database/dao.py` (was `scripts/verse_db.py`), `database/history.py` (sqlite3 post-history), `database/themes.json`, `database/licensing.csv` (P6-02), `database/schema.sql` (P1-07).

---

## `fonts/` — typefaces

| File | Purpose | Status |
|---|---|---|
| `Amiri-Regular.ttf` | Primary Arabic face used by `image_gen.py` after auto-extract resolves a zip header. | Active. |
| `Amiri-Regular-2.ttf` | Duplicate of the above. | **Junk** — delete (P0-08). |
| `PlayfairDisplay-Regular.ttf` | English face for transliteration / translation / reference. | Active. |
| `PlayfairDisplay-Regular-2.ttf` | Duplicate. | **Junk** — delete (P0-08). |
| `_extracted_fonts/Amiri-Italic.ttf` | Auto-extracted from `Amiri-Regular.ttf` because that file is actually a zipped TTF package (header `PK..`). Currently the *de facto* Arabic font for production output. | Active (extracted at runtime by `image_gen._resolve_font_path`). |
| `_extracted_fonts/Amiri-Italic-2.ttf` | Duplicate extract. | **Junk** — delete. |
| `_extracted_fonts/AmiriQuran.ttf` | Quran-optimized Amiri variant (used by legacy `create_post.py`). | Legacy; not used by `image_gen.py`. |
| `_extracted_fonts/AmiriQuran-2.ttf` | Duplicate. | **Junk** — delete. |
| `_extracted_fonts/AmiriQuranColored.ttf` | Colored glyph variant. | **Junk** (debug artifact). |
| `_extracted_fonts/AmiriQuranColored-2.ttf` | Duplicate. | **Junk**. |
| `_extracted_fonts/PlayfairDisplay-Regular.ttf` | Mirror of the English face. | Active. |
| `_extracted_fonts/PlayfairDisplay-Regular-2.ttf` | Duplicate. | **Junk**. |

> **How fonts are picked at runtime:** `image_gen._get_arabic_font_path` prefers `Amiri-Regular.ttf` (auto-extracts to `_extracted_fonts/Amiri-Italic.ttf` on first run), then falls back to Windows Arabic fonts (`arabtype.ttf`, `tahoma.ttf`, `arial.ttf`).

---

## `nasheeds/` — background audio

| File | Purpose | Status |
|---|---|---|
| `calm_01.mp3` | Calm nasheed take 1. | **Unused** — no code reads this folder today. |
| `calm_01-2.mp3` | Duplicate. | **Junk** — delete. |
| `calm_02.mp3` | Calm take 2. | Unused. |
| `calm_02-2.mp3` | Duplicate. | **Junk** — delete. |
| `emotional_01.mp3` | Emotional take 1. | Unused. |
| `emotional_01-2.mp3` | Duplicate. | **Junk** — delete. |
| `emotional_02.mp3` | Emotional take 2. | Unused. |
| `emotional_02-2.mp3` | Duplicate. | **Junk** — delete. |

> Wired up in **Phase 2** (P2-03): theme-rotated nasheed selection, loop/trim to target reel duration, audio fade-in/out.

---

## `templates/` — static visual assets

| File | Purpose |
|---|---|
| `background.jpg` | Background plate composited under the text in `image_gen.py` (35 % opacity blend). |
| `logo.png` | Brand mark pasted at the top of every post. |
| `separator.png` | Decorative divider rendered between the transliteration and the translation, and again above the reference. |

> All three are read by `image_gen.ImageGenerator` from `assets_dir = BASE / "templates"`. Missing files are tolerated (logo and separator become `None`; the image still generates with a flat background).

---

## `output/` — generated media

| File pattern | Purpose |
|---|---|
| `post_<timestamp>.png` | Production 1080×1080 posts generated by `gen_single.py` / `image_gen.py` / `create_post.py`. |
| `single_sample.png` | Output of `gen_single.py`. |
| `test_arabic_quran.png`, `test_font_*.png`, `font_render_test*.png`, `test_arial.ttf_reshaped.png`, `test_AmiriQuran.ttf_reshaped.png` | Diagnostic images from the various `test_*.py` / `inspect_*.py` scripts. |
| `arabic_font_tests/test_<font>.png` | Per-font render tests from `test_arabic.py`. |
| (214 files total today; ~200 are timestamped `post_*.png` runs.) | |

> **P0-06 plan:** move all non-production images to `output/_archive/`. From Phase 2 onward, also expect `output/reels/<date>_<id>.mp4` and `output/pending/` for `--dry-run` runs.

---

## `scripts/` — Python source

The scripts split cleanly into four groups. Each entry below names the file, what it does, and the `TODO.md` task it belongs to.

### A. Production code (keep)

| File | Role | TODO |
|---|---|---|
| `verse_db.py` | `VerseDB` class: loads `quran_posts.csv`, tracks `used_verses.txt`, validates required columns, picks a random unused verse, auto-resets when exhausted. Atomic write of the used-verse file (`.tmp` + replace). | P1-04: promote to `database/dao.py`, add `select_by_theme`, `list_recently_used(days)`, `soft_reset`. |
| `image_gen.py` | `ImageGenerator` class: composites logo + Arabic (reshaped/bidi-corrected) + transliteration + translation + reference onto the background plate, dynamic font sizing to fit 1080×1080. Has its own `__main__` smoke test. | P0-01/P0-13: pick as canonical, fix the `from scripts.verse_db` import (P0-03), wrap in `scripts/make_post.py` module entry point. |
| `gen_single.py` | The de-facto CLI: instantiates `ImageGenerator` + `VerseDB`, picks one random verse, writes `output/single_sample.png`. | P0-13: replaced by `python -m scripts.make_post`. |
| `paths.py` | Pure module that exposes `BASE_DIR`, `UPLOADS`, `OUTPUT`, `DATABASE`, `NASHEEDS`, `TEMPLATES`, `FONTS` from the project root. Includes stray `print()` debug lines. | X-06: becomes the single source of absolute paths for every other script. |

### B. Production code to retire

| File | Role | TODO |
|---|---|---|
| `create_post.py` | Older standalone poster. Hard-codes `fonts/_extracted_fonts/AmiriQuran.ttf`, re-implements its own pandas + used-verse scan and its own dynamic sizer. Disagrees with `image_gen.py` on fonts and layout. | **P0-01: move to `scripts/_legacy/create_post.py`.** |

### C. Debug / diagnostic / superseded (delete or archive)

| File | Was used for | TODO |
|---|---|---|
| `select_verse.py` | First-pass random-pick using `pandas.DataFrame.sample` with no used-tracking. Superseded by `VerseDB`. | P0-04 delete. |
| `read_verse.py` | Just `pd.read_csv` + `df.head()`. Smoke test only. | P0-04 delete. |
| `test.py` | `print("Islamic AI Agent Started")`. | P0-04 delete. |
| `test_font.py` | Smoke-loads `arial.ttf`. | P0-04 delete. |
| `test_verse_db.py` | End-to-end: select every verse, assert no duplicates, then assert reset behaviour. | P0-05: **keep** as `tests/test_verse_db.py`. |
| `debug_verse_load.py` | Prints the first 5 loaded verses and validation result. | P0-04 delete. |
| `test_image_gen.py` | Generates 20 images in a row (warm path). | P0-05: **keep** as `tests/test_image_gen.py`. |
| `check_fonts.py` | Loads each font, prints size and 8-byte header. | P0-04 delete. |
| `debug_image_gen.py` | Prints which assets and fonts `ImageGenerator` resolved, then generates `debug_post.png`. | P0-04 delete. |
| `test_arabic_render.py` | Renders a single reshaped+bidi'd Arabic string with `Amiri-Italic.ttf`. | P0-04 delete. |
| `inspect_layout.py` | Reproduces the dynamic-sizer math outside `image_gen` and dumps every intermediate. | P0-04 delete. |
| `inspect_generator_state.py` | Dumps asset paths, font paths, layout line counts, and `y` positions. | P0-04 delete. |
| `gen_single.py` | (already in section A) | — |
| `inspect_arabic_render.py` | Verifies `arabic_reshaper` + `bidi` on a hard-coded Arabic phrase. | P0-04 delete. |
| `test_arabic_fonts.py` | Renders an Arabic phrase in a list of Windows fonts. | P0-04 delete. |
| `check_font_use.py` | Prints which Arabic font `ImageGenerator` selected. | P0-04 delete. |
| `check_font_render.py` | Renders a sample Arabic string using the generator's chosen font. | P0-04 delete. |
| `inspect_font_files.py` | For every font file: print header bytes, try `ImageFont.truetype`, sample 5 glyph bboxes. | P0-04 delete. |
| `test_font_batch.py` | Renders the same Arabic phrase in 7 candidate fonts. | P0-04 delete. |
| `test_arabic.py` | Walks the whole `fonts/` tree and renders an Arabic phrase in every TTF/OTF. | P0-04 delete. |

### D. Planned (not yet on disk)

| File | Role | TODO |
|---|---|---|
| `scripts/make_post.py` | Module entry point wrapping `ImageGenerator` so `python -m scripts.make_post` works from any cwd. | P0-13. |
| `scripts/make_reel.py` | Module entry point for `video_gen.ReelGenerator`. | P2-10. |
| `scripts/make_caption.py` | Module entry point for `caption_gen.CaptionGenerator`. | P3-09. |
| `scripts/publish.py` | Module entry point for `publishers/*`. | P4-10. |
| `scripts/report.py` | Last-7-days report (posts, themes, engagement, failures). | P5-08. |
| `scripts/_legacy/` | Folder for retired scripts after P0. | P0-04. |
| `tests/` | Real test directory after P0-05. | P0-05. |
| `agent.py` | The orchestrator (`--once` / `--schedule` / `--dry-run`). | P5-01. |

### Library code (planned)

| File | Role | TODO |
|---|---|---|
| `scripts/video_gen.py` | Reel assembly (9:16, ken-burns, timed subtitles, audio, multi-aspect export). | P2-01. |
| `scripts/caption_gen.py` | LLM captioning + SEO + alt-text with provider abstraction and a rule-based fallback. | P3-01. |
| `scripts/publishers/base.py` | `Publisher` interface: `login`, `upload_reel`, `get_engagement`. | P4-03. |
| `scripts/publishers/instagram.py` | Instagram Reels via official Graph API v18+. | P4-04. |
| `scripts/publishers/tiktok.py` | TikTok stub. | P4-06. |
| `scripts/publishers/youtube_shorts.py` | YouTube Shorts stub (resumable upload). | P4-07. |
| `database/dao.py` | Verse data-access object (moved up from `scripts/verse_db.py`). | P1-04. |
| `database/history.py` | SQLite post-history (init/log/mark_published/update_engagement/list_recent). | P1-08. |
| `database/schema.sql` | DDL for the history DB. | P1-07. |
| `database/themes.json` | Per-theme caption prompts, hashtags, accent colors, nasheed pools. | P1-03. |
| `database/licensing.csv` | Track which nasheed/translation/background/logo was used and under what license. | P6-02. |
| `docs/instagram_setup.md` | Human-run setup steps for the Facebook app + Graph API token. | P4-02. |
| `install_windows_task.bat` | Optional Windows Task Scheduler installer. | P5-10. |
| `.env.example` | Documented keys (no secrets). | P0-11. |
| `.gitignore` | `.env`, `output/`, `uploads/`, `logs/`, `__pycache__/`, `venv/`, `*.tmp`, `STOP.flag`. | P0-12. |
| `README.md` | Quickstart, env vars, schedule install, how to add a verse, how to add a theme. | P6-10. |

---

## How a request flows today (before Phase 0)

```
gen_single.py
    └──> verse_db.VerseDB          (loads quran_posts.csv + used_verses.txt)
            └──> random unused verse
    └──> image_gen.ImageGenerator   (templates/, fonts/)
            └──> ImageDraw composes logo + arabic + translit + trans + ref
    └──> output/post_<ts>.png
```

## How a request should flow at the end of the roadmap (after Phase 5)

```
agent.py  --schedule 08:00 / 13:00 / 20:00
   └──> database.dao.VerseDB.select(theme? | verse_id?)
   └──> scripts.image_gen.make_post(verse)            # 1080x1080 PNG
   └──> scripts.video_gen.make_reel(image, nasheed)   # 1080x1920 MP4
   └──> scripts.caption_gen.make_caption(verse, plat) # {caption, hashtags, desc, alt}
   └──> database.history.log_post(...)
   └──> scripts.publishers.instagram.upload_reel(...) # requires scholar_review=true
   └──> database.history.mark_published(post_id, ...)
   └──> (next day) publishers.<...>.get_engagement(post_id)
            └──> database.history.update_engagement(...)
```

`STOP.flag` and the variety guard short-circuit the pipeline at any step. `--dry-run` writes everything except the publish step. Every run lands a JSON manifest in `logs/runs/<date>.json`.

---

## Quick "what do I touch for X?"

| Goal | Touch this |
|---|---|
| Add a verse | `database/quran_posts.csv` (and update `themes.json` if you add a new theme). |
| Change the look of the post | `scripts/image_gen.py` and `templates/`. |
| Add a new font | Drop the TTF in `fonts/` and update `image_gen._get_arabic_font_path`. |
| Change the reel length / aspect | `scripts/video_gen.py` (Phase 2). |
| Change caption tone | System prompt in `scripts/caption_gen.py` (Phase 3). |
| Add a new platform | New `scripts/publishers/<platform>.py` implementing the `Publisher` interface (Phase 4). |
| Stop the agent | Create an empty `STOP.flag` at the repo root. |
| See what ran | `logs/agent.log` and `logs/runs/<date>.json` (after Phase 5). |
