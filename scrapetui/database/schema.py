"""Database schema definitions for WebScrape-TUI."""

from typing import List

SCHEMA_VERSION = "2.0.0"


def get_schema_v2_0_0() -> str:
    """Get v2.0.0 database schema with multi-user support."""
    return """
-- Schema version 2.0.0
-- Multi-user foundation with authentication and RBAC

-- Users table (v2.0.0)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('admin', 'user', 'viewer')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- User sessions table (v2.0.0)
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Articles/scraped data table
CREATE TABLE IF NOT EXISTS scraped_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    summary TEXT,
    link TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentiment TEXT,
    user_id INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET DEFAULT
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Article-tag association table
CREATE TABLE IF NOT EXISTS article_tags (
    article_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

-- Saved scraper profiles table
CREATE TABLE IF NOT EXISTS saved_scrapers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    selector TEXT NOT NULL,
    default_limit INTEGER DEFAULT 0,
    default_tags_csv TEXT,
    description TEXT,
    is_preinstalled INTEGER DEFAULT 0,
    user_id INTEGER DEFAULT 1,
    is_shared INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET DEFAULT
);

-- Summarization templates table
CREATE TABLE IF NOT EXISTS summarization_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    template TEXT NOT NULL,
    description TEXT,
    is_builtin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Filter presets table
CREATE TABLE IF NOT EXISTS filter_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    title_filter TEXT,
    url_filter TEXT,
    date_from TEXT,
    date_to TEXT,
    tags_filter TEXT,
    sentiment_filter TEXT,
    use_regex INTEGER DEFAULT 0,
    tags_logic TEXT DEFAULT 'AND',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled scrapes table (v1.5.0)
CREATE TABLE IF NOT EXISTS scheduled_scrapes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    scraper_profile_id INTEGER,
    schedule_type TEXT NOT NULL,
    schedule_value TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    run_count INTEGER DEFAULT 0,
    last_status TEXT,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scraper_profile_id) REFERENCES saved_scrapers(id) ON DELETE CASCADE
);

-- Topic modeling tables (v1.9.0)
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    keywords TEXT,
    model_type TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS article_topics (
    article_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    confidence REAL,
    is_primary INTEGER DEFAULT 0,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, topic_id)
);

-- Entity relationship tables (v1.9.0)
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL UNIQUE,
    entity_type TEXT,
    count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS article_entities (
    article_id INTEGER NOT NULL,
    entity_id INTEGER NOT NULL,
    occurrences INTEGER DEFAULT 1,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, entity_id)
);

CREATE TABLE IF NOT EXISTS entity_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity1_id INTEGER NOT NULL,
    entity2_id INTEGER NOT NULL,
    relationship_type TEXT DEFAULT 'co-occurrence',
    weight INTEGER DEFAULT 1,
    article_id INTEGER,
    FOREIGN KEY (entity1_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (entity2_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE
);

-- Q&A history table (v1.9.0)
CREATE TABLE IF NOT EXISTS qa_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    article_ids TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Summary feedback table (v1.9.0)
CREATE TABLE IF NOT EXISTS summary_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    summary_id TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE
);

-- Summary quality table (v1.9.0)
CREATE TABLE IF NOT EXISTS summary_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL UNIQUE,
    rouge1 REAL,
    rouge2 REAL,
    rougeL REAL,
    coherence_score REAL,
    user_rating INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE
);

-- Article clusters table (v1.9.0)
CREATE TABLE IF NOT EXISTS article_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    cluster_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES scraped_data(id) ON DELETE CASCADE
);

-- Schema version tracking table
CREATE TABLE IF NOT EXISTS schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
"""


def get_indexes() -> str:
    """Get index creation SQL."""
    return """
-- Performance indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_link_unique ON scraped_data (link);
CREATE INDEX IF NOT EXISTS idx_url ON scraped_data (url);
CREATE INDEX IF NOT EXISTS idx_timestamp ON scraped_data (timestamp);
CREATE INDEX IF NOT EXISTS idx_title ON scraped_data (title);
CREATE INDEX IF NOT EXISTS idx_sentiment ON scraped_data (sentiment);
CREATE INDEX IF NOT EXISTS idx_scraped_data_user_id ON scraped_data(user_id);

CREATE INDEX IF NOT EXISTS idx_tag_name ON tags (name);
CREATE INDEX IF NOT EXISTS idx_article_tags_article ON article_tags (article_id);
CREATE INDEX IF NOT EXISTS idx_article_tags_tag ON article_tags (tag_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_scraper_name ON saved_scrapers (name);
CREATE INDEX IF NOT EXISTS idx_saved_scrapers_user ON saved_scrapers (user_id);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);

-- Advanced AI indexes (v1.9.0)
CREATE INDEX IF NOT EXISTS idx_topics_model_type ON topics (model_type);
CREATE INDEX IF NOT EXISTS idx_article_topics_article ON article_topics (article_id);
CREATE INDEX IF NOT EXISTS idx_article_topics_topic ON article_topics (topic_id);
CREATE INDEX IF NOT EXISTS idx_entities_text ON entities (text);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities (entity_type);
CREATE INDEX IF NOT EXISTS idx_article_entities_article ON article_entities (article_id);
CREATE INDEX IF NOT EXISTS idx_article_entities_entity ON article_entities (entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_entity1 ON entity_relationships (entity1_id);
CREATE INDEX IF NOT EXISTS idx_entity_relationships_entity2 ON entity_relationships (entity2_id);
CREATE INDEX IF NOT EXISTS idx_qa_history_created ON qa_history (created_at);
CREATE INDEX IF NOT EXISTS idx_summary_feedback_article ON summary_feedback (article_id);
CREATE INDEX IF NOT EXISTS idx_article_clusters_cluster ON article_clusters (cluster_id);
CREATE INDEX IF NOT EXISTS idx_article_clusters_article ON article_clusters (article_id);
"""


