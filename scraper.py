import json
import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
import isodate
from config import (
    YOUTUBE_API_KEY, CREATORS, CHAT_ID,
    MIN_DURATION_MINUTES, MAX_DURATION_MINUTES,
    MIN_VIEWS, MAX_RESULTS_PER_CREATOR,
    SCORE_PRET_A_POSTER, SCORE_A_EDITER
)

logger = logging.getLogger(__name__)
SEEN_FILE = "seen_videos.json"


# ================================================
# 💾 Gestion des vidéos déjà vues (évite doublons)
# ================================================
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return json.load(f)
    return []

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)


# ================================================
# 📊 Algorithme de scoring (0-100%)
# ================================================
def calculate_score(video):
    score = 0
    views = video.get("views", 0)
    likes = video.get("likes", 0)
    duration_min = video.get("duration_minutes", 0)
    has_chapters = video.get("has_chapters", False)
    published_hours_ago = video.get("published_hours_ago", 999)

    # 1. Ratio engagement likes/vues (40 pts)
    if views > 0:
        ratio = likes / views
        if ratio >= 0.08:
            score += 40
        elif ratio >= 0.05:
            score += 30
        elif ratio >= 0.03:
            score += 20
        elif ratio >= 0.01:
            score += 10

    # 2. Vitesse virale — vues dans les 48h (30 pts)
    if published_hours_ago <= 48:
        if views >= 500000:
            score += 30
        elif views >= 100000:
            score += 25
        elif views >= 50000:
            score += 18
        elif views >= 10000:
            score += 10
        elif views >= 5000:
            score += 5
    else:
        # Vidéo plus ancienne mais populaire
        if views >= 1000000:
            score += 20
        elif views >= 500000:
            score += 15
        elif views >= 100000:
            score += 10

    # 3. Durée idéale pour clipper (20 pts)
    if 20 <= duration_min <= 60:
        score += 20
    elif 15 <= duration_min <= 90:
        score += 15
    elif 10 <= duration_min <= 120:
        score += 10

    # 4. Chapitres YouTube présents = timestamps gratuits (10 pts)
    if has_chapters:
        score += 10

    return min(score, 100)


# ================================================
# 🏷️ Statut basé sur le score
# ================================================
def get_status(score, has_chapters):
    if score >= SCORE_PRET_A_POSTER and has_chapters:
        return "✅ PRÊT À POSTER"
    elif score >= SCORE_PRET_A_POSTER:
        return "✂️ À ÉDITER"
    elif score >= SCORE_A_EDITER:
        return "👀 POTENTIEL MOYEN"
    else:
        return None  # Skip


# ================================================
# 📺 Récupérer les vidéos d'un créateur via YouTube API
# ================================================
def fetch_creator_videos(channel_id, creator_name):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    # Chercher les vidéos récentes de la chaîne
    published_after = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    search_response = youtube.search().list(
        channelId=channel_id,
        part="id,snippet",
        order="date",
        type="video",
        publishedAfter=published_after,
        maxResults=MAX_RESULTS_PER_CREATOR
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

    if not video_ids:
        logger.info(f"Aucune nouvelle vidéo pour {creator_name}")
        return []

    # Récupérer les stats détaillées
    stats_response = youtube.videos().list(
        part="statistics,contentDetails,snippet",
        id=",".join(video_ids)
    ).execute()

    videos = []
    for item in stats_response.get("items", []):
        try:
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            details = item["contentDetails"]

            # Durée
            duration = isodate.parse_duration(details["duration"])
            duration_min = duration.total_seconds() / 60

            # Filtrer par durée
            if not (MIN_DURATION_MINUTES <= duration_min <= MAX_DURATION_MINUTES):
                continue

            # Vues
            views = int(stats.get("viewCount", 0))
            if views < MIN_VIEWS:
                continue

            likes = int(stats.get("likeCount", 0))

            # Date de publication
            pub_date = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))
            hours_ago = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600

            # Chapitres (présents dans la description sous forme de timestamps)
            description = snippet.get("description", "")
            has_chapters = "0:00" in description or "00:00" in description

            # Extraire les chapitres si présents
            chapters = []
            if has_chapters:
                lines = description.split("\n")
                for line in lines:
                    import re
                    match = re.match(r"(\d+:\d+(?::\d+)?)\s*[-–—]?\s*(.+)", line.strip())
                    if match:
                        chapters.append({
                            "timestamp": match.group(1),
                            "title": match.group(2).strip()[:60]
                        })

            video = {
                "id": item["id"],
                "title": snippet["title"],
                "creator": creator_name,
                "url": f"https://youtube.com/watch?v={item['id']}",
                "views": views,
                "likes": likes,
                "duration_minutes": round(duration_min),
                "published_hours_ago": round(hours_ago),
                "has_chapters": bool(chapters),
                "chapters": chapters[:8],  # Max 8 chapitres
            }

            video["score"] = calculate_score(video)
            video["status"] = get_status(video["score"], video["has_chapters"])

            if video["status"]:  # Skip les vidéos sous le seuil
                videos.append(video)

        except Exception as e:
            logger.error(f"Erreur parsing vidéo: {e}")
            continue

    return videos


