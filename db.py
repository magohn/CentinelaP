"""
SENTINELA v2 — Capa de Persistencia SQLite
"""
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea tablas si no existen."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id   TEXT,           -- ID único del post en la plataforma
            actor       TEXT NOT NULL,  -- nombre del actor/medio
            categoria   TEXT,           -- OFICIALISMO / OPOSICIÓN / OTROS / MEDIOS
            platform    TEXT NOT NULL,  -- twitter / instagram / facebook
            text        TEXT,
            url         TEXT,
            likes       INTEGER DEFAULT 0,
            comments    INTEGER DEFAULT 0,
            shares      INTEGER DEFAULT 0,
            views       INTEGER DEFAULT 0,
            published_at TEXT,          -- ISO timestamp del post original
            collected_at TEXT NOT NULL, -- cuándo lo recolectamos
            is_alert    INTEGER DEFAULT 0,
            UNIQUE(source_id, platform)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            media       TEXT NOT NULL,
            title       TEXT,
            summary     TEXT,
            url         TEXT UNIQUE,
            published_at TEXT,
            collected_at TEXT NOT NULL,
            is_alert    INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type  TEXT,           -- CRISIS / TRENDING
            actor       TEXT,
            platform    TEXT,
            keyword     TEXT,
            text        TEXT,
            url         TEXT,
            triggered_at TEXT NOT NULL,
            notified    INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_metrics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,  -- YYYY-MM-DD
            actor       TEXT NOT NULL,
            platform    TEXT NOT NULL,
            post_count  INTEGER DEFAULT 0,
            total_likes INTEGER DEFAULT 0,
            total_comments INTEGER DEFAULT 0,
            total_views INTEGER DEFAULT 0,
            UNIQUE(date, actor, platform)
        )
    """)

    conn.commit()
    conn.close()


# ── Guardar datos ─────────────────────────────────────────────────────────────

def save_post(actor, categoria, platform, text, url,
              likes=0, comments=0, shares=0, views=0,
              published_at=None, source_id=None):
    """Inserta un post; ignora duplicados por source_id+platform."""
    now = datetime.now(timezone.utc).isoformat()
    # Generar source_id a partir de URL si no viene
    if not source_id:
        source_id = url or f"{actor}_{platform}_{now}"

    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO posts
              (source_id, actor, categoria, platform, text, url,
               likes, comments, shares, views, published_at, collected_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (source_id, actor, categoria, platform, text, url,
              likes, comments, shares, views, published_at, now))
        conn.commit()
        return True
    except Exception as e:
        print(f"  [db] Error guardando post: {e}")
        return False
    finally:
        conn.close()


def save_news(media, title, summary, url, published_at=None):
    """Inserta una noticia; ignora duplicados por URL."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO news
              (media, title, summary, url, published_at, collected_at)
            VALUES (?,?,?,?,?,?)
        """, (media, title, summary, url, published_at, now))
        conn.commit()
        return True
    except Exception as e:
        print(f"  [db] Error guardando noticia: {e}")
        return False
    finally:
        conn.close()


def save_alert(alert_type, actor, platform, keyword, text, url):
    """Guarda una alerta de crisis."""
    now = datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    conn.execute("""
        INSERT INTO alerts
          (alert_type, actor, platform, keyword, text, url, triggered_at, notified)
        VALUES (?,?,?,?,?,?,?,0)
    """, (alert_type, actor, platform, keyword, text, url, now))
    conn.commit()
    conn.close()


def mark_alerts_notified():
    conn = get_conn()
    conn.execute("UPDATE alerts SET notified=1 WHERE notified=0")
    conn.commit()
    conn.close()


# ── Consultas ─────────────────────────────────────────────────────────────────

def get_today_posts():
    """Posts de las últimas 24 horas."""
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM posts
        WHERE collected_at >= ?
        ORDER BY likes DESC, collected_at DESC
    """, (since,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_news():
    """Noticias de las últimas 24 horas."""
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM news
        WHERE collected_at >= ?
        ORDER BY collected_at DESC
    """, (since,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_alerts():
    """Alertas que aún no han sido notificadas."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM alerts WHERE notified=0
        ORDER BY triggered_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_posts_last_2h():
    """Posts de las últimas 2 horas (para detección de alertas)."""
    since = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM posts WHERE collected_at >= ?
    """, (since,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_week_posts():
    """Posts de los últimos 7 días (para resumen semanal del sábado)."""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM posts
        WHERE collected_at >= ?
        ORDER BY likes DESC, collected_at DESC
    """, (since,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_week_news():
    """Noticias de los últimos 7 días."""
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM news
        WHERE collected_at >= ?
        ORDER BY collected_at DESC
    """, (since,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
