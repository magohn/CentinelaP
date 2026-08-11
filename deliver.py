#!/usr/bin/env python3
"""
CENTINELA v2 — Módulo de Entrega
Corre a las 8:30pm diariamente vía launchd.
Genera reporte con Claude AI y envía por email.
Los sábados genera además el resumen semanal.
"""
import os
import sys
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/social_monitor/.env"), override=True)

import anthropic
import db
from config import POLITICAL_ACTORS, MEDIA_ACCOUNTS, REPORT_EMAIL, REPORTS_DIR

GMAIL_USER         = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── Construcción del resumen de datos para Claude ────────────────────────────

def trim_post(p, max_text=200):
    """Reduce un post a los campos esenciales para no saturar el prompt."""
    return {
        "text":     (p.get("text") or "")[:max_text],
        "url":      p.get("url", ""),
        "likes":    p.get("likes", 0),
        "comments": p.get("comments", 0),
        "views":    p.get("views", 0),
        "published_at": p.get("published_at", ""),
    }


def build_data_summary(posts, news_items, period="day"):
    """
    Organiza posts y noticias en un diccionario estructurado para Claude.
    Limita el volumen de datos para evitar timeouts en la API.
    period: 'day' (últimas 24h) | 'week' (últimos 7 días)
    """
    MAX_POSTS_PER_ACTOR = 5   # máx 5 posts por actor político
    MAX_POSTS_PER_MEDIA = 5   # máx 5 tweets por medio
    MAX_NEWS_PER_MEDIA  = 3   # máx 3 noticias RSS por medio

    summary = {
        "actores_politicos": {},
        "medios_twitter":    {},
        "medios_rss":        {},
    }

    # ── Actores políticos ─────────────────────────────────────────────────
    for name, info in POLITICAL_ACTORS.items():
        actor_posts = [p for p in posts if p["actor"] == name]
        # Ordenar por engagement y tomar los más relevantes
        actor_posts.sort(key=lambda p: (p.get("likes",0) + p.get("comments",0)), reverse=True)
        summary["actores_politicos"][name] = {
            "rol":       info.get("rol", ""),
            "partido":   info.get("partido", ""),
            "categoria": info.get("categoria", "OTROS"),
            "twitter":   [trim_post(p) for p in actor_posts if p["platform"] == "twitter"][:MAX_POSTS_PER_ACTOR],
            "instagram": [trim_post(p) for p in actor_posts if p["platform"] == "instagram"][:MAX_POSTS_PER_ACTOR],
            "tiktok":    [trim_post(p) for p in actor_posts if p["platform"] == "tiktok"][:MAX_POSTS_PER_ACTOR],
        }

    # ── Medios — Twitter ──────────────────────────────────────────────────
    for media_name in MEDIA_ACCOUNTS:
        media_posts = [p for p in posts
                       if p["actor"] == media_name and p["platform"] == "twitter"]
        media_posts.sort(key=lambda p: (p.get("likes",0) + p.get("comments",0)), reverse=True)
        summary["medios_twitter"][media_name] = [trim_post(p) for p in media_posts[:MAX_POSTS_PER_MEDIA]]

    # ── Medios — RSS ──────────────────────────────────────────────────────
    for media_name in MEDIA_ACCOUNTS:
        media_news = [n for n in news_items if n["media"] == media_name]
        summary["medios_rss"][media_name] = [
            {
                "title":        n["title"],
                "summary":      (n["summary"] or "")[:200],
                "url":          n["url"],
                "published_at": n["published_at"],
            }
            for n in media_news[:MAX_NEWS_PER_MEDIA]
        ]

    return json.dumps(summary, ensure_ascii=False, indent=2)


# ── Prompts para Claude ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres CENTINELA, un sistema de inteligencia política hondureña desarrollado por Stratégica.
Tu tarea es analizar publicaciones de redes sociales y medios de comunicación
de actores políticos y medios hondureños, y producir un informe estructurado,
preciso y accionable.

CONTEXTO POLÍTICO ACTUAL (mayo 2026):
- Presidente de Honduras: Nasry "Tito" Asfura (Partido Nacional, desde 27 ene 2026)
- Expresidenta: Xiomara Castro (Partido Libre, mandato 2022–2026)
- Presidente del Congreso: Tomas Zambrano (Partido Nacional)
- Partido oficialista: Partido Nacional
- Partido Libre: OPOSICIÓN
- Roberto Contreras: Alcalde de San Pedro Sula, Partido Liberal de Honduras