# ================================================
# 📲 Formater la notification Telegram
# ================================================
def format_notification(video):
    score = video["score"]
    score_bar = "🟩" * (score // 20) + "⬜" * (5 - score // 20)

    # Temps depuis publication
    hours = video["published_hours_ago"]
    if hours < 1:
        time_str = "Il y a moins d'1h 🔥"
    elif hours < 24:
        time_str = f"Il y a {round(hours)}h"
    else:
        time_str = f"Il y a {round(hours/24)}j"

    # Ratio engagement
    ratio = round((video["likes"] / video["views"]) * 100, 2) if video["views"] > 0 else 0

    msg = (
        f"🎬 *NOUVELLE VIDÉO DÉTECTÉE*\n"
        f"{'─' * 30}\n"
        f"👤 *{video['creator']}*\n"
        f"📹 {video['title'][:70]}{'...' if len(video['title']) > 70 else ''}\n"
        f"⏱️ {video['duration_minutes']} min  |  📅 {time_str}\n\n"
        f"📊 *Score clippabilité : {score}%*\n"
        f"{score_bar}\n"
        f"👁️ {video['views']:,} vues  |  👍 {video['likes']:,} likes\n"
        f"💬 Ratio engagement : {ratio}%\n\n"
        f"🏷️ Statut : *{video['status']}*\n"
    )

    # Ajouter les chapitres si présents
    if video["chapters"]:
        msg += f"\n✂️ *Moments à clipper :*\n"
        for ch in video["chapters"][:5]:
            msg += f"→ `{ch['timestamp']}` — {ch['title']}\n"

    msg += f"\n🔗 {video['url']}"
    return msg


# ================================================
# 🔄 Scan principal — tous les créateurs
# ================================================
async def scan_all_creators(bot):
    seen = load_seen()
    new_count = 0

    for creator in CREATORS:
        logger.info(f"Scan de {creator['name']}...")
        try:
            videos = fetch_creator_videos(creator["channel_id"], creator["name"])

            for video in videos:
                if video["id"] in seen:
                    continue  # Déjà envoyé

                # Envoyer la notification
                msg = format_notification(video)
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=msg,
                    parse_mode="Markdown"
                )
                seen.append(video["id"])
                new_count += 1
                await asyncio.sleep(1)  # Éviter le spam

        except Exception as e:
            logger.error(f"Erreur scan {creator['name']}: {e}")
            await bot.send_message(
                chat_id=CHAT_ID,
                text=f"⚠️ Erreur lors du scan de {creator['name']}: {str(e)}"
            )

    save_seen(seen)

    if new_count == 0:
        logger.info("Aucune nouvelle vidéo trouvée.")
    else:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"✅ Scan terminé — {new_count} nouvelle(s) vidéo(s) trouvée(s) !"
        )


# ================================================
# 🏆 Top vidéos des 7 derniers jours
# ================================================
async def get_top_videos(update, context):
    await update.message.reply_text("🔍 Recherche du top des vidéos...")

    all_videos = []
    for creator in CREATORS:
        try:
            videos = fetch_creator_videos(creator["channel_id"], creator["name"])
            all_videos.extend(videos)
        except Exception as e:
            logger.error(f"Erreur top vidéos: {e}")

    if not all_videos:
        await update.message.reply_text("Aucune vidéo trouvée pour cette période.")
        return

    # Trier par score
    top = sorted(all_videos, key=lambda x: x["score"], reverse=True)[:5]

    msg = "🏆 *TOP 5 VIDÉOS À CLIPPER (7 derniers jours)*\n\n"
    for i, v in enumerate(top, 1):
        msg += (
            f"*{i}. {v['creator']}* — Score {v['score']}%\n"
            f"📹 {v['title'][:55]}...\n"
            f"👁️ {v['views']:,} vues | {v['status']}\n"
            f"🔗 {v['url']}\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")
