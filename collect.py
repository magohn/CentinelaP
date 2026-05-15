#!/usr/bin/env python3
"""
SENTINELA v2 — Módulo de Recolección
Corre cada 2 horas (4am–8pm) vía launchd.
Recolecta posts de Twitter (Nitter RSS), Instagram (instaloader) y RSS de medios.
Detecta crisis keywords y envía alertas inmediatas.
"""
import os
import sys
import time
import random
import smtplib
import feedparser
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# Asegurar que el directorio del script esté en el path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/social_monitor/.env"), override=True)

import db
from config import (
    POLITICAL_ACTORS, MEDIA_ACCOUNTS, NITTER_INSTANCES,
    CRISIS_KEYWORDS, TWITTER_KEYWORDS, MAX_TWEETS_PER_PROFILE, MAX_RSS_ITEMS,
    REPORT_EMAIL
)

GMAIL_USER         = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]

# ── Utilidades ───────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def normalize_dt(dt_str):
    """Convierte varias representaciones de fecha a ISO UTC string."""
    if not dt_str:
        return None
    try:
        # feedparser puede devolver struct_time
        if hasattr(dt_str, 'tm_year'):
            import calendar
            ts = calendar.timegm(dt_str)
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        # String RFC 2822 (email dates)
        dt = parsedate_to_datetime(str(dt_str))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            # ISO format directo
            return datetime.fromisoformat(str(dt_str).replace("Z", "+00:00")).isoformat()
        except Exception:
            return None


def contains_crisis(text):
    """Retorna la primera crisis keyword encontrada, o None."""
    if not text:
        return None
    text_lower = text.lower()
    for kw in CRISIS_KEYWORDS:
        if kw.lower() in text_lower:
            return kw
    return None