def get_builtin_data() -> str:
    """Get built-in data (default admin user, preinstalled scrapers, templates)."""
    return """
-- Default admin user (username: admin, password: Ch4ng3M3)
-- Password hash generated with bcrypt cost factor 12
INSERT OR IGNORE INTO users (id, username, password_hash, email, role, is_active)
VALUES (
    1,
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eiE0gW5VG8Gy',
    'admin@localhost',
    'admin',
    1
);

-- Preinstalled scraper profiles
INSERT OR IGNORE INTO saved_scrapers (
    name, url, selector, default_limit, default_tags_csv,
    description, is_preinstalled, user_id, is_shared
) VALUES
    ('TechCrunch', 'https://techcrunch.com', 'article', 10, 'tech,news',
     'Latest technology news and startup coverage', 1, 1, 1),
    ('The Verge', 'https://www.theverge.com', 'article', 10, 'tech,gadgets',
     'Technology, science, and culture news', 1, 1, 1),
    ('Ars Technica', 'https://arstechnica.com', 'article', 10, 'tech,science',
     'In-depth technology and science journalism', 1, 1, 1),
    ('Hacker News', 'https://news.ycombinator.com', '.storylink', 15, 'tech,programming',
     'Tech and startup community news', 1, 1, 1),
    ('Reddit r/programming', 'https://reddit.com/r/programming', '.thing', 15, 'programming',
     'Programming discussions and news', 1, 1, 1),
    ('BBC News', 'https://www.bbc.com/news', 'article', 10, 'news,world',
     'International news coverage', 1, 1, 1),
    ('The Guardian Tech', 'https://www.theguardian.com/technology', 'article', 10, 'tech,news',
     'Technology section of The Guardian', 1, 1, 1),
    ('Wired', 'https://www.wired.com', 'article', 10, 'tech,culture',
     'Technology, business, and culture', 1, 1, 1),
    ('MIT Technology Review', 'https://www.technologyreview.com', 'article', 10, 'tech,research',
     'Emerging technology research and analysis', 1, 1, 1),
    ('Stack Overflow Blog', 'https://stackoverflow.blog', 'article', 10, 'programming,dev',
     'Developer community and programming insights', 1, 1, 1);

-- Built-in summarization templates
INSERT OR IGNORE INTO summarization_templates (name, template, description, is_builtin) VALUES
    ('Overview',
     'Provide a concise overview (100-150 words) of the following content:\n\n{content}\n\nOverview:',
     'Standard overview summary (100-150 words)', 1),
    ('Bullet Points',
     'Summarize the following content into key bullet points:\n\n{content}\n\nKey Points:',
     'Bullet-point summary of main ideas', 1),
    ('ELI5',
     'Explain the following content like I''m 5 years old:\n\n{content}\n\nSimple Explanation:',
     'Simplified explanation for general audience', 1),
    ('Academic',
     'Provide an academic-style summary with key findings, methodology, and conclusions:\n\n{content}\n\nAcademic Summary:',
     'Formal academic summary with structured analysis', 1),
    ('Executive Summary',
     'Create an executive summary highlighting key business insights, recommendations, and action items:\n\n{content}\n\nExecutive Summary:',
     'Business-focused summary with actionable insights', 1),
    ('Technical Brief',
     'Summarize the technical aspects, implementation details, and specifications:\n\n{content}\n\nTechnical Summary:',
     'Technical summary for engineering audience', 1),
    ('News Brief',
     'Write a news-style summary with who, what, when, where, why, and how:\n\n{content}\n\nNews Summary:',
     'Journalistic 5W1H summary format', 1);

-- Set schema version to 2.0.0
INSERT OR REPLACE INTO schema_version (version, description)
VALUES ('2.0.0', 'Multi-user foundation: users, sessions, ownership tracking');
"""


def get_schema() -> str:
    """
    Get complete database schema including tables, indexes, and built-in data.

    Returns:
        Complete SQL script for database initialization
    """
    return get_schema_v2_0_0() + "\n" + get_indexes() + "\n" + get_builtin_data()


def get_table_names() -> List[str]:
    """
    Get list of all table names in the schema.

    Returns:
        List of table names
    """
    return [
        'users',
        'user_sessions',
        'scraped_data',
        'tags',
        'article_tags',
        'saved_scrapers',
        'summarization_templates',
        'filter_presets',
        'scheduled_scrapes',
        'topics',
        'article_topics',
        'entities',
        'article_entities',
        'entity_relationships',
        'qa_history',
        'summary_feedback',
        'summary_quality',
        'article_clusters',
        'schema_version'
    ]
