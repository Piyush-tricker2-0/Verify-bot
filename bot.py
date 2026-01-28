import logging, time, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = "8037000962:AAHlRWkhL3XAWWdWUZo7WeR0zUl3qQQWxAU"
ADMIN_ID = 8334124528

CHANNELS = [
    "@indiantechnical0m",
    "@piyush_chauhan_34"
]
# =========================================

logging.basicConfig(level=logging.INFO)

USERS = set()
ANTI_SPAM = {}

# ---------- FORCE JOIN CHECK --------------
async def joined_all(bot, user_id):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True

# ---------- ANTI SPAM ---------------------
def spam_check(uid):
    now = time.time()
    last = ANTI_SPAM.get(uid, 0)
    if now - last < 4:
        return False
    ANTI_SPAM[uid] = now
    return True

# ---------- START -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)

    if not spam_check(user.id):
        return

    if await joined_all(context.bot, user.id):
        keyboard = [
            [InlineKeyboardButton("🛠 Free Tools", callback_data="tools")],
            [InlineKeyboardButton("📢 Official Channel", url="https://t.me/indiantechnical0m")],
            [InlineKeyboardButton("📞 Support", url="https://t.me/piyush_chauhan_34")]
        ]
        await update.message.reply_text(
            f"✅ **Verification Complete**\n\n"
            f"Welcome {user.first_name} 😎🔥\n"
            f"Bot unlocked successfully.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        buttons = []
        for ch in CHANNELS:
            buttons.append(
                [InlineKeyboardButton("🔔 Join Channel", url=f"https://t.me/{ch.replace('@','')}")]
            )
        buttons.append([InlineKeyboardButton("✅ Verify", callback_data="verify")])

        await update.message.reply_text(
            "🚫 **Access Denied**\n\n"
            "Bot use karne ke liye pehle dono channel join karo 👇",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )

# ---------- VERIFY ------------------------
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    user = q.from_user
    USERS.add(user.id)

    if await joined_all(context.bot, user.id):
        await q.answer("Verified Successfully ✅", show_alert=True)
        await q.edit_message_text(
            "🎉 **Verification Successful!**\n\nAb bot use kar sakte ho 😎🔥",
            parse_mode="Markdown"
        )
    else:
        await q.answer("❌ Pehle dono channel join karo", show_alert=True)

# ---------- TOOLS -------------------------
async def tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await joined_all(context.bot, user.id):
        await update.message.reply_text("❌ Channel join compulsory hai")
        return

    await update.message.reply_text(
        "🛠 **Free Tools Menu**\n\n"
        "🔥 Instagram Downloader\n"
        "🚀 YouTube Tools\n"
        "⚡ Telegram Tricks\n\n"
        "More coming soon...",
        parse_mode="Markdown"
    )

# ---------- ADMIN BROADCAST ---------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage:\n/broadcast Your message")
        return

    msg = " ".join(context.args)
    sent, failed = 0, 0

    for uid in list(USERS):
        try:
            await context.bot.send_message(uid, msg)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    await update.message.reply_text(
        f"📢 **Broadcast Complete**\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

# ---------- MAIN --------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(tools, pattern="tools"))

    app.run_polling()

if __name__ == "__main__":
    main()