INSTRUCCIONES DE FORMATO — MUY IMPORTANTE:
- Usa ÚNICAMENTE etiquetas HTML válidas: <p>, <ul>, <li>, <strong>, <em>, <table>, <tr>, <td>, <th>
- NUNCA uses markdown: no **negrita**, no *cursiva*, no # títulos, no - guiones como bullets
- Cada punto va dentro de <li></li>, cada párrafo dentro de <p></p>
- Deja espacio visual entre subsecciones usando <p>&nbsp;</p> o <br>
- La red social X (antes Twitter) se llama SIEMPRE "X", nunca "Twitter"
- Sé conciso: máximo 4 bullets por subsección
- INSTRUCCIÓN CRÍTICA: Analiza ÚNICAMENTE los datos reales proporcionados.
  No inventes información. Si no hay datos, indícalo con <p><em>Sin actividad registrada.</em></p>"""

DAILY_PROMPT = """Analiza los datos de redes sociales y medios de comunicación
de actores políticos hondureños recopilados HOY ({date}) y genera el informe
diario de CENTINELA.

PERÍODO: Últimas 24 horas ({period_start} → {period_end})

DATOS:
{data}

Genera el informe en HTML limpio con EXACTAMENTE estas 9 secciones en este orden:

<h2>📋 1. RESUMEN EJECUTIVO</h2>
- Síntesis del día político en 3–4 oraciones
- Los 3 hechos más importantes del día (listado breve)
- Nivel del clima político: indica claramente si es TENSO / MODERADO / TRANQUILO y por qué

<h2>🏛️ 2. AGENDA DEL GOBIERNO</h2>
Acciones y declaraciones del oficialismo. Subsecciones:
- Presidencia (Nasry Asfura): publicaciones, declaraciones, eventos
- Congreso Nacional (Tomás Zambrano): sesiones, leyes, decretos, declaraciones
- Ministros (Emilio Hércules / Yaudeth Búrbara): apariciones y acciones
- Otros eventos oficiales relevantes
Si algún actor no tuvo actividad, indicarlo.

<h2>🗂️ 3. MAPA DE TEMAS DEL DÍA</h2>
Genera una tabla HTML con columnas: Tema | Categoría | Red | Volumen | Tendencia
- Categoría: 🟢 Positivo · 🔴 Conflicto · 🟡 Neutral · 🚨 Crisis
- Volumen: Alto / Medio / Bajo
- Tendencia: ↑ Subiendo · → Estable · ↓ Bajando
- En la columna "Red" usa siempre "X" nunca "Twitter"

<h2>📰 4. COBERTURA MEDIÁTICA</h2>
Para cada medio usa este formato HTML exacto:
<h3>[Nombre del medio]</h3>
<ul>
<li><strong>Temas cubiertos:</strong> [lista]</li>
<li><strong>Nota destacada:</strong> [la más relevante]</li>
<li><strong>Tono:</strong> CRÍTICO / NEUTRAL / FAVORABLE AL GOBIERNO</li>
</ul>

<h2>👤 5. FICHA POR ACTOR POLÍTICO</h2>
Para cada actor (Presidencia HN, Asfura, Zambrano, Hércules, Búrbara, Xiomara Castro,
Zelaya, Nasralla, Iroska Elvir, Rixi Moncada, Octavio Pineda, Roberto Contreras, JOH)
usa este formato:
<h3>[Nombre] — [Partido/Rol]</h3>
<ul>
<li><strong>Actividad en X:</strong> [resumen o "Sin actividad registrada"]</li>
<li><strong>Reacción ciudadana:</strong> Positiva / Negativa / Mixta / Sin datos</li>
<li><strong>Nivel de aceptación:</strong> [1–10]</li>
<li><strong>Temas generados:</strong> [lista breve]</li>
</ul>

<h2>⚠️ 6. ALERTAS DE ESCALADA</h2>
Para cada alerta usa:
<ul>
<li><strong>Riesgo:</strong> [descripción]</li>
<li><strong>Por qué escala:</strong> [razón]</li>
<li><strong>Tiempo:</strong> Inmediato / Próximas 48h / Próxima semana</li>
<li><strong>Recomendación:</strong> [acción concreta]</li>
</ul>
Si no hay alertas: <p><em>Sin alertas de escalada detectadas.</em></p>

<h2>🔵 7. ANÁLISIS DE OPOSICIÓN</h2>
<ul>
<li><strong>Narrativas principales:</strong> [lista]</li>
<li><strong>Coordinación entre partidos:</strong> Alta / Media / Baja</li>
<li><strong>Tácticas utilizadas:</strong> [lista]</li>
<li><strong>Temas que intentan instalar:</strong> [lista]</li>
</ul>

