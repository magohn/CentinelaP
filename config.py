"""
CENTINELA v2 — Configuración Central
Monitoreo de actores políticos y medios de comunicación en Honduras
Desarrollado por Stratégica
"""

# ── Actores Políticos ────────────────────────────────────────────────────────

POLITICAL_ACTORS = {
    # ── OFICIALISMO (Partido Nacional) ─────────────────────────────────────
    "Presidencia Honduras": {
        "rol":       "Cuenta oficial de la Presidencia de la República",
        "partido":   "Partido Nacional",
        "categoria": "OFICIALISMO",
        "twitter":   "hnpresidencia",
        "instagram": None,
        "facebook":  None,
        "tiktok":    None,
    },
    "Nasry Asfura": {
        "rol":       "Presidente de Honduras (desde 27 ene 2026)",
        "partido":   "Partido Nacional",
        "categoria": "OFICIALISMO",
        "twitter":   "Titoasfura",
        "instagram": "titoasfura",
        "facebook":  "https://www.facebook.com/titoasfura",
        "tiktok":    "papialaordenhn",
    },
    "Tomas Zambrano": {
        "rol":       "Presidente del Congreso Nacional",
        "partido":   "Partido Nacional",
        "categoria": "OFICIALISMO",
        "twitter":   "TommyZambranoM",
        "instagram": None,
        "facebook":  "https://www.facebook.com/TZambranoHN",
        "tiktok":    "Tommy_zambrano",
    },
    "Emilio Hercules": {
        "rol":       "Ministro de Finanzas",
        "partido":   "Partido Nacional",
        "categoria": "OFICIALISMO",
        "twitter":   "eehercules",
        "instagram": None,
        "facebook":  None,
        "tiktok":    "emiliohernandezhercules",
    },
    "Yaudeth Burbara": {
        "rol":       "Ministro de la ENP (Empresa Nacional Portuaria)",
        "partido":   "Partido Nacional",
        "categoria": "OFICIALISMO",
        "twitter":   "jrburbara",
        "instagram": "yaudethburbara",
        "facebook":  None,
        "tiktok":    "jrburbara",
    },
    "Luis Castro": {
        "rol":       "Secretario Privado de la Presidencia",
        "partido":   "Partido Nacional",
        "categoria": "OFICIALISMO",
        "twitter":   "Lcastro30",
        "instagram": None,
        "facebook":  None,
        "tiktok":    None,
    },

    # ── OPOSICIÓN (Partido Libre) ──────────────────────────────────────────
    "Xiomara Castro": {
        "rol":       "Expresidenta de Honduras (hasta 27 ene 2026)",
        "partido":   "Partido Libre",
        "categoria": "OPOSICIÓN",
        "twitter":   "XiomaraCastroZ",
        "instagram": "xiomaracastroz",
        "facebook":  "https://www.facebook.com/XiomaraCastroZ",
        "tiktok":    None,
    },
    "Manuel Zelaya Rosales": {
        "rol":       "Expresidente / Coordinador General Partido Libre",
        "partido":   "Partido Libre",
        "categoria": "OPOSICIÓN",
        "twitter":   "ManuelZelayaR",
        "instagram": None,
        "facebook":  "https://www.facebook.com/ManuelZelayaR",
        "tiktok":    None,
    },
    "Salvador Nasralla": {
        "rol":       "Diputado / Opositor",
        "partido":   "Partido Liberal de Honduras",
        "categoria": "OPOSICIÓN",
        "twitter":   "Salvapresidente",
        "instagram": "salvadornasralla",
        "facebook":  "https://www.facebook.com/SalvadorNasralla",
        "tiktok":    "salavadornasralla",
    },
    "Iroska Elvir": {
        "rol":       "Diputada",
        "partido":   "Partido Liberal de Honduras",
        "categoria": "OPOSICIÓN",
        "twitter":   "IroshkaElvir",
        "instagram": None,
        "facebook":  None,
        "tiktok":    "iroskanasralla",
    },

    # ── OTROS / RELEVANTES ─────────────────────────────────────────────────
    "Roberto Contreras": {
        "rol":       "Alcalde de San Pedro Sula / Presidente del Comité Central Ejecutivo del Partido Liberal de Honduras",
        "partido":   "Partido Liberal de Honduras",
        "categoria": "OTROS",
        "twitter":   "RobertoContreM",
        "instagram": "robertocontrerashonduras",
        "facebook":  "https://www.facebook.com/RobertoContrerasSPS",
        "tiktok":    "robertocontrerasmen",
    },
    "Rixi Moncada": {
        "rol":       "Excandidata presidencial de Libre / Militante",
        "partido":   "Partido Libre",
        "categoria": "OPOSICIÓN",
        "twitter":   "riximga",
        "instagram": None,
        "facebook":  None,
        "tiktok":    None,
    },
    "Octavio Pineda": {
        "rol":       "Exministro de la SIT (Secretaría de Infraestructura y Transporte) / Militante de Libre",
        "partido":   "Partido Libre",
        "categoria": "OPOSICIÓN",
        "twitter":   "octaJPP",
        "instagram": None,
        "facebook":  None,
        "tiktok":    None,
    },
    "Juan Orlando Hernandez": {
        "rol":       "Expresidente de Honduras (2014–2022)",
        "partido":   "Partido Nacional",
        "categoria": "OTROS",
        "twitter":   "JuanOrlandoH",
        "instagram": None,
        "facebook":  "https://www.facebook.com/JuanOrlandoH",
        "tiktok":    "juanorlandoha",
    },
}

