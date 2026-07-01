import json
import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8912596894:AAFn-vCc6XlY7afG0OYW4gnnYkSRx4qHF-c"
ADMIN_ID = 7427410925
DATA_FILE = "movies.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pending_admin_state = {}


def load_movies():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_movies(movies):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Kino kodini yoki nomini yozing, men topib beraman.\n\nMasalan: 101  yoki  Titanik"
    )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Kechirasiz, faqat admin kino qo'sha oladi.")
        return

    file_id = update.message.video.file_id
    pending_admin_state[user_id] = {"file_id": file_id, "step": "wait_code"}
    await update.message.reply_text("Video qabul qilindi. Endi shu kino uchun KOD kiriting (masalan: 101):")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id == ADMIN_ID and user_id in pending_admin_state:
        state = pending_admin_state[user_id]

        if state["step"] == "wait_code":
            state["code"] = text
            state["step"] = "wait_name"
            await update.message.reply_text("Endi kino NOMINI kiriting:")
            return

        elif state["step"] == "wait_name":
            movies = load_movies()
            movies[state["code"]] = {"name": text, "file_id": state["file_id"]}
            save_movies(movies)
            await update.message.reply_text(f"Saqlandi! Kod: {state['code']} Nom: {text}")
            del pending_admin_state[user_id]
            return

    movies = load_movies()
    query = text.lower()

    if text in movies:
        movie = movies[text]
        await update.message.reply_video(movie["file_id"], caption=movie["name"])
        return

    results = [(code, m) for code, m in movies.items() if query in m["name"].lower()]

    if len(results) == 1:
        code, movie = results[0]
        await update.message.reply_video(movie["file_id"], caption=movie["name"])
    elif len(results) > 1:
        lines = [f"{code} - {m['name']}" for code, m in results[:15]]
        await update.message.reply_text("Bir nechta natija topildi, kodini yozing:\n\n" + "\n".join(lines))
    else:
        await update.message.reply_text("Bunday kino topilmadi.")


async def list_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    movies = load_movies()
    if not movies:
        await update.message.reply_text("Hozircha bazada kino yo'q.")
        return
    lines = [f"{code} - {m['name']}" for code, m in movies.items()]
    await update.message.reply_text("Kinolar ro'yxati:\n\n" + "\n".join(lines))


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_movies))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