<h2>📊 8. MÉTRICAS GENERALES DEL DÍA</h2>
<ul>
<li><strong>Mayor interacción positiva:</strong> [actor y dato]</li>
<li><strong>Mayor interacción negativa:</strong> [actor y dato]</li>
<li><strong>Tema más viral:</strong> [tema]</li>
<li><strong>Red más activa:</strong> [red — usa "X" no "Twitter"]</li>
<li><strong>Hashtags en tendencia:</strong> [lista o "Sin datos"]</li>
</ul>

<h2>🎯 9. RECOMENDACIONES ESTRATÉGICAS</h2>
Exactamente 3 recomendaciones. Para cada una:
<h3>[Título de la recomendación]</h3>
<ul>
<li><strong>Contexto:</strong> [por qué es relevante ahora]</li>
<li><strong>Acción sugerida:</strong> [acción concreta]</li>
<li><strong>Urgencia:</strong> ALTA / MEDIA / BAJA</li>
</ul>"""

WEEKLY_PROMPT = """Analiza los datos de la semana {week_start}–{week_end}
y genera el RESUMEN SEMANAL de CENTINELA.

DATOS DE LA SEMANA:
{data}

Genera el informe semanal en HTML con estas secciones:

<h2>📊 BALANCE SEMANAL</h2>
Tabla de actividad por actor: total de posts, engagement acumulado, plataforma más activa.

<h2>🏆 TEMAS DE LA SEMANA</h2>
Los 5 temas más relevantes que dominaron la agenda política esta semana.
Para cada uno: evolución día a día, actores involucrados, resolución o estado actual.

<h2>📈 ACTOR DE LA SEMANA</h2>
El actor político con mayor impacto/actividad. Análisis de su estrategia de comunicación.

<h2>🗞️ MEDIOS: AGENDA EDITORIAL</h2>
Qué temas priorizaron los medios esta semana. ¿Coinciden con la agenda del gobierno?