# ── Medios de Comunicación ───────────────────────────────────────────────────

MEDIA_ACCOUNTS = {
    "HCH Televisión": {
        "twitter":   "HCHTelevDigital",
        "instagram": "hchtelevision",
        "rss":       "https://hch.tv/feed/",
    },
    "TSI Honduras": {
        "twitter":   "TSIHonduras",
        "instagram": None,
        "rss":       None,
    },
    "Tu Nota": {
        "twitter":   "tunota_com",
        "instagram": None,
        "rss":       None,
    },
    "Once Noticias": {
        "twitter":   "11_Noticias",
        "instagram": None,
        "rss":       None,
    },
    "QHubo": {
        "twitter":   "Qhubotvoficial",
        "instagram": "qhubohn",
        "rss":       None,
    },
    "La Prensa": {
        "twitter":   "DiarioLaPrensa",
        "instagram": "laprensahn",
        "rss":       "https://www.laprensa.hn/feed/",
    },
    "La Tribuna": {
        "twitter":   "LaTribunahn",
        "instagram": "latribunadiario",
        "rss":       "https://www.latribuna.hn/feed/",
    },
    "HRN": {
        "twitter":   "radiohrn",
        "instagram": "radiohrn",
        "rss":       "https://www.radiohrn.hn/feed/",
    },
    "Radio América": {
        "twitter":   "radioamericahn",
        "instagram": "radioamericahn",
        "rss":       None,
    },
    "Radio Cadena Voces": {
        "twitter":   "RCVHonduras",
        "instagram": None,
        "rss":       None,
    },
}

# ── Instancias Nitter (fallback automático) ──────────────────────────────────

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.it",
    "https://nitter.nl",
    "https://nitter.1d4.us",
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
]

# ── Palabras clave de crisis (alerta inmediata) ──────────────────────────────

CRISIS_KEYWORDS = [
    # 🚨 Ruptura institucional
    "golpe de Estado", "toque de queda", "Estado de emergencia",

    # 🏛️ Crisis de gobierno
    "renuncia", "destitución", "impeachment", "vacancia",

    # 📢 Movilización masiva
    "marcha nacional", "paro nacional", "bloqueo de carreteras",
]

# ── Palabras clave de monitoreo general ─────────────────────────────────────

TWITTER_KEYWORDS = [
    # 👤 Actores clave
    "Asfura", "Zambrano", "Mel Zelaya", "Nasralla", "Libre",
    "Partido Nacional", "Liberal", "Emilio Hernandez Hercules",
    "Rixi", "Octavio Pineda",

    # 🏛️ Instituciones
    "Congreso", "gobierno", "Ministerio", "Secretaría",
    "Ministerio Público", "TSC", "CNE", "ENEE", "Finanzas",
    "911", "ICF", "portuaria",

    # ⚖️ Actos de gobierno
    "decreto", "ley", "reforma", "presupuesto", "licitación",
    "contrato", "auditoría", "resolución", "aprobó", "vetó",

    # 🔥 Temas de conflicto político
    "corrupción", "fraude", "impunidad", "acusado", "detenido",
    "capturado", "investigado", "juicio", "condena", "escándalo",

    # 📢 Política general
    "elecciones", "diputado", "alcalde", "oposición", "oficialismo",
    "campaña", "voto", "protesta", "manifestación",

    # 🌎 Contexto relevante
    "Honduras", "Tegucigalpa", "San Pedro Sula",

    # ➕ Adicionales para mejor cobertura
    "FFAA", "Fuerzas Armadas", "lempira", "dólar", "economía",
    "coalición", "inversión", "narcotráfico", "extradición",
    "seguridad", "fiscal", "deuda", "ATIC", "FUSINA",
]

# ── Rutas y configuración general ───────────────────────────────────────────

import os

_GHA       = os.environ.get("GITHUB_ACTIONS") == "true"
_WORKSPACE = os.environ.get("GITHUB_WORKSPACE", "")

if _GHA:
    BASE_DIR    = _WORKSPACE
    REPORTS_DIR = os.path.join(_WORKSPACE, "reportes")
    DB_PATH     = os.path.join(_WORKSPACE, "sentinela.db")
    ENV_PATH    = os.path.join(_WORKSPACE, ".env")
    LOG_PATH    = os.path.join(_WORKSPACE, "sentinela.log")
else:
    BASE_DIR    = os.path.expanduser("~/social_monitor/centinela_v2")
    REPORTS_DIR = os.path.expanduser("~/social_monitor/reportes")
    DB_PATH     = os.path.join(BASE_DIR, "sentinela.db")
    ENV_PATH    = os.path.expanduser("~/social_monitor/.env")
    LOG_PATH    = os.path.join(BASE_DIR, "sentinela.log")

REPORT_EMAIL = [
    "cristian.cousin@gmail.com",
    "max.gonzaleshn@gmail.com",
]
SENDER_NAME  = "🛡️ CENTINELA"

# Horario de recolección (horas de inicio)
COLLECT_HOURS = [4, 6, 8, 10, 12, 14, 16, 18, 20]

# Máximo de tweets por perfil por ciclo
MAX_TWEETS_PER_PROFILE = 10

# Máximo de items RSS por feed
MAX_RSS_ITEMS = 15
