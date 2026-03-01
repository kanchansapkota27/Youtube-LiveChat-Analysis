-- =============================================================================
-- Schema
-- =============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT        PRIMARY KEY,
    video_id        TEXT        NOT NULL DEFAULT '',
    video_title     TEXT        NOT NULL DEFAULT 'Loading...',
    channel_name    TEXT        NOT NULL DEFAULT '',
    video_url       TEXT        NOT NULL DEFAULT '',
    thumbnail_url   TEXT        NOT NULL DEFAULT '',
    status          TEXT        NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    paused_at       TIMESTAMPTZ,
    last_checkpoint TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ,
    resumed_at      TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS chats (
    id                  BIGSERIAL   PRIMARY KEY,
    session_id          TEXT        NOT NULL REFERENCES sessions(session_id),
    video_id            TEXT        NOT NULL DEFAULT '',
    message_author_name TEXT        NOT NULL DEFAULT '',
    message_content     TEXT        NOT NULL DEFAULT '',
    message_dt          TIMESTAMPTZ,
    message_time_usec   BIGINT,
    inferred_sentiment  TEXT,
    has_profanity       BOOLEAN     NOT NULL DEFAULT FALSE,
    viewers_count       INTEGER     NOT NULL DEFAULT 0,
    is_live             BOOLEAN     NOT NULL DEFAULT TRUE,
    is_archived         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS video_info (
    id            SERIAL      PRIMARY KEY,
    session_id    TEXT        REFERENCES sessions(session_id),
    video_id      TEXT        NOT NULL DEFAULT '',
    channel_name  TEXT        NOT NULL DEFAULT '',
    channel_url   TEXT        NOT NULL DEFAULT '',
    video_title   TEXT        NOT NULL DEFAULT '',
    video_url     TEXT        NOT NULL DEFAULT '',
    thumbnail_url TEXT        NOT NULL DEFAULT '',
    is_live       BOOLEAN     NOT NULL DEFAULT FALSE,
    recorded_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================================
-- Indexes for analytics queries
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_chats_session_id       ON chats(session_id);
CREATE INDEX IF NOT EXISTS idx_chats_message_dt       ON chats(message_dt);
CREATE INDEX IF NOT EXISTS idx_chats_sentiment        ON chats(inferred_sentiment);
CREATE INDEX IF NOT EXISTS idx_chats_session_archived ON chats(session_id, is_archived);
CREATE INDEX IF NOT EXISTS idx_chats_created_at       ON chats(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_status        ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_video_info_video_id    ON video_info(video_id);

-- =============================================================================
-- LISTEN/NOTIFY trigger
-- Fires pg_notify('chat_<session_id>', <row as JSON>) on every chat insert.
-- The backend holds an asyncpg connection that LISTENs on this channel
-- and forwards the payload over SSE to the browser.
-- =============================================================================

CREATE OR REPLACE FUNCTION notify_chat_insert()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('chat_' || NEW.session_id, row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS chat_insert_notify ON chats;
CREATE TRIGGER chat_insert_notify
    AFTER INSERT ON chats
    FOR EACH ROW EXECUTE FUNCTION notify_chat_insert();
