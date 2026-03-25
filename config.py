import os

# ================================================
# 🔑 TOKENS — Remplace par tes vraies valeurs
# ================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "TON_TOKEN_TELEGRAM_ICI")
CHAT_ID = os.getenv("CHAT_ID", "TON_CHAT_ID_ICI")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "TA_CLE_YOUTUBE_ICI")

# ================================================
# 👥 CRÉATEURS À SURVEILLER
# Pour trouver le channel_id : va sur la chaîne YouTube
# → clic droit → "Afficher la source" → cherche "channelId"
# ================================================
CREATORS = [
    {
        "name": "Tony Robbins",
        "channel_id": "UCkMSB7GC_0PCBM8EX3bwfkw",  # Chaîne officielle
    },
    {
        "name": "Charlie Kirk",
        "channel_id": "UCo-3ThNQmPmQSQL_L8oj6Lg",  # TPUSA / Charlie Kirk
    },
]

# ================================================
# ⚙️ PARAMÈTRES DE SCAN
# ================================================
MIN_DURATION_MINUTES = 15       # Vidéos minimum X minutes (clippables)
MAX_DURATION_MINUTES = 180      # Vidéos maximum X minutes
MIN_VIEWS = 5000                # Ignorer les vidéos avec trop peu de vues
SCAN_INTERVAL_HOURS = 6         # Scan toutes les X heures
MAX_RESULTS_PER_CREATOR = 10    # Nombre de vidéos à analyser par scan

# ================================================
# 📊 SEUILS DE SCORE
# ================================================
SCORE_PRET_A_POSTER = 75        # % minimum pour "Prêt à poster"
SCORE_A_EDITER = 50             # % minimum pour "À éditer"
