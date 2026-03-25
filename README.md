# 🎬 Bot Clipping Telegram

Bot qui surveille automatiquement Tony Robbins & Charlie Kirk sur YouTube,
score les vidéos et t'envoie des notifications avec les meilleurs moments à clipper.

---

## ⚡ Setup en 5 étapes

### 1. Créer ton Bot Telegram
1. Ouvre Telegram → cherche `@BotFather`
2. Envoie `/newbot` → donne un nom → récupère le **TOKEN**
3. Pour ton CHAT_ID : parle à `@userinfobot` → il te donne ton ID

### 2. Créer une clé YouTube API (gratuit)
1. Va sur https://console.cloud.google.com
2. Crée un projet → "APIs & Services" → "Enable APIs"
3. Cherche "YouTube Data API v3" → Active-la
4. "Credentials" → "Create Credentials" → "API Key"
5. Copie la clé

### 3. Configurer les variables d'environnement
Crée un fichier `.env` à la racine :
```
TELEGRAM_TOKEN=ton_token_ici
CHAT_ID=ton_chat_id_ici
YOUTUBE_API_KEY=ta_cle_youtube_ici
```

### 4. Installer et lancer
```bash
pip install -r requirements.txt
python main.py
```

### 5. Déployer sur Render.com (gratuit)
1. Push le code sur GitHub
2. Va sur render.com → "New Web Service"
3. Connecte ton repo
4. Build command : `pip install -r requirements.txt`
5. Start command : `python main.py`
6. Ajoute les variables d'environnement dans "Environment"
7. Deploy !

---

## 📲 Commandes du bot

| Commande | Description |
|---|---|
| `/start` | Affiche l'aide |
| `/scan` | Lance un scan immédiat |
| `/top` | Top 5 vidéos de la semaine |
| `/createurs` | Liste des créateurs surveillés |
| `/stats` | Statistiques du bot |

---

## 📊 Système de score

| Critère | Points |
|---|---|
| Ratio likes/vues élevé | 0-40 pts |
| Vues rapides (< 48h) | 0-30 pts |
| Durée idéale (20-60 min) | 0-20 pts |
| Chapitres YouTube présents | 0-10 pts |

- **✅ PRÊT À POSTER** = Score ≥ 75% + chapitres présents
- **✂️ À ÉDITER** = Score ≥ 75% sans chapitres
- **👀 POTENTIEL MOYEN** = Score 50-75%

---

## ➕ Ajouter un créateur

Dans `config.py`, ajoute dans la liste `CREATORS` :
```python
{
    "name": "Nom du créateur",
    "channel_id": "UCxxxxxxxxxxxxxxx",  # ID de la chaîne YouTube
}
```

Pour trouver le channel_id : va sur la chaîne YouTube → clic droit → 
"Afficher la source de la page" → Ctrl+F → cherche "channelId"
