import asyncio
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from scheduler import start_scheduler
from config import TELEGRAM_TOKEN, CHAT_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Bot Clipping Actif !*\n\n"
        "Commandes disponibles :\n"
        "/scan — Scanner maintenant les nouvelles vidéos\n"
        "/top — Top 5 vidéos des 7 derniers jours\n"
        "/createurs — Liste des créateurs surveillés\n"
        "/ajouter [URL chaîne] — Ajouter un créateur\n"
        "/stats — Statistiques du bot",
        parse_mode="Markdown"
    )

async def scan_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Scan en cours... je te notifie dès que j'ai des résultats !")
    from scraper import scan_all_creators
    await scan_all_creators(context.application.bot)

async def top_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from scraper import get_top_videos
    await get_top_videos(update, context)

async def list_creators(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from config import CREATORS
    msg = "👥 *Créateurs surveillés :*\n\n"
    for c in CREATORS:
        msg += f"• {c['name']} (`{c['channel_id']}`)\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import json, os
    seen = []
    if os.path.exists("seen_videos.json"):
        with open("seen_videos.json") as f:
            seen = json.load(f)
    await update.message.reply_text(
        f"📊 *Stats du bot :*\n\n"
        f"🎬 Vidéos analysées : {len(seen)}\n"
        f"⏰ Scan automatique : toutes les 6h\n"
        f"👤 Créateurs : 2 (Tony Robbins, Charlie Kirk)",
        parse_mode="Markdown"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_now))
    app.add_handler(CommandHandler("top", top_videos))
    app.add_handler(CommandHandler("createurs", list_creators))
    app.add_handler(CommandHandler("stats", stats))

    # Démarrer le scheduler (scan toutes les 6h)
    start_scheduler(app.bot)

    logger.info("✅ Bot démarré !")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
