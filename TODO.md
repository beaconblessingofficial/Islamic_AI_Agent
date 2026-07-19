# Islamic_AI_Agent — TODO

Source-of-truth checklist for turning the project into an autonomous daily Islamic reels + captions + SEO + posting agent. Items are ordered by phase; **do not skip ahead**.

Each item is small enough to be completed in one sitting (15-90 minutes). Group by phase; the phase ordering is load-bearing.

**Conventions**
- [ ] = pending
- [x] = done
- A task with `BLOCKED` in front of it cannot start until the named dependency is done.
- `verify:` at the end of an item tells you how to confirm it works.
- File paths are relative to repo root (`D:\Islamic_AI_Agent\`).

---

## Phase 0 — Housekeeping

**Goal:** the image pipeline renders correctly, the scripts folder is small, and the package can be imported cleanly from any cwd. This blocks every later phase.

### 0.1 — Fix the rendering bugs in `image_gen.py`

These two bugs produce the "boxes for Arabic" and "transliteration overlaps the verse" symptoms.

- [ ] **0.1.1** In `scripts/image_gen.py:__init__`, replace the `_resolve_font_path` call for the Arabic slot with a direct, unconditional path to `BASE / "fonts" / "_extracted_fonts" / "AmiriQuran.ttf"`.
  - verify: `gen.ar_font_path` is the AmiriQuran path; no zip extraction runs.
- [ ] **0.1.2** Add a one-time `assert` (or `raise FileNotFoundError`) in `ImageGenerator.__init__` if the AmiriQuran TTF is missing. The message must name the file and the expected location.
  - verify: rename the file temporarily; running `gen_single.py` fails with a clear error.
- [ ] **0.1.3** Keep the Windows-font fallback chain (`_font_fallback_paths`) for the **English** font only. Do not let it race in for Arabic.
  - verify: `gen.en_font_path` still falls back if PlayfairDisplay is missing; `gen.ar_font_path` does not.
- [ ] **0.1.4** In `image_gen._wrap_text`, **reshape the full Arabic string first, then bidi it, then wrap on whitespace.** Remove the `is_rtl=True` path that reshapes per-line after measuring.
  - verify: for verse id 1 (Al-Kahf 18:10), the measured line width equals the drawn line width within 2 px.
- [ ] **0.1.5** In the draw loop, change the inter-block gap from `12` to `20` at `image_gen.py:248, 257, 271` to match the measurement gap (`gaps = 20`).
  - verify: visual inspection of `single_sample.png` shows clean separation between Arabic, transliteration, and translation blocks.
- [ ] **0.1.6** Widen the height safety margin: `if total_h <= self.HEIGHT - 200` instead of `- 160`.
  - verify: for the longest verse in the corpus, the dynamic sizer stops on attempt 0 or 1, not 12.
- [ ] **0.1.7** Block: clear `database/used_verses.txt`, run `python scripts\gen_single.py`, and confirm `output/single_sample.png` shows no boxes, no overlap, and proper Arabic shaping.
  - verify: open the PNG. Arabic is right-to-left with full tashkeel. Transliteration sits below. Translation below that. Reference at the bottom.

### 0.2 — Clean the scripts folder

- [ ] **0.2.1** Add `scripts/__init__.py` (empty file is fine).
  - verify: `python -c "from scripts.verse_db import VerseDB"` works from any cwd.
- [ ] **0.2.2** Create `scripts/_legacy/` directory.
- [ ] **0.2.3** Move `scripts/create_post.py` → `scripts/_legacy/create_post.py`.
  - verify: `scripts/create_post.py` no longer exists at the top level; legacy still works if invoked directly.
- [ ] **0.2.4** Move the 16 diagnostic scripts to `scripts/_legacy/`: `test.py`, `test_font.py`, `read_verse.py`, `select_verse.py`, `check_fonts.py`, `inspect_font_files.py`, `test_font_batch.py`, `test_arabic_fonts.py`, `test_arabic.py`, `test_arabic_render.py`, `inspect_arabic_render.py`, `inspect_layout.py`, `inspect_generator_state.py`, `debug_verse_load.py`, `debug_image_gen.py`, `check_font_use.py`, `check_font_render.py`.
  - verify: `Get-ChildItem scripts\*.py` shows only 5 files: `__init__.py`, `image_gen.py`, `verse_db.py`, `gen_single.py`, `paths.py`.
- [ ] **0.2.5** Move `scripts/test_verse_db.py` → `tests/test_verse_db.py` and `scripts/test_image_gen.py` → `tests/test_image_gen.py`. Add `tests/__init__.py`.
  - verify: `python -m pytest tests/` runs both files.
- [ ] **0.2.6** Remove all `sys.path.insert(0, str(BASE / "scripts"))` lines from the moved test files; replace with `from scripts.verse_db import VerseDB` etc.
  - verify: tests still pass after the change.
- [ ] **0.2.7** De-duplicate `database/`: delete `quran_posts-2.csv`, `themes-2.csv`, `used_verses-2.txt`.
  - verify: `Get-ChildItem database\*` shows exactly 3 files.
- [ ] **0.2.8** De-duplicate `fonts/`: delete `Amiri-Regular-2.ttf`, `PlayfairDisplay-Regular-2.ttf`, and the four `-2` files in `fonts/_extracted_fonts/`. **Do not** delete the non-`-2` extracted fonts — those are the production fonts.
  - verify: each font has exactly one copy.
- [ ] **0.2.9** Move diagnostic PNGs from `output/` to `output/_archive/`: every `test_*.png`, `font_render_test*.png`, `debug_post.png`, `inspect_arabic.png`, `single_sample.png`. Also move the entire `output/arabic_font_tests/` subdirectory.
  - verify: `output/` contains only production `post_*.png` runs (currently the ~200 timestamped files; those stay).
- [x] **0.2.10** Rewrite `requirements.txt` with the real dependency set: `Pillow>=10.0.0`, `arabic-reshaper>=3.0.0`, `python-bidi>=0.4.2`, `pandas>=2.0.0`, `numpy>=1.24.0`, `python-dotenv>=1.0.0`, `pydantic>=2.0.0`, `python-dateutil>=2.8.0`. Add commented-out lines for the later phases: `moviepy>=2.0.0`, `imageio-ffmpeg>=0.5.0`, `opencv-python>=4.8.0`, `openai>=1.30.0`, `anthropic>=0.30.0`, `requests>=2.31.0`, `APScheduler>=3.10.0`, `google-api-python-client>=2.100.0`.
  - verify: `pip install -r requirements.txt` succeeds in a fresh venv.
- [ ] **0.2.11** Create `.env.example` with all keys documented (no secrets): `OPENAI_API_KEY=`, `ANTHROPIC_API_KEY=`, `IG_ACCESS_TOKEN=`, `IG_USER_ID=`, `FB_PAGE_ID=`, `FB_PAGE_ACCESS_TOKEN=`, `YT_OAUTH_CLIENT_SECRETS=`, `LOG_LEVEL=INFO`, `TIMEZONE=UTC`, `LLM_DAILY_BUDGET_USD=5.00`.
- [ ] **0.2.12** Create `.gitignore`: `.env`, `output/`, `uploads/`, `logs/`, `__pycache__/`, `venv/`, `*.tmp`, `STOP.flag`, `youtube-oauth2.json`, `backups/`.
- [x] **0.2.13** Create `scripts/make_post.py` as the proper module entry point: `python -m scripts.make_post [--verse-id N] [--theme T] [--count N] [--dry-run]`. It wraps `ImageGenerator` + `VerseDB`.
  - verify: `python -m scripts.make_post` produces one image in `output/`.
- [x] **0.2.14** Add `from dotenv import load_dotenv; load_dotenv()` at the top of every entry-point script (`make_post.py` and any future `make_reel.py`, `make_caption.py`, `publish.py`, `agent.py`).
- [x] **0.2.15** Delete `scripts/gen_single.py` after `make_post.py` is verified. Update `PROJECT_MAP.md` to point to `make_post` as the canonical entry.
  - verify: `python -m scripts.make_post` still works; `gen_single.py` no longer exists.

---

## Phase 1 — Daily image generation (Goal #1)

**Goal:** `python -m scripts.make_post` produces a clean image on demand, with theme-driven accents and no-repeat selection. **Blocks:** Phase 2 (reel needs the static image), Phase 3 (caption needs the verse data).

### 1.1 — Expand the verse corpus

- [ ] **1.1.1** Audit the existing 25 verses in `database/quran_posts.csv` and confirm every row has all 8 required columns: `id, surah, ayah, theme, arabic, transliteration, translation, caption_topic`. Fix any that don't.
- [ ] **1.1.2** Curate and add at least 175 more verses to bring the corpus to ≥ 200. Use these criteria:
  - Full tashkeel on the Arabic.
  - Translation from a permissibly-licensed source (Sahih International, Pickthall, Yusuf Ali). Add a `translation_source` column to every row.
  - `caption_topic` is a short, evocative phrase (3-8 words), not the full translation.
- [ ] **1.1.3** Add a `translation_source` column to `quran_posts.csv`. Allowed values: `sahih`, `pickthall`, `yusuf_ali`, `saheeh`, `clear_quran`, `other`. Populate for all 200+ rows.
  - verify: every row has a non-empty `translation_source`.
- [ ] **1.1.4** Add a `has_full_tashkeel` boolean column. Set to `true` for every row. Validation rejects `false` rows.
  - verify: `validate_verse()` rejects a row with `has_full_tashkeel=false`.
- [ ] **1.1.5** BLOCKED on 1.1.3-1.1.4. Update `verse_db.REQUIRED_COLUMNS` to include `translation_source` and `has_full_tashkeel`.

### 1.2 — Convert themes to JSON

- [x] **1.2.1** Create `database/themes.json` with the 5 themes from `themes.csv` (`Guidance, Forgiveness, Patience, Knowledge, Family`) plus 15 more from the corpus (`Steadfastness, Repentance, Trust, Balance, Prayer, Acceptance, Submission, Power, Reflection, Mercy, Ease, Facilitation, Communication, Understanding, Need, Faith`).
- [x] **1.2.2** For each theme, define: `caption_prompt` (system-prompt fragment, 2-3 sentences), `hashtags[]` (3-5 hashtags), `accent_color` (hex string for poster accent), `nasheed_pool[]` (filenames from `nasheeds/`).
  - verify: `json.load(open("database/themes.json"))` returns a dict with all 20 themes; each has all 4 fields.
- [x] **1.2.3** Delete `database/themes.csv` and `database/themes-2.csv`.
  - verify: `Get-ChildItem database\*` shows 3 files (CSV, JSON, txt).

### 1.3 — Promote the data layer

- [ ] **1.3.1** Create `database/` as a package: add `database/__init__.py`.
- [ ] **1.3.2** Move `scripts/verse_db.py` → `database/dao.py`. Strip the `if __name__ == "__main__":` block.
  - verify: `from database.dao import VerseDB` works from any cwd.
- [ ] **1.3.3** Update all imports: `scripts/make_post.py` and `tests/test_verse_db.py` now import from `database.dao`.
  - verify: `python -m pytest tests/` passes.
- [ ] **1.3.4** Add `VerseDB.select_by_theme(theme: str) -> list[dict]` method. Returns all verses with that theme from the corpus (regardless of used-state).
  - verify: `db.select_by_theme("Forgiveness")` returns a non-empty list.
- [ ] **1.3.5** Add `VerseDB.select_by_surah(surah: str) -> list[dict]` and `VerseDB.select_by_id(vid: int) -> dict | None`.
- [ ] **1.3.6** Add `VerseDB.list_unused(theme: str | None = None) -> list[int]`. Filters the unused set by theme if given.
- [ ] **1.3.7** Add `VerseDB.list_recently_used(days: int) -> list[int]`. Reads the used-verses file with mtime checks (or, after 1.4.1, queries the SQLite history).
- [ ] **1.3.8** Add `VerseDB.soft_reset(older_than_days: int = 30)`. Clears used-verses entries older than the cutoff; keeps recent ones.
  - verify: after `soft_reset(30)`, used-verses only contains ids from the last 30 days.
- [ ] **1.3.9** Add `tests/test_dao.py` covering: load, `select_random`, exhaustion → auto-reset, `mark_used` idempotency, `select_by_theme`, `soft_reset`. All must pass on a fresh DB.
- [ ] **1.3.10** Run `python -m pytest tests/test_dao.py` and confirm green.

### 1.4 — Make used-verse writes concurrency-safe

- [ ] **1.4.1** **Option A (simple):** wrap the `_persist_used` write in `msvcrt.locking` (Windows) and `fcntl.flock` (POSIX) for the used-verses file. The lock is held for the duration of the read-modify-write.
  - verify: run two `python -m scripts.make_post` processes in parallel; no double-use of verses.
- [ ] **1.4.2** **Option B (preferred, also enables 1.4.3):** move used-verse state to SQLite. Defer to Phase 2's history DB (task 2.2.1).
  - note: this is the cleaner long-term answer. Pick one or the other for 1.4.1; if 1.4.2, mark 1.4.1 deferred.

### 1.5 — Make the image generator theme-aware

- [x] **1.5.1** In `image_gen.py`, add an optional `accent_color: str | None` parameter to `generate_post`. Default `None` (no accent).
- [x] **1.5.2** When `accent_color` is set, draw a 2 px horizontal line under the reference text in that color. The line is centered, 30% of canvas width.
  - verify: `gen.generate_post(verse, accent_color="#3B7A57")` shows a green line under the reference.
- [x] **1.5.3** In `scripts/make_post.py`, add `--theme T` flag. When set, pick a verse from that theme and pass `accent_color` from `themes.json`.
  - verify: `python -m scripts.make_post --theme Forgiveness` produces an image with the Forgiveness accent.
- [x] **1.5.4** Add `--count N` flag to `make_post.py`. Runs the pipeline N times with N distinct verses.
  - verify: `python -m scripts.make_post --count 5` produces 5 images; no duplicate verses.
- [x] **1.5.5** Add `--output-name NAME` flag for deterministic filenames. Default is `post_<YYYYMMDD_HHMMSS>.png`.

### 1.6 — Verify Phase 1

- [ ] **1.6.1**. Run `python -m scripts.make_post --count 30 --theme Guidance` and confirm:
  - 30 images are produced in <60 s.
  - All 30 have the Guidance accent color.
  - All 30 are unique verses.
  - No overlap in `database/used_verses.txt` (or SQLite history).
  - No rendering regressions (Arabic reads correctly, no overlap).

---

## Phase 2 — Reel generation with subtle animation (Goals #2 + #3)

**Goal:** `python -m scripts.make_reel --verse-id N --duration 30` produces a 1080×1920 MP4 ≤ 30 MB with timed Arabic/transliteration/translation cards and a background nasheed. **Blocks:** Phase 4 (publishers need the MP4), Phase 5 (orchestrator chains this).

### 2.1 — Tooling decision

- [x] **2.1.1** Confirm `moviepy`, `imageio-ffmpeg`, and `opencv-python` are installed in the venv (`pip show moviepy`). If not, install per `requirements.txt`.

### 2.2 — Add the SQLite history database (also enables 1.4.2)

- [x] **2.2.1** Create `database/schema.sql` with tables:
  - `posts` (post_id, created_at, verse_id, theme, image_path, reel_path, caption_id, status, published_at, engagement_json).
  - `post_platforms` (id, post_id, platform, platform_post_id, platform_url, published_at, last_polled_at, engagement_json).
  - `nasheed_history` (id, nasheed_file, used_at, post_id).
  - `runs` (id, started_at, finished_at, dry_run, cost_usd, errors_json, manifest_path).
  - verify: `sqlite3 database/post_history.sqlite < database/schema.sql` succeeds.
- [x] **2.2.2** Create `database/history.py` with `init_db`, `log_post`, `mark_published`, `update_engagement`, `list_recent(n)`, `record_nasheed_use`, `get_nasheed_recently_used(days)`. All methods return typed dicts.
- [x] **2.2.3** Wire `init_db()` to run at the start of every entry-point script.
- [x] **2.2.4** BLOCKED on 2.2.1-2.2.3. Add `tests/test_history.py` covering: insert, update, query by date range, engagement round-trip. All must pass on a fresh DB.

### 2.3 — Build the reel generator skeleton

- [x] **2.3.1** Create `scripts/video_gen.py` with an empty `ReelGenerator` class. Constructor takes `assets_dir`, `output_dir`, `themes_path`.
- [x] **2.3.2** Add `ReelGenerator.make_reel(verse, image_path, nasheed_path, duration=30, aspect="9:16", dry_run=False) -> Path` method signature. Implementation raises `NotImplementedError` for now.
- [x] **2.3.3** Add a `ReelGenerator._pick_nasheed(theme: str) -> Path` method. Reads `themes.json → nasheed_pool[theme]`, picks one at random without history integration for now.

### 2.4 — Canvas and ken-burns

- [x] **2.4.1** Implement `_build_canvas(aspect: str) -> tuple[int, int]`. Returns `(width, height)`. 9:16 → (1080, 1920). 1:1 → (1080, 1080). 16:9 → (1920, 1080).
- [x] **2.4.2** Implement `_apply_ken_burns(clip, duration: float) -> VideoClip`. Slow zoom 1.0× → 1.02× and 0 → 4 px diagonal pan over `duration`. Use `moviepy`'s `fl` time-varying function on a `resize` transform.
  - verify: the resulting clip is `duration` seconds, has a slight zoom visible on every frame, and is GPU-friendly (no per-frame re-encode during the transform).
- [x] **2.4.3** Implement `_add_vertical_gradient_bg(canvas_size, accent_color=None) -> VideoClip`. A cream-colored background (matching the static image) with a soft vertical gradient transparent → cream at top and bottom, to fill the 420 px gap above and below the 1080×1080 plate.

### 2.5 — Subtitle cards

- [x] **2.5.1** Implement `_render_arabic_card(verse, font, duration) -> ImageClip`. Pre-render a transparent PNG of the reshaped+bidi'd Arabic text. Wrap to canvas width. Return an `ImageClip` of `duration` seconds.
  - verify: the PNG has no boxes; text is right-aligned and properly shaped.
- [x] **2.5.2** Implement `_render_translit_card(verse, font, duration) -> ImageClip`. Same pattern for the transliteration.
- [x] **2.5.3** Implement `_render_translation_card(verse, font, duration) -> ImageClip`. Same for the translation.
- [x] **2.5.4** Implement `_render_reference_card(verse, font, duration) -> ImageClip`. The "Al-Baqarah 2:286" card.
- [x] **2.5.5** Implement `_time_subtitles(verse) -> list[(card, start_sec, end_sec)]`. Beat math:
  - Arabic: appears at 0.0 s, holds for 3.0 s, fades 0.3 s.
  - Translit: starts at 3.3 s, holds 2.5 s, fades 0.3 s.
  - Translation: starts at 6.1 s, holds 3.0 s, fades 0.3 s.
  - Reference: starts at `duration - 1.5`, holds 1.5 s, fades 0.3 s.
  - verify: timing sums ≤ `duration`; no overlap between cards (except reference which may overlap the tail of translation by 0.5 s).
- [x] **2.5.6** Implement `_compose_cards(cards, canvas_size, background) -> VideoClip`. Layers all four cards on top of the ken-burns background. Logo and separator are persistent across the full duration.

### 2.6 — Audio

- [x] **2.6.1** Implement `_attach_audio(clip, nasheed_path, duration) -> VideoClip`. Load the MP3, loop or trim to `duration`, apply 0.5 s fade in + 0.5 s fade out.
  - verify: the audio is exactly `duration` seconds; no clipping at the seams when looping.
- [x] **2.6.2** Implement `_normalize_audio(clip, target_lufs=-16) -> VideoClip`. Use `moviepy.audio.fx.all.audio_normalize` followed by a `volumex` adjustment. Cap at -3 dBFS peak to avoid clipping.
  - verify: a peak-volume MP3 in the input does not produce clipping in the output.

### 2.7 — Export

- [x] **2.7.1** Implement `_export(clip, output_path) -> Path`. H.264, yuv420p, `preset=medium`, `bitrate="5000k"`, `audio_bitrate="192k"`, `ffmpeg_params=["-movflags", "+faststart"]`. File size target: ≤ 30 MB for 30 s.
  - verify: `ffprobe output_path` shows H.264, yuv420p, faststart; file size is ≤ 30 MB for 30 s.
- [x] **2.7.2** Wire `make_reel` to call the full pipeline: build canvas → apply ken-burns → compose cards → attach audio → export.
  - verify: a 30 s reel for verse id 1 is produced in <60 s and plays cleanly in VLC.

### 2.8 — Entry point and CLI

- [x] **2.8.1** Create `scripts/make_reel.py`: `python -m scripts.make_reel --verse-id N --duration 30 [--aspect 9:16] [--theme T] [--dry-run]`.
- [x] **2.8.2** `--dry-run` writes the reel to `output/pending/` instead of `output/reels/`.
- [x] **2.8.3** BLOCKED on 2.2. Log the nasheed choice to `nasheed_history` table on every reel (real or dry-run).

### 2.9 — Tests

- [ ] **2.9.1** Create `tests/test_video_gen.py` with smoke tests:
  - [ ] `test_make_reel_produces_mp4`: produces a file, ffprobe confirms H.264. (Mocked unit test done, need true integration test)
  - [x] `test_aspect_9_16`: dimensions are 1080×1920.
  - [x] `test_aspect_1_1`: dimensions are 1080×1080.
  - [ ] `test_file_size_under_30mb_for_30s`: file size ≤ 30 MB. (Mocked unit test done, need true integration test)
  - [x] `test_nasheed_picked_from_theme`: nasheed is in the theme's pool.
  - [x] `test_dry_run_writes_to_pending`: output path is under `output/pending/`.
- [ ] **2.9.2** Run `python -m pytest tests/test_video_gen.py` and confirm green (including integration tests).

### 2.10 — Verify Phase 2

- [ ] **2.10.1** Generate a 15 s reel: `python -m scripts.make_reel --verse-id 7 --duration 15 --dry-run`.
- [ ] **2.10.2** Generate a 30 s reel for the same verse: `python -m scripts.make_reel --verse-id 7 --duration 30 --dry-run`.
- [ ] **2.10.3** Play both reels in VLC end-to-end. Confirm:
  - No clipping in the audio.
  - Subtitle cards appear in order and at the right times.
  - Arabic is right-to-left and properly shaped (no boxes).
  - The ken-burns is visible but subtle.

---

## Phase 3 — Captions, hashtags, SEO (Goal #4)

**Goal:** `python -m scripts.make_caption --verse-id N --platform instagram` returns a valid Pydantic `CaptionOutput` with caption + hashtags + description + alt_text. Works online (LLM) and offline (rule-based). **Blocks:** Phase 4 (publishers need the caption).

### 3.1 — Pydantic models

- [ ] **3.1.1** Create `scripts/caption_gen.py`. Define `CaptionOutput` Pydantic model with fields: `caption: str`, `hashtags: list[str]`, `description: str`, `alt_text: str`, `youtube_title: str | None = None`, `youtube_description: str | None = None`, `youtube_tags: list[str] | None = None`.
- [ ] **3.1.2** Add field validators:
  - `caption` ≤ 2200 chars (Instagram/Facebook) or ≤ 5000 (YouTube Shorts).
  - `hashtags` ≤ 30 items, each starts with `#`, no duplicates.
  - `description` ≤ 2200 chars (Instagram/Facebook) or ≤ 5000 (YouTube Shorts).
  - `alt_text` ≤ 140 chars.
  - `youtube_title` ≤ 100 chars (if set).
  - `youtube_description` ≤ 5000 chars (if set).
  - `youtube_tags` ≤ 500 chars total (if set).
- [ ] **3.1.3** Define `CaptionInputs` Pydantic model: `verse: dict`, `theme: str`, `platform: Literal["instagram","facebook","youtube"]`, `max_length: int = 2200`, `language: str = "en"`.
- [ ] **3.1.4** Add `__post_init__` checks:
  - Description must contain the reference (e.g. "Al-Baqarah 2:286").
  - Description must contain a primary keyword ("quran verse" + theme) in first 125 chars.
  - Caption must end with a CTA (one of the allowed phrases).
  - Captions must not start with "Certainly," "Indeed," or "Of course,"
  - Captions must not contain "The Prophet said" without a source collection name.

### 3.2 — Provider abstraction

- [ ] **3.2.1** Define `BaseProvider` abstract class with one method: `generate(inputs: CaptionInputs) -> CaptionOutput`.
- [ ] **3.2.2** Implement `OpenAIProvider` using the `openai` SDK. Default model: `gpt-4o-mini`. Uses the system prompt from 3.3.1.
- [ ] **3.2.3** Implement `AnthropicProvider` using the `anthropic` SDK. Default model: `claude-haiku-4-5`. Uses the same system prompt.
- [ ] **3.2.4** Implement `RuleBasedProvider` — deterministic offline fallback. No API call. Implementation in 3.5.
- [ ] **3.2.5** Add `CaptionGenerator` class. Constructor takes `provider: BaseProvider`, `themes_path: Path`, `taglines_path: Path`. Exposes `generate(inputs: CaptionInputs) -> CaptionOutput` which delegates to the provider.
- [ ] **3.2.6** Provider selection via `.env`: `CAPTION_PROVIDER=openai|anthropic|rulebased`. Default: `rulebased` (safe default; user opts in to LLM cost).

### 3.3 — System prompt (LLM providers)

- [ ] **3.3.1** Define the system prompt as a constant in `caption_gen.py`. Non-negotiable rules:
  - "Never fabricate a hadith. If you reference a hadith, name the collection and narrator, and only when the user has provided the text."
  - "Never name a narrator you cannot source."
  - "Never claim a nasheed is by a specific artist unless told."
  - "Tone: gentle, hopeful, dua-style closing. No sectarian positioning."
  - "Length: keep captions under 150 words by default."
  - "Do not begin with 'Certainly,' 'Indeed,' or 'Of course.'"
  - "Do not use emoji more than 3 times per caption."
  - "Always end with a call to reflect, share, or make dua."
- [ ] **3.3.2** Define the user prompt template that fills in: theme, translation, surah:ayah, target platform, max length.

### 3.4 — Hashtag strategy

- [ ] **3.4.1** Read `themes.json → themes[theme].hashtags[]`. Take all of them.
- [ ] **3.4.2** Append 5 always-on hashtags: `#Islam #Quran #Muslim #Faith #DailyReminder`.
- [ ] **3.4.3** Append 3 rotating hashtags from a curated `database/trending_pool.json` (hand-picked, never scraped). Rotate deterministically (e.g. by day-of-year mod pool size).
- [ ] **3.4.4** Deduplicate and cap at 30 total.

### 3.5 — Rule-based fallback

- [ ] **3.5.1** Create `database/taglines.json` with 20+ rotating taglines (e.g. "A verse for your heart today.", "Carry this with you.", "Read it once more before you go.").
- [ ] **3.5.2** Implement `RuleBasedProvider.generate(inputs) -> CaptionOutput`:
  - `caption` = theme prompt + translation + reference + rotating tagline.
  - `hashtags` from 3.4.1-3.4.4.
  - `description` = primary-keyword phrase + translation + reflection (a templated sentence per theme) + reference + CTA.
  - `alt_text` = "Arabic calligraphy on a soft cream background, [reference], a verse about [theme]."
  - `youtube_title` = first 80 chars of `caption`.
  - `youtube_description` = `description` + 3 extra reflection sentences + hashtags (≤ 15, not 30).
  - `youtube_tags` = `hashtags` joined by comma, ≤ 500 chars.

### 3.6 — Entry point and tests

- [ ] **3.6.1** Create `scripts/make_caption.py`: `python -m scripts.make_caption --verse-id N --platform instagram [--save] [--provider openai|anthropic|rulebased]`.
- [ ] **3.6.2** Default output: JSON to stdout. `--save` writes to `output/captions/<date>_<id>.json`.
- [ ] **3.6.3** Create `tests/test_caption_gen.py`:
  - `test_output_validates`: Pydantic validation passes.
  - `test_length_limits`: `len(caption) <= 2200`, `len(hashtags) <= 30`, etc.
  - `test_description_has_reference`: `"Al-Baqarah 2:286"` in description.
  - `test_description_keyword_in_first_125`: primary keyword in first 125 chars.
  - `test_no_fabricated_hadith`: caption does not contain `"The Prophet said"` without `"al-Bukhari"` or `"Muslim"` after.
  - `test_cta_present`: caption ends with one of the allowed CTAs.
  - `test_openai_provider_mocked`: mock the openai SDK; assert the call structure is right.
  - `test_rulebased_provider_real`: actually runs, no API call.
- [ ] **3.6.4** Run `python -m pytest tests/test_caption_gen.py` and confirm green.

### 3.7 — Verify Phase 3

- [ ] **3.7.1** Generate captions for 3 verses in offline mode: `python -m scripts.make_caption --verse-id 1 --platform instagram --provider rulebased --save` (and id 7, 12).
- [ ] **3.7.2** Generate the same 3 in online mode (if `OPENAI_API_KEY` is set): `python -m scripts.make_caption --verse-id 1 --platform instagram --provider openai --save`.
- [ ] **3.7.3** Inspect each output. Confirm:
  - All length checks pass.
  - Description has the reference and a primary keyword early.
  - No fabricated hadith strings.
  - Tone matches the system prompt.

---

## Phase 4 — Publishing to Instagram, Facebook, YouTube (Goal #6)

**Goal:** `python -m scripts.publish --platform instagram --reel <path> --caption <path> --dry-run` works; live mode (without `--dry-run`) posts to all three platforms. **Blocks:** Phase 5 (orchestrator chains this).

### 4.1 — Publisher interface

- [ ] **4.1.1** Create `scripts/publishers/__init__.py` (empty).
- [ ] **4.1.2** Create `scripts/publishers/base.py` with `Publisher` Protocol:
  - `login() -> None`
  - `upload_reel(reel_path: Path, caption: CaptionOutput, cover_path: Path | None = None) -> str` (returns platform post id)
  - `get_engagement(post_id: str) -> Engagement`
- [ ] **4.1.3** Define `Engagement` Pydantic model: `views: int, likes: int, comments: int, saves: int, shares: int, fetched_at: datetime`.
- [ ] **4.1.4** Define `PublishError` exception class.

### 4.2 — Instagram Reels

- [ ] **4.2.1** Document setup in `docs/instagram_setup.md`: create Facebook app → add Instagram product → link Instagram Business account → generate long-lived user token → exchange for long-lived page token → store in `.env`. **Do not script this.**
- [ ] **4.2.2** Create `scripts/publishers/instagram.py` with `InstagramPublisher` class.
- [ ] **4.2.3** Implement `login()`: verify the access token is valid by calling `GET /me`. If 401, raise `PublishError` with a clear message.
- [ ] **4.2.4** Implement `upload_reel(reel_path, caption, cover_path=None)`:
  1. Upload the reel to a public URL (use a temp upload service or self-hosted S3).
  2. POST `/me/media` with `media_type=REELS`, `video_url`, `caption` (caption + hashtags joined), `cover_url` (if set), `thumb_offset`, `share_to_feed=true`. Returns `container_id`.
  3. Poll `container_id` every 5 s until `status_code == FINISHED` (max 5 min).
  4. POST `/me/media_publish` with `creation_id=container_id`. Returns `post_id`.
  - verify: a `--dry-run` invocation prints the full request body without hitting the network.
- [ ] **4.2.5** Implement `get_engagement(post_id)` using `GET /<post_id>/insights` with `metric=impressions,reach,likes,comments,saved,shares`. Map to `Engagement` Pydantic model.

### 4.3 — Facebook Reels

- [ ] **4.3.1** Create `docs/facebook_setup.md` (similar to Instagram, since the same Facebook app covers both).
- [ ] **4.3.2** Create `scripts/publishers/facebook.py` with `FacebookPublisher` class.
- [ ] **4.3.3** Implement `login()`, `upload_reel()`, `get_engagement()` — same patterns as Instagram but the endpoints target the Facebook Page, not the Instagram account:
  - `POST /<page_id>/videos` for upload.
  - `GET /<post_id>/insights` for engagement.
  - Cover image is **mandatory** for Facebook Reels (fail with `PublishError` if not provided).

### 4.4 — YouTube Shorts

- [ ] **4.4.1** Document OAuth2 setup in `docs/youtube_setup.md`. Use `google-auth-oauthlib`. The first run opens a browser; the user grants permission; a `youtube-oauth2.json` is written. Add it to `.gitignore`.
- [ ] **4.4.2** Create `scripts/publishers/youtube.py` with `YouTubePublisher` class.
- [ ] **4.4.3** Implement `login()`: load `youtube-oauth2.json`, refresh if expired, raise `PublishError` if file is missing.
- [ ] **4.4.4** Implement `upload_reel(reel_path, caption)`:
  1. Use `videos.insert` with `part=snippet,status`, `uploadType=resumable`.
  2. Body: `snippet.title` (from `caption.youtube_title`), `snippet.description` (from `caption.youtube_description`), `snippet.tags[]` (from `caption.youtube_tags`), `snippet.categoryId=22` (People & Blogs), `status.privacyStatus=public` (or `unlisted` for first review), `status.selfDeclaredMadeForKids=false`.
  3. Upload the MP4 in chunks.
  4. YouTube auto-detects Shorts by aspect ratio (9:16) and duration (≤ 60 s).
  - verify: a `--dry-run` invocation prints the full request body without hitting the network.
- [ ] **4.4.5** Implement `get_engagement(post_id)` using `videos.list(part=statistics)` with `id=post_id`. Map to `Engagement`.

### 4.5 — Cross-platform dispatch

- [ ] **4.5.1** Create `scripts/publishers/all.py` with `publish_to_all(reel_path, caption, cover_path, platforms: list[str], history) -> dict[str, str]`. Iterates the configured publishers, calls `upload_reel` on each, catches per-publisher exceptions, returns `{platform: post_id}`. Logs failures to `history.log_post`.
- [ ] **4.5.2** Every successful upload writes a row to `post_platforms` (post_id, platform, platform_post_id, platform_url, published_at).
- [ ] **4.5.3** Every adapter must have a `--dry-run` mode that logs the full request and response but does not call the network.

### 4.6 — Entry point

- [ ] **4.6.1** Create `scripts/publish.py`: `python -m scripts.publish --platform instagram,facebook,youtube --reel <path> --caption <path> [--cover <path>] [--dry-run]`.
- [ ] **4.6.2** BLOCKED on 4.2-4.4. The CLI builds the `Publisher` for each requested platform, calls `publish_to_all`, and prints the result.

### 4.7 — Tests

- [ ] **4.7.1** Create `tests/test_publishers.py` with mocked HTTP responses (use `responses` or `httpx-mock`):
  - `test_instagram_login`: 200 response, `login()` succeeds.
  - `test_instagram_upload`: mocked container create + poll + publish; `upload_reel` returns a post_id.
  - `test_instagram_engagement`: mocked insights response; `get_engagement` returns a valid `Engagement`.
  - Same three tests for Facebook and YouTube.
  - `test_dry_run_does_not_call_network`: every publisher, in dry-run, makes zero network calls.
  - `test_publish_to_all_skips_failed_platforms`: one platform raises; the other succeeds; result has only the successful one.
- [ ] **4.7.2** Run `python -m pytest tests/test_publishers.py` and confirm green.
- [ ] **4.7.3** **Verify with sandbox accounts**: `python -m scripts.publish --platform instagram --reel <test_reel> --caption <test_caption> --dry-run` prints the full request without hitting the network. Repeat for Facebook and YouTube.

---

## Phase 5 — Orchestrator & scheduling (Goal #5 + #7 enforcement)

**Goal:** `python -m agent --once --dry-run` runs the full pipeline; `python -m agent --schedule --dry-run` runs unattended in the background. **Blocks:** Phase 6 (guardrails wrap this).

### 5.1 — Orchestrator skeleton

- [ ] **5.1.1** Create `agent.py` at the repo root. Empty `main()` and `__main__` block.
- [ ] **5.1.2** Define `Orchestrator` class. Constructor reads `.env`, loads `themes.json`, instantiates `VerseDB`, `ImageGenerator`, `ReelGenerator`, `CaptionGenerator`, and the publisher list.
- [ ] **5.1.3** Add `Orchestrator.run_once(theme=None, verse_id=None, platform=None, dry_run=False) -> RunResult` method. Stub for now.
- [ ] **5.1.4** Define `RunResult` Pydantic model: `verse: dict, image_path: Path, reel_path: Path, caption: CaptionOutput, posts: dict[str, str], errors: list[str], cost_usd: float, dry_run: bool`.

### 5.2 — Pipeline implementation

- [ ] **5.2.1** Step 1 of pipeline: `dao.select(theme=theme, verse_id=verse_id, exclude_recent_days=30, exclude_consecutive_theme=True)`. Implements 5.3.1-5.3.3.
- [ ] **5.2.2** Step 2: `image_gen.make_post(verse, accent_color=theme.accent_color)`. Writes `output/<name>.png`.
- [ ] **5.2.3** Step 3: `video_gen.make_reel(verse, image, nasheed=theme.nasheed_pool, duration=30, aspect="9:16", dry_run=dry_run)`. Writes `output/reels/<id>.mp4` or `output/pending/<id>.mp4` if dry-run.
- [ ] **5.2.4** Step 4: `caption_gen.generate(verse, platform).` Returns `CaptionOutput`. Save JSON to `output/captions/<id>.json`.
- [ ] **5.2.5** Step 5: `history.log_post(...)` — write the `posts` row with status=`pending_review`.
- [ ] **5.2.6** Step 6 (only if `not dry_run`): for each platform, `publishers.<platform>.upload_reel(reel, caption)`. On success, `history.mark_published(post_id, platform, platform_post_id)`. On failure, catch `PublishError`, append to `RunResult.errors`, continue to the next platform.
- [ ] **5.2.7** Step 7: write the run manifest to `logs/runs/<YYYY-MM-DD>_<HHMMSS>.json`. Include all inputs, outputs, costs, errors.

### 5.3 — Variety guard (Goal #7)

- [ ] **5.3.1** `dao.select(theme=None, exclude_recent_days=30)` — never pick a verse that was posted in the last 30 days. Implement by checking `used_verses.txt` (Phase 1 state) and the SQLite `posts` table.
- [ ] **5.3.2** `dao.select(theme=None, exclude_consecutive_theme=True)` — never pick the same theme as the previous post. Compare with the most recent row in `posts`.
- [ ] **5.3.3** `_pick_nasheed(theme, exclude_recent_days=7)` — never pick the same nasheed MP3 twice in a 7-day window. Reads `nasheed_history`.
- [ ] **5.3.4** If no verse satisfies all three guards, the run logs a warning and skips the post (does not crash the scheduler).

### 5.4 — CLI flags

- [ ] **5.4.1** `--once` — run the pipeline once and exit.
- [ ] **5.4.2** `--schedule` — start APScheduler. Default slots: 08:00, 13:00, 20:00 local time. Configurable via `SCHEDULE_TIMES=08:00,13:00,20:00` in `.env`.
- [ ] **5.4.3** `--dry-run` — runs steps 1-5 + 7, skips step 6. Reels go to `output/pending/`.
- [ ] **5.4.4** `--platform instagram,facebook,youtube` — restrict which platforms get the post. Default: all configured (read from `ENABLED_PLATFORMS` in `.env`).
- [ ] **5.4.5** `--theme Forgiveness` — force a specific theme for this run. Default: any.
- [ ] **5.4.6** `--verse-id 7` — bypass `dao.select` and use a specific verse.
- [ ] **5.4.7** `--count 3` — run the pipeline 3 times in a row. Each run gets a different verse (variety guard applies).

### 5.5 — Scheduling

- [ ] **5.5.1** Use `APScheduler` `BackgroundScheduler` with `CronTrigger`. Timezone from `TIMEZONE` in `.env` (default UTC).
- [ ] **5.5.2** Add `install_windows_task.bat` as an alternative: `schtasks /create /sc daily /tn IslamicAIAgent /tr "python -m agent --once" /st 08:00`. Document the trade-off vs APScheduler.
- [ ] **5.5.3** On startup, log the schedule: "Next run: 2026-07-14 08:00:00 (TIMEZONE)".

### 5.6 — Logging

- [ ] **5.6.1** Rotating file handler for `logs/agent.log`: 10 MB × 5 generations. `LOG_LEVEL=INFO` by default; `LOG_LEVEL=DEBUG` for verbose.
- [ ] **5.6.2** Per-run JSON manifest in `logs/runs/<YYYY-MM-DD>_<HHMMSS>.json`. Fields: `started_at`, `finished_at`, `duration_sec`, `verse_id`, `theme`, `image_path`, `reel_path`, `caption_id`, `platforms_attempted`, `platforms_published`, `engagement`, `errors`, `cost_usd`.
- [ ] **5.6.3** Every adapter call logs the request and response (with secrets masked). Implement a `mask_secrets(dict) -> dict` helper that replaces any key matching `*token*`, `*secret*`, `*password*`, `*key*` with `***`.

### 5.7 — Failure handling

- [ ] **5.7.1** Every adapter raises a typed exception: `PublishError`, `CaptionError`, `RenderError`, `AudioError`, `NetworkError`. The orchestrator catches per-step.
- [ ] **5.7.2** A full failure (no platforms succeeded) writes `output/failed/<date>_<verse_id>.json` with the inputs and errors. The scheduler logs the failure and continues to the next slot.
- [ ] **5.7.3** Transient network errors retry with exponential backoff: 3 attempts at 5 s, 15 s, 60 s. After 3 attempts, log and mark failed.

### 5.8 — Kill switch

- [ ] **5.8.1** At the start of every run, check for `STOP.flag` at the repo root. If present, log "STOP.flag present, skipping run", delete the flag, exit cleanly.
- [ ] **5.8.2** Document in `README.md`: "To pause the agent, create an empty file named `STOP.flag` at the repo root."

### 5.9 — Engagement polling

- [ ] **5.9.1** A separate APScheduler job runs **24 h after each post** (or every 6 h for the first 7 days, then once daily). Calls `get_engagement(post_id)` for every platform.
- [ ] **5.9.2** Writes the result to `post_platforms.engagement_json`. Updates `last_polled_at`.
- [ ] **5.9.3** The poll runs even if no new post was made that day.

### 5.10 — Report

- [ ] **5.10.1** Create `scripts/report.py`: `python -m scripts.report [--days 7] [--json]`.
- [ ] **5.10.2** Output: total posts, posts by theme, posts by platform, total engagement (views/likes/comments/saves/shares), top 5 verses by engagement, top 5 hashtags by reach, failure count, total cost.

### 5.11 — Tests

- [ ] **5.11.1** Create `tests/test_agent.py`:
  - `test_run_once_dry_run`: full pipeline runs, no network calls, manifest written, history row written.
  - `test_run_once_with_verse_id`: bypasses `dao.select`.
  - `test_run_once_with_theme`: filters by theme.
  - `test_variety_guard_rejects_recent_verse`: posting the same verse twice in 30 days raises a guard exception.
  - `test_variety_guard_rejects_consecutive_theme`: posting two Forgiveness posts in a row raises a guard exception.
  - `test_kill_switch`: with `STOP.flag` present, `run_once` returns immediately and deletes the flag.
  - `test_retry_on_transient_network_error`: a publisher that fails twice then succeeds is retried.
  - `test_publish_to_all_skips_failed_platforms`: one platform raises; the other succeeds.
- [ ] **5.11.2** Run `python -m pytest tests/test_agent.py` and confirm green.
- [ ] **5.11.3** Verify: `python -m agent --once --dry-run` runs the full pipeline and exits 0.

### 5.12 — Verify Phase 5

- [ ] **5.12.1** Run `python -m agent --once --dry-run` and confirm:
  - A complete bundle is produced in `output/pending/<id>.mp4`.
  - A manifest is written to `logs/runs/<date>.json`.
  - A row is added to the `posts` table with status=`pending_review`.
  - No network calls were made.
- [ ] **5.12.2** Run `python -m agent --schedule --dry-run` for 60 s in the background. Confirm one run per scheduled slot.
- [ ] **5.12.3** Run `python -m scripts.report --days 1` and confirm the manifest data is reflected.

---

## Phase 6 — Guardrails, growth, polish (Goal #7, made production-grade)

**Goal:** the agent can run unattended for 30 days without violating scholar review, licensing, cost, or variety guardrails. Each task is independent and can ship in any order.

### 6.1 — Scholar review queue (most important)

- [ ] **6.1.1** Every generated caption is `pending_review=true` in the history DB by default.
- [ ] **6.1.2** The orchestrator never publishes a `pending_review=true` post. The `--schedule` mode skips publishing; only `--once --force-publish` bypasses.
- [ ] **6.1.3** Create `scripts/review.py`: `python -m scripts.review --post-id <uuid> --approve | --reject [--note "..."]`.
- [ ] **6.1.4** `--approve` sets `pending_review=false`, `approved_at=now`, `approved_by=$USER`. `--reject` sets `status=rejected`.
- [ ] **6.1.5** BLOCKED on 6.1.3. Add `--auto-approve-after 24h` flag to `agent.py`. Only applies to low-risk themes (`Knowledge, Reflection, Balance, Ease, Facilitation`). Higher-risk themes (any theme that could be confused with hadith, sectarian, or that quotes a narrator) always require manual approval. Curate the high-risk list in `themes.json → themes[theme].requires_manual_review: bool`.
- [ ] **6.1.6** Add `scripts/list_pending.py`: lists all posts with `pending_review=true`. Used by the human reviewer as a daily checklist.

### 6.2 — Licensing log

- [ ] **6.2.1** Create `database/licensing.csv` with columns: `asset_type, asset_name, source, license, attribution, used_in_post_id, used_at`.
- [ ] **6.2.2** For every generated post, the agent logs: nasheed MP3 (file + license), translation source (verse + translator + license), background plate (`background.jpg` + license), logo (license).
- [ ] **6.2.3** Verify the asset licenses in `database/licensing.csv` are filled for every active asset:
  - `nasheeds/*.mp3`: check the source (likely royalty-free; record the source URL).
  - `templates/background.jpg`: record the source and license.
  - `templates/logo.png`: confirm you have rights to use it. If not, replace.
  - `fonts/Amiri-Regular.ttf` and `PlayfairDisplay-Regular.ttf`: confirm the SIL OFL license is preserved.
- [ ] **6.2.4** Create `scripts/audit_licensing.py`: scans the post history and verifies every asset is properly attributed. Fails with a list of missing attributions.

### 6.3 — Translation source audit

- [ ] **6.3.1** Confirm every verse in `quran_posts.csv` has a `translation_source` set (task 1.1.3).
- [ ] **6.3.2** Confirm the licenses for the translation sources:
  - Sahih International: free with attribution → `attribution: "Saheeh International, used under fair use, https://quran.com/"`.
  - Pickthall: public domain.
  - Yusuf Ali: public domain with notice.
  - Saheeh International: display required → `attribution: "Saheeh International, displayed as required"`.
  - Clear Quran (Mustafa Khattab): free with attribution.
- [ ] **6.3.3** Add the attribution string to every verse's `translation_attribution` column (one-time bulk edit).
- [ ] **6.3.4** Update the rule-based caption generator to include the translation attribution in the YouTube description.

### 6.4 — Cost guardrail

- [ ] **6.4.1** `LLM_DAILY_BUDGET_USD=5.00` in `.env.example` (already there from 0.2.11).
- [ ] **6.4.2** The agent tracks LLM cost in the manifest (`cost_usd` field). Cost = `prompt_tokens * input_price + completion_tokens * output_price` per provider.
- [ ] **6.4.3** If a run would push daily cost over the budget, the agent falls back to `RuleBasedProvider` for that run and logs an `ALERT` (high-priority log line) with the cumulative cost.
- [ ] **6.4.4** Cumulative cost is logged daily; `scripts/report.py` includes a cost section.

### 6.5 — Backup and restore

- [ ] **6.5.1** Weekly APScheduler job: dump `database/post_history.sqlite` to `backups/post_history_<date>.sqlite`.
- [ ] **6.5.2** Retention: keep 12 weeks. Older backups auto-deleted.
- [ ] **6.5.3** Create `scripts/restore_history.py`: `python -m scripts.restore_history --from <backup_file>`. Confirms before overwriting.

### 6.6 — Multi-language

- [ ] **6.6.1** Add `caption_language: Literal["en","ur","id","tr"]` to the caption generator's `CaptionInputs`.
- [ ] **6.6.2** Add `translation_ur`, `translation_id`, `translation_tr` columns to `quran_posts.csv`. Populate for the top 50 verses (curated by reach).
- [ ] **6.6.3** Add `caption_prompt_ur`, `caption_prompt_id`, `caption_prompt_tr` to each theme in `themes.json`. Translation by a native speaker; do not machine-translate the prompts.
- [ ] **6.6.4** Add `--language ur` flag to `agent.py`. Default: `en`.
- [ ] **6.6.5** The rule-based provider generates the caption in the requested language using the localized translation column + localized prompt.

### 6.7 — Thumbnail generator

- [ ] **6.7.1** After the reel is rendered, extract a 1080×1920 frame at 50% duration using `moviepy`.
- [ ] **6.7.2** Pick the frame with the highest contrast against the cream background (use `opencv-python`'s `cvtColor` + histogram).
- [ ] **6.7.3** Composite the logo + reference onto the chosen frame. Save as `output/thumbnails/<id>.jpg`.
- [ ] **6.7.4** Pass this path to the publishers as `cover_path` (mandatory for Facebook Reels; optional for Instagram and YouTube Shorts).

### 6.8 — A/B testing

- [ ] **6.8.1** Define two caption styles in `themes.json → themes[theme].caption_styles[]`: `"reflective"` and `"dua-style"`. The rule-based provider picks one based on the post id modulo 2.
- [ ] **6.8.2** Define two thumbnail styles: `"logo-top"` and `"logo-bottom"`. The thumbnail generator picks one based on the post id modulo 2.
- [ ] **6.8.3** Add `variant_caption` and `variant_thumbnail` columns to the `posts` table.
- [ ] **6.8.4** After 30 posts, `scripts/report.py` shows engagement broken down by variant.

### 6.9 — Sentry (optional)

- [ ] **6.9.1** Add `sentry-sdk[fastapi]>=1.40.0` to `requirements.txt` (commented out by default).
- [ ] **6.9.2** `SENTRY_DSN` in `.env.example`.
- [ ] **6.9.3** When `SENTRY_DSN` is set, the agent process initializes Sentry and all uncaught exceptions flow there.

### 6.10 — README

- [ ] **6.10.1** Write `README.md`:
  - **Quickstart**: clone, create venv, `pip install -r requirements.txt`, copy `.env.example` to `.env`, `python -m scripts.make_post` to verify.
  - **Env vars**: link to `.env.example`, document each one.
  - **Schedule install**: `python -m agent --schedule` (APScheduler) or `install_windows_task.bat` (Task Scheduler).
  - **How to add a verse**: append a row to `database/quran_posts.csv`. List the required columns and an example.
  - **How to add a theme**: add an entry to `database/themes.json`. List the required keys and an example.
  - **How to add a nasheed**: drop the MP3 in `nasheeds/`, add it to the theme's `nasheed_pool[]` and to `database/licensing.csv`.
  - **How to add a publisher**: implement the `Publisher` Protocol in `scripts/publishers/`, add to `agent.py`'s publisher list.
  - **How to audit licensing**: `python -m scripts.audit_licensing`.
  - **Troubleshooting**: common errors and their fixes.

---

## Cross-cutting — never forget

These are constraints every task above must respect, not new work to do at the end.

- [ ] **X-01** Never commit secrets. `.env` is git-ignored; only `.env.example` is tracked. (Done by 0.2.11-0.2.12.)
- [ ] **X-02** Never publish without scholar review enabled (6.1.1-6.1.5 must be in place before any real publish).
- [ ] **X-03** Never assume the LLM is correct on hadith attribution; the system prompt must forbid fabrication (3.3.1).
- [ ] **X-04** Every external adapter (OpenAI, Instagram, TikTok, YouTube) must have a `--dry-run` mode.
- [ ] **X-05** Every run writes a JSON manifest in `logs/runs/` with inputs, outputs, costs, errors (5.6.2).
- [ ] **X-06** Use absolute paths via `paths.py` everywhere; no hard-coded `C:\…` strings outside `paths.py`. (Done in 0.2.1; audit during 0.2.4.)
- [ ] **X-07** Public APIs only (no `instagrapi`) for production publishing. Enforced by 4.2.2.

---

## Progress tracker

A one-line summary of where we are. Update as phases complete.

```
Phase 0: [ ] not started
Phase 1: [ ] not started
Phase 2: [ ] not started
Phase 3: [ ] not started
Phase 4: [ ] not started
Phase 5: [ ] not started
Phase 6: [ ] not started
```

---

## Quick reference: what to touch for X

| Goal | Touch this |
|---|---|
| Add a verse | `database/quran_posts.csv` (and update `themes.json` if a new theme) |
| Change the look of the post | `scripts/image_gen.py` and `templates/` |
| Change the reel look | `scripts/video_gen.py` |
| Change caption tone | `scripts/caption_gen.py` system prompt (3.3.1) |
| Add a new font | Drop the TTF in `fonts/`; update `scripts/image_gen.py` to reference it |
| Change reel length / aspect | `scripts/video_gen.py` (2.4.1) and `scripts/make_reel.py` (2.8.1) |
| Add a new platform | New `scripts/publishers/<platform>.py` implementing `Publisher` (4.1.2) |
| Add a new language | `database/quran_posts.csv` translation columns + `themes.json` prompt variants (6.6) |
| Stop the agent | Create an empty `STOP.flag` at the repo root |
| See what ran | `logs/agent.log` and `logs/runs/<date>.json` |
| Audit licensing | `python -m scripts.audit_licensing` |
| See the weekly report | `python -m scripts.report` |