def is_political(text):
    """Retorna True si el texto contiene al menos una keyword política."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in TWITTER_KEYWORDS)


# ── Nitter RSS (Twitter sin API) ─────────────────────────────────────────────

def get_nitter_rss(handle, kind="profile"):
    """
    Intenta obtener RSS de Nitter probando instancias en orden aleatorio.
    kind: 'profile' → /handle/rss | 'search' → /search/rss?q=...
    """
    instances = NITTER_INSTANCES.copy()
    random.shuffle(instances)

    for base in instances:
        try:
            if kind == "profile":
                url = f"{base}/{handle}/rss"
            else:
                url = f"{base}/search/rss?q={handle}&f=tweets"

            resp = requests.get(url, timeout=12,
                                headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and "<rss" in resp.text:
                feed = feedparser.parse(resp.text)
                if feed.entries:
                    return feed.entries
        except Exception:
            continue

    return []


def fetch_twitter_actor(name, actor_info):
    """Recolecta tweets de un actor político."""
    handle = actor_info.get("twitter")
    if not handle:
        return 0

    categoria = actor_info.get("categoria", "OTROS")
    entries   = get_nitter_rss(handle)
    count     = 0

    for entry in entries[:MAX_TWEETS_PER_PROFILE]:
        text  = entry.get("summary", entry.get("title", ""))
        url   = entry.get("link", "")
        pub   = normalize_dt(entry.get("published_parsed") or entry.get("published"))

        # Filtrar: solo últimas 24h
        if pub:
            try:
                dt = datetime.fromisoformat(pub)
                if dt < datetime.now(timezone.utc) - timedelta(hours=24):
                    continue
            except Exception:
                pass

        saved = db.save_post(
            actor=name, categoria=categoria, platform="twitter",
            text=text, url=url, published_at=pub,
            source_id=entry.get("id", url)
        )

        if saved:
            count += 1
            kw = contains_crisis(text)
            if kw:
                db.save_alert("CRISIS", name, "twitter", kw, text[:400], url)
                log(f"  ⚠️  ALERTA: '{kw}' en tweet de {name}")

    return count


def fetch_twitter_media(media_name, media_info):
    """Recolecta tweets de un medio de comunicación."""
    handle = media_info.get("twitter")
    if not handle:
        return 0

    entries = get_nitter_rss(handle)
    count   = 0

    for entry in entries[:MAX_TWEETS_PER_PROFILE]:
        text = entry.get("summary", entry.get("title", ""))
        url  = entry.get("link", "")
        pub  = normalize_dt(entry.get("published_parsed") or entry.get("published"))

        if pub:
            try:
                dt = datetime.fromisoformat(pub)
                if dt < datetime.now(timezone.utc) - timedelta(hours=24):
                    continue
            except Exception:
                pass

        # Filtro político — descartar tweets sin contenido relevante
        if not is_political(text):
            continue

        saved = db.save_post(
            actor=media_name, categoria="MEDIOS", platform="twitter",
            text=text, url=url, published_at=pub,
            source_id=entry.get("id", url)
        )
        if saved:
            count += 1

    return count


# ── RSS de Medios ────────────────────────────────────────────────────────────

def fetch_rss(media_name, rss_url):
    """Recolecta artículos desde feed RSS de un medio."""
    if not rss_url:
        return 0

    try:
        feed  = feedparser.parse(rss_url)
        count = 0

        for entry in feed.entries[:MAX_RSS_ITEMS]:
            title   = entry.get("title", "")
            summary = entry.get("summary", "")[:500]
            url     = entry.get("link", "")
            pub     = normalize_dt(
                entry.get("published_parsed") or entry.get("published")
            )

            # Solo noticias de las últimas 24h
            if pub:
                try:
                    dt = datetime.fromisoformat(pub)
                    if dt < datetime.now(timezone.utc) - timedelta(hours=24):
                        continue
                except Exception:
                    pass

            saved = db.save_news(
                media=media_name, title=title, summary=summary,
                url=url, published_at=pub
            )
            if saved:
                count += 1
                kw = contains_crisis(title + " " + summary)
                if kw:
                    db.save_alert("CRISIS", media_name, "rss", kw,
                                  f"{title}: {summary[:200]}", url)
                    log(f"  ⚠️  ALERTA RSS: '{kw}' en {media_name}")

        return count
    except Exception as e:
        log(f"  [rss] Error {media_name}: {e}")
        return 0


# ── TikTok (pyktok) ─────────────────────────────────────────────────────────

def fetch_tiktok_actor(name, actor_info):
    """Recolecta videos de TikTok usando pyktok."""
    handle = actor_info.get("tiktok")
    if not handle:
        return 0

    categoria = actor_info.get("categoria", "OTROS")

    try:
        import pyktok as pyk
        pyk.specify_browser("chrome")

        videos = pyk.get_account_video_ids(handle)
        count  = 0
        since  = datetime.now(timezone.utc) - timedelta(hours=24)

        for vid_id in (videos or [])[:10]:
            try:
                meta = pyk.get_tiktok_json(
                    f"https://www.tiktok.com/@{handle}/video/{vid_id}", "chrome"
                )
                item = (meta.get("itemInfo", {}) or {}).get("itemStruct", {}) or {}
                if not item:
                    continue

                create_ts = item.get("createTime", 0)
                if create_ts:
                    pub_dt = datetime.fromtimestamp(int(create_ts), tz=timezone.utc)
                    if pub_dt < since:
                        continue
                    pub_iso = pub_dt.isoformat()
                else:
                    pub_iso = None

                text   = item.get("desc", "")
                stats  = item.get("stats", {})
                likes  = stats.get("diggCount", 0)
                comms  = stats.get("commentCount", 0)
                views  = stats.get("playCount", 0)
                url    = f"https://www.tiktok.com/@{handle}/video/{vid_id}"

                saved = db.save_post(
                    actor=name, categoria=categoria, platform="tiktok",
                    text=text, url=url,
                    likes=likes, comments=comms, views=views,
                    published_at=pub_iso, source_id=str(vid_id)
                )
                if saved:
                    count += 1
                    kw = contains_crisis(text)
                    if kw:
                        db.save_alert("CRISIS", name, "tiktok", kw, text[:400], url)
                        log(f"  ⚠️  ALERTA TikTok: '{kw}' en {name}")

                time.sleep(random.uniform(1, 3))
            except Exception:
                continue

        return count
    except Exception as e:
        log(f"  [tiktok] Error {name}: {e}")
        return 0


# ── Instagram (instaloader) ──────────────────────────────────────────────────

def fetch_instagram_actor(name, actor_info):
    """Recolecta posts de Instagram usando instaloader."""
    handle = actor_info.get("instagram")
    if not handle:
        return 0

    categoria = actor_info.get("categoria", "OTROS")

    try:
        import instaloader
        L = instaloader.Instaloader(
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
        )
        profile = instaloader.Profile.from_username(L.context, handle)
        count   = 0
        since   = datetime.now(timezone.utc) - timedelta(hours=24)

        for post in profile.get_posts():
            post_dt = post.date_utc.replace(tzinfo=timezone.utc)
            if post_dt < since:
                break
            saved = db.save_post(
                actor=name, categoria=categoria, platform="instagram",
                text=post.caption or "", url=post.url or f"https://www.instagram.com/p/{post.shortcode}/",
                likes=post.likes, comments=post.comments,
                published_at=post_dt.isoformat(),
                source_id=post.shortcode
            )
            if saved:
                count += 1
            if count >= 5:
                break

        return count
    except Exception as e:
        log(f"  [ig] Error {name}: {e}")
        return 0


# ── Alertas inmediatas ───────────────────────────────────────────────────────

def send_immediate_alert(alerts):
    """Envía email de alerta inmediata para crisis detectadas."""
    if not alerts:
        return

    rows_html = ""
    for a in alerts:
        rows_html += f"""
        <tr>
          <td style="padding:8px;border-bottom:1px solid #eee"><b>{a['actor']}</b></td>
          <td style="padding:8px;border-bottom:1px solid #eee">{a['platform'].upper()}</td>
          <td style="padding:8px;border-bottom:1px solid #eee;color:#c0392b"><b>{a['keyword']}</b></td>
          <td style="padding:8px;border-bottom:1px solid #eee">{(a['text'] or '')[:200]}</td>
          <td style="padding:8px;border-bottom:1px solid #eee">
            <a href="{a['url'] or '#'}">Ver fuente</a>
          </td>
        </tr>"""

    html = f"""
    <html><body>
    <div style="background:#c0392b;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0">
      <h2 style="margin:0">⚠️ SENTINELA — ALERTA DE CRISIS</h2>
      <p style="margin:6px 0 0;opacity:.85;font-size:13px">
        {datetime.now().strftime('%d/%m/%Y %H:%M')} · Detección automática
      </p>
    </div>
    <div style="padding:20px;border:1px solid #ddd;border-top:none;border-radius:0 0 8px 8px">
      <p>Se detectaron <b>{len(alerts)}</b> publicaciones con palabras clave de crisis:</p>
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <tr style="background:#2c3e50;color:#fff">
          <th style="padding:8px">Actor</th>
          <th style="padding:8px">Plataforma</th>
          <th style="padding:8px">Keyword</th>
          <th style="padding:8px">Extracto</th>
          <th style="padding:8px">Fuente</th>
        </tr>
        {rows_html}
      </table>
    </div>
    </body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⚠️ SENTINELA ALERTA — {datetime.now().strftime('%d/%m %H:%M')}"
        msg["From"]    = GMAIL_USER
        msg["To"]      = REPORT_EMAIL
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, REPORT_EMAIL, msg.as_string())
        log(f"  ✓ Alerta enviada a {REPORT_EMAIL}")
        db.mark_alerts_notified()
    except Exception as e:
        log(f"  [email] Error enviando alerta: {e}")


