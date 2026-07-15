CREATE TABLE IF NOT EXISTS posts (
    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verse_id INTEGER NOT NULL,
    theme TEXT NOT NULL,
    image_path TEXT NOT NULL,
    reel_path TEXT,
    caption_id TEXT,
    status TEXT DEFAULT 'pending',
    published_at TIMESTAMP,
    engagement_json TEXT
);

CREATE TABLE IF NOT EXISTS post_platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    platform_post_id TEXT,
    platform_url TEXT,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_polled_at TIMESTAMP,
    engagement_json TEXT,
    FOREIGN KEY(post_id) REFERENCES posts(post_id)
);

CREATE TABLE IF NOT EXISTS nasheed_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nasheed_file TEXT NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    post_id INTEGER,
    FOREIGN KEY(post_id) REFERENCES posts(post_id)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    dry_run BOOLEAN NOT NULL DEFAULT 0,
    cost_usd REAL,
    errors_json TEXT,
    manifest_path TEXT
);