<h2>🔮 PERSPECTIVA DE LA PRÓXIMA SEMANA</h2>
Basado en la semana que termina: qué temas, conflictos o eventos podrían dominar la próxima semana."""


# ── Análisis con Claude ──────────────────────────────────────────────────────

def analyze_daily(data_summary):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    now    = datetime.now()
    since  = (now - timedelta(hours=24)).strftime("%d/%m %H:%M")

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": DAILY_PROMPT.format(
                date=now.strftime("%d de %B, %Y"),
                period_start=since,
                period_end=now.strftime("%d/%m %H:%M"),
                data=data_summary,
            )
        }]
    )
    return msg.content[0].text


def analyze_weekly(data_summary):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    now    = datetime.now()
    week_start = (now - timedelta(days=6)).strftime("%d/%m")

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": WEEKLY_PROMPT.format(
                week_start=week_start,
                week_end=now.strftime("%d/%m/%Y"),
                data=data_summary,
            )
        }]
    )
    return msg.content[0].text


# ── HTML del email ───────────────────────────────────────────────────────────

def build_email_html(analysis_html, report_type="DIARIO", weekly_block=""):
    now = datetime.now()
    date_str = now.strftime("%d de %B, %Y · %H:%M")

    icon   = "🛡️"
    titulo = "INFORME DIARIO + RESUMEN SEMANAL" if weekly_block else "INFORME DIARIO"

    return f"""
    <html>
    <head>
      <style>
        body  {{ font-family: Arial, sans-serif; max-width: 960px; margin: 0 auto; color: #222; }}
        h2    {{ margin-top: 28px; padding: 8px 14px; border-radius: 6px;
                 background: #f0f4f8; border-left: 4px solid #1a3a6b; }}
        table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }}
        th    {{ background: #2c3e50; color: #fff; padding: 9px 12px; text-align: left; }}
        td    {{ padding: 8px 12px; border-bottom: 1px solid #eee; vertical-align: top; }}
        tr:nth-child(even) {{ background: #f7f9fc; }}
        a     {{ color: #2980b9; }}
        p     {{ line-height: 1.6; }}
      </style>
    </head>
    <body>
      <div style="background:#1a3a6b;color:#fff;padding:20px 24px;border-radius:8px 8px 0 0">
        <div style="display:flex;align-items:center;gap:14px">
          <span style="font-size:40px">{icon}</span>
          <div>
            <h1 style="margin:0;font-size:28px;font-weight:900;letter-spacing:1px">CENTINELA</h1>
            <div style="font-size:11px;opacity:.80;margin-top:3px;letter-spacing:1px">
              Desarrollado por: <b>Stratégica</b>
            </div>
            <div style="font-size:11px;opacity:.65;margin-top:2px;text-transform:uppercase;letter-spacing:2px">
              {titulo} · Inteligencia Política Honduras
            </div>
          </div>
        </div>
        <p style="margin:12px 0 0;opacity:.75;font-size:13px;
                  border-top:1px solid rgba(255,255,255,.25);padding-top:10px">
          📅 {date_str}
        </p>
      </div>

      <div style="padding:20px;background:#fff;border:1px solid #ddd;
                  border-top:none;border-radius:0 0 8px 8px">
        <div style="background:#e8edf5;border-left:4px solid #1a3a6b;
                    padding:10px 14px;border-radius:4px;margin-bottom:20px;font-size:13px">
          Actores monitoreados: <b>Presidencia HN · Nasry Asfura · Tomas Zambrano ·
          Emilio Hércules · Yaudeth Búrbara · Xiomara Castro · Manuel Zelaya ·
          Salvador Nasralla · Iroska Elvir · Rixi Moncada · Octavio Pineda ·
          Roberto Contreras · JOH</b>
          <br>Medios: <b>HCH · TSI Honduras · Tu Nota · Once Noticias · QHubo ·
          La Prensa · La Tribuna · HRN · Radio América · Cadena Voces</b>
        </div>
        {analysis_html}
        {f'''
        <hr style="margin:32px 0;border:none;border-top:3px solid #1a3a6b">
        <div style="background:#1a3a6b;color:#fff;padding:12px 16px;border-radius:6px;margin-bottom:20px">
          <span style="font-size:22px">📅</span>
          <strong style="font-size:16px;margin-left:8px">RESUMEN SEMANAL</strong>
        </div>
        {weekly_block}
        ''' if weekly_block else ''}
      </div>

      <p style="color:#aaa;font-size:11px;text-align:center;margin-top:12px">
        🛡️ CENTINELA — Desarrollado por Stratégica · Inteligencia Política Honduras
      </p>
    </body>
    </html>"""


# ── Guardar reporte local ────────────────────────────────────────────────────

def save_local_report(html, report_type="diario"):
    """Guarda el reporte HTML en ~/social_monitor/reportes/YYYY/MM/"""
    now = datetime.now()
    dir_path = os.path.join(
        REPORTS_DIR,
        now.strftime("%Y"),
        now.strftime("%m"),
    )
    os.makedirs(dir_path, exist_ok=True)
    filename = f"centinela_{report_type}_{now.strftime('%Y-%m-%d_%H%M')}.html"
    path     = os.path.join(dir_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"  ✓ Reporte guardado: {path}")
    return path


# ── Envío de email ───────────────────────────────────────────────────────────

def send_email(html, subject):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = GMAIL_USER  # Solo se muestra el remitente
    recipients = REPORT_EMAIL if isinstance(REPORT_EMAIL, list) else [REPORT_EMAIL]
    msg["Bcc"]  = ", ".join(recipients)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.sendmail(GMAIL_USER, recipients, msg.as_string())
    log(f"  ✓ Email enviado (BCC) a {len(recipients)} destinatarios")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    log("=" * 60)
    log("CENTINELA v2 — Módulo de entrega iniciado")
    db.init_db()

    now = datetime.now()
    is_saturday = now.weekday() == 5

    # ── Informe diario ────────────────────────────────────────────────────
    log("→ Cargando datos de las últimas 24h…")
    posts = db.get_today_posts()
    news  = db.get_today_news()
    log(f"   {len(posts)} posts · {len(news)} noticias")

    if posts or news:
        log("→ Analizando con Claude AI…")
        data_summary  = build_data_summary(posts, news, period="day")
        analysis_html = analyze_daily(data_summary)

        # ── Los viernes noche (sábado UTC) incluir resumen semanal en el mismo correo
        weekly_block = ""
        if is_saturday:
            log("→ Es viernes noche HN (sábado UTC) — adjuntando resumen semanal…")
            week_posts = db.get_week_posts()
            week_news  = db.get_week_news()
            log(f"   {len(week_posts)} posts · {len(week_news)} noticias (semana)")
            if week_posts or week_news:
                data_week    = build_data_summary(week_posts, week_news, period="week")
                weekly_block = analyze_weekly(data_week)

        email_html = build_email_html(analysis_html, report_type="DIARIO",
                                      weekly_block=weekly_block)
        save_local_report(email_html, report_type="diario")

        if is_saturday:
            week_start = (now - timedelta(days=6)).strftime("%d/%m")
            subject = f"🛡️ CENTINELA — {now.strftime('%A %d/%m/%Y')} · Diario + Resumen Semanal {week_start}–{now.strftime('%d/%m')}"
        else:
            subject = f"🛡️ CENTINELA — {now.strftime('%A %d/%m/%Y')} · Informe Diario"

        log("→ Enviando informe…")
        send_email(email_html, subject)
        db.mark_alerts_notified()
    else:
        log("  ⚠️  Sin datos para informe diario (¿collect.py corrió?)")

    log("✓ Entrega completa")
    log("=" * 60)


if __name__ == "__main__":
    main()