# ── Ciclo principal de recolección ───────────────────────────────────────────

def collect_cycle():
    log("=" * 60)
    log("SENTINELA v2 — Ciclo de recolección iniciado")
    db.init_db()

    total_posts = 0
    total_news  = 0

    # ── Twitter de actores políticos ──────────────────────────────────────
    log("→ Twitter / Actores Políticos")
    for name, info in POLITICAL_ACTORS.items():
        n = fetch_twitter_actor(name, info)
        if n > 0:
            log(f"    {name}: {n} tweets")
        total_posts += n
        time.sleep(random.uniform(2, 5))  # cortesía al servidor Nitter

    # ── Twitter de medios ─────────────────────────────────────────────────
    log("→ Twitter / Medios de Comunicación")
    for media_name, media_info in MEDIA_ACCOUNTS.items():
        n = fetch_twitter_media(media_name, media_info)
        if n > 0:
            log(f"    {media_name}: {n} tweets")
        total_posts += n
        time.sleep(random.uniform(2, 4))

    # ── RSS de medios ─────────────────────────────────────────────────────
    log("→ RSS / Medios de Comunicación")
    for media_name, media_info in MEDIA_ACCOUNTS.items():
        rss = media_info.get("rss")
        if rss:
            n = fetch_rss(media_name, rss)
            if n > 0:
                log(f"    {media_name} RSS: {n} noticias")
            total_news += n
            time.sleep(1)

    # ── TikTok — desactivado temporalmente (API de pyktok cambió)
    # log("→ TikTok / Actores Políticos")
    # Para reactivar: actualizar fetch_tiktok_actor() con nueva API de pyktok

    # ── Instagram desactivado (requiere sesión activa; se evita para no bloquear)
    # Para activar: descomentar y hacer login con instaloader CLI primero
    # log("→ Instagram / Actores Políticos")
    # for name, info in POLITICAL_ACTORS.items():
    #     if info.get("instagram"):
    #         n = fetch_instagram_actor(name, info)
    #         if n > 0:
    #             log(f"    {name}: {n} posts IG")
    #         total_posts += n
    #         time.sleep(random.uniform(3, 7))

    log(f"\n✓ Ciclo completo: {total_posts} posts · {total_news} noticias")

    # ── Alertas pendientes ────────────────────────────────────────────────
    pending = db.get_pending_alerts()
    if pending:
        log(f"⚠️  {len(pending)} alerta(s) pendiente(s) — enviando email")
        send_immediate_alert(pending)
    else:
        log("✓ Sin alertas de crisis en este ciclo")

    log("=" * 60)


if __name__ == "__main__":
    collect_cycle()
