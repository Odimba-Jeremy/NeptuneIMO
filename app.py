import os
import aiohttp
import asyncio
import subprocess
import tempfile
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ======================
# 🔥 CONFIGURATION DIRECTE
# ======================

# 🔹 Ton token Telegram (copie-colle ici)
BOT_TOKEN = "7916059127:AAFE0LEPTh9mL_ewIrDj5PxxvJ2rK1Jg6gU"

# 🔹 Ta clé API AdFly (optionnelle)
ADFLY_API_KEY = "CD0E4AC7A5B98571FB72C19F48BA928A446F40D8"

# ======================
# 🔧 AUTRES CONFIGURATIONS
# ======================

# 🔹 Dossier temporaire pour les vidéos
DOWNLOAD_DIR = Path(tempfile.mkdtemp(prefix="video_downloads_"))
DOWNLOAD_DIR.mkdir(exist_ok=True)

# 🔹 Domaines autorisés
ALLOWED_DOMAINS = [
    "tiktok.com", "vm.tiktok.com", "vt.tiktok.com",
    "instagram.com", "www.instagram.com",
    "facebook.com", "fb.watch", "www.facebook.com",
    "youtube.com", "youtu.be", "www.youtube.com",
    "twitter.com", "x.com", "www.twitter.com",
    "reddit.com", "www.reddit.com",
    "twitch.tv", "www.twitch.tv",
    "dailymotion.com", "www.dailymotion.com",
    "vimeo.com", "www.vimeo.com"
]

# 🔹 Stockage simple des utilisateurs en attente
waiting_users = {}
user_links = {}

# ======================
# 🔗 API AdFly Cloud
# ======================

async def shorten_adfly(url: str, user_id: int) -> str:
    """Raccourcit une URL avec l'API AdFly Cloud"""
    try:
        # Générer un alias unique
        import time
        import hashlib
        alias_hash = hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()[:8]
        alias = f"user{user_id}_{alias_hash}"
        
        # Construire l'URL API
        api_url = f"https://adfly.cloud/api?api={ADFLY_API_KEY}&url={url}&alias={alias}"
        
        # Faire la requête
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    # Selon la documentation AdFly, la réponse peut varier
                    if isinstance(result, dict):
                        if "shortenedUrl" in result:
                            return result["shortenedUrl"]
                        elif "url" in result:
                            return result["url"]
                        elif "short_url" in result:
                            return result["short_url"]
                    elif isinstance(result, str) and result.startswith("http"):
                        return result
                    
                    # Fallback
                    return f"https://adfly.cloud/{alias}"
                else:
                    print(f"Erreur API AdFly: {resp.status}")
                    return f"https://adfly.cloud/{alias}"
                    
    except Exception as e:
        print(f"Erreur lors du raccourcissement AdFly: {e}")
        return "https://adfly.cloud/6Ra1"

# ======================
# 🎯 COMMANDES TELEGRAM
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    welcome_text = f"""
👋 *Bienvenue {user.first_name} sur NeptuneKPTBot !* 🤖

✨ *Fonctionnalités :*
• 📥 Téléchargement vidéo depuis {len(ALLOWED_DOMAINS)} plateformes
• 🔗 Liens AdFly intégrés
• ⚡ Rapide et simple

📋 *Comment utiliser :*
1. Envoie un lien vidéo
2. Clique sur la publicité (5s)
3. Renvoie le même lien
4. Reçois ta vidéo !

🔧 *Commandes :*
/start - Ce message
/help - Aide détaillée
/sites - Sites supportés
"""
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🆘 *Centre d'aide*

📥 *Processus :*
1. Envoie un lien vidéo
2. Je génère un lien AdFly unique
3. Tu cliques et attends 5 secondes
4. Tu renvoies le lien original
5. Je t'envoie la vidéo

⚠️ *Problèmes fréquents :*
• Lien non supporté : Vérifie /sites
• Vidéo >50MB : Limite Telegram
• Erreur : Réessaie dans 1 minute
"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def sites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sites_text = "🌐 *Plateformes supportées :*\n\n"
    
    for domain in ALLOWED_DOMAINS:
        sites_text += f"• {domain}\n"
    
    sites_text += "\n⚠️ Tous ces liens seront raccourcis via AdFly Cloud."
    
    await update.message.reply_text(sites_text, parse_mode="Markdown")

# ======================
# 🔗 GESTION DES LIENS
# ======================

def is_supported_domain(url: str) -> bool:
    """Vérifie si l'URL vient d'un domaine supporté"""
    try:
        domain = url.split('/')[2].lower()
        return any(allowed_domain in domain for allowed_domain in ALLOWED_DOMAINS)
    except:
        return False

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Envoie un lien valide (http:// ou https://)")
        return
    
    if not is_supported_domain(url):
        await update.message.reply_text("❌ Domaine non supporté. Tape /sites")
        return
    
    user_id = user.id
    
    if user_id in waiting_users and waiting_users[user_id] == url:
        # L'utilisateur renvoie le lien après avoir cliqué
        del waiting_users[user_id]
        await process_video_download(update, url, user)
    else:
        # Premier envoi : générer lien AdFly
        waiting_users[user_id] = url
        
        wait_msg = await update.message.reply_text("⏳ Génération du lien AdFly...", parse_mode="Markdown")
        
        try:
            adfly_url = await shorten_adfly(url, user_id)
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Cliquer pour débloquer (5 secondes)", url=adfly_url)]
            ])
            
            await wait_msg.edit_text(
                f"🔗 *Lien AdFly unique généré !*\n\n"
                f"📌 *Lien original :*\n`{url}`\n\n"
                f"💰 *Lien AdFly (clique ici) :*\n{adfly_url}\n\n"
                f"📋 *Instructions :*\n"
                f"1. Clique sur le bouton\n2. Attend 5s\n3. Clique 'Continuer'\n4. Renvoie ce lien :\n`{url}`\n\n"
                f"💡 Cette pub finance le bot gratuitement.",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            
            user_links[user_id] = url
            
        except Exception as e:
            await wait_msg.edit_text("❌ Erreur génération lien. Réessaie.", parse_mode="Markdown")
            print(f"Erreur: {e}")

# ======================
# 📥 TÉLÉCHARGEMENT VIDÉO
# ======================

async def download_video_async(url: str, download_dir: Path) -> Path | None:
    """Téléchargement asynchrone de vidéo"""
    try:
        output_template = download_dir / "video_%(title)s_%(id)s.%(ext)s"
        
        yt_dlp_args = [
            "yt-dlp",
            "--no-warnings",
            "--quiet",
            "--format", "best[ext=mp4]/best",
            "--output", str(output_template),
            "--max-filesize", "50M",
            "--merge-output-format", "mp4",
            "--no-playlist",
            url
        ]
        
        process = await asyncio.create_subprocess_exec(
            *yt_dlp_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            print(f"Erreur yt-dlp: {stderr.decode()}")
            return None
        
        for file in download_dir.glob("*"):
            if file.is_file():
                return file
        
        return None
        
    except Exception as e:
        print(f"Erreur téléchargement: {e}")
        return None

async def process_video_download(update: Update, url: str, user):
    """Processus de téléchargement de la vidéo"""
    
    status_msg = await update.message.reply_text("⏳ Téléchargement en cours...", parse_mode="Markdown")
    
    try:
        video_path = await download_video_async(url, DOWNLOAD_DIR)
        
        if not video_path or not video_path.exists():
            await status_msg.edit_text("❌ Impossible de télécharger la vidéo. Vérifie le lien.")
            return
        
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 50:
            await status_msg.edit_text(f"⚠️ Vidéo trop lourde ({file_size_mb:.1f}MB). Limite: 50MB")
            video_path.unlink(missing_ok=True)
            return
        
        await status_msg.edit_text("📤 Envoi de la vidéo...", parse_mode="Markdown")
        
        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"✅ Téléchargement réussi !\n👤 Pour : {user.first_name}\n📏 Taille : {file_size_mb:.1f}MB\n💖 Merci pour votre soutien !",
                parse_mode="Markdown",
                supports_streaming=True
            )
        
        await status_msg.delete()
        
        user_id = user.id
        if user_id in user_links:
            del user_links[user_id]
        
    except Exception as e:
        await status_msg.edit_text("❌ Erreur téléchargement. Réessaie.", parse_mode="Markdown")
        print(f"Erreur: {e}")
    
    finally:
        cleanup_downloads(DOWNLOAD_DIR)

def cleanup_downloads(download_dir: Path):
    """Nettoie les fichiers temporaires"""
    try:
        for file in download_dir.glob("*"):
            if file.is_file():
                file.unlink(missing_ok=True)
    except:
        pass

# ======================
# 🚀 MAIN
# ======================

async def cleanup_old_data(context: ContextTypes.DEFAULT_TYPE):
    """Nettoie les données anciennes"""
    global waiting_users, user_links
    waiting_users = {}
    user_links = {}
    print("🧹 Nettoyage effectué")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les erreurs du bot"""
    print(f"Erreur: {context.error}")

def main():
    """Fonction principale"""
    # Créer l'application AVEC LE TOKEN DIRECT
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Ajouter les handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("sites", sites_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    # Gestion des erreurs
    application.add_error_handler(error_handler)
    
    # Tâches de fond
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(cleanup_old_data, interval=7200, first=10)
    
    # Démarrer le bot
    print("=" * 50)
    print("🤖 NeptuneKPTBot EN LIGNE !")
    print(f"🔑 Token intégré : {BOT_TOKEN[:10]}...")
    print(f"💰 AdFly API : {'Activée' if ADFLY_API_KEY else 'Désactivée'}")
    print(f"🌐 Domaines supportés : {len(ALLOWED_DOMAINS)}")
    print("=" * 50)
    
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()