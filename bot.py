import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "8037000962:AAHlRWkhL3XAWWdWUZo7WeR0zUl3qQQWxAU"
ADMIN_ID = 8334124528  # Apni ID yahan daalein
LOG_CHANNEL_ID = -1312 # Notification channel ki ID

# Prices
PRICE_FB_NORMAL = 20
PRICE_FF_LEVEL8 = 30

# Database Setup
def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock (item_name TEXT PRIMARY KEY, count INTEGER DEFAULT 0)''')
    # Default Stock (sirf pehli baar ke liye)
    cursor.execute("INSERT OR IGNORE INTO stock VALUES ('fb_normal', 100), ('ff_level8', 50)")
    conn.commit()
    conn.close()

init_db()

# --- MAIN FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verification/Join Check (Simulated)
    keyboard = [
        [InlineKeyboardButton("✅ VERIFY & JOIN CHANNEL", url="https://t.me/YourChannelLink")],
        [InlineKeyboardButton("🚀 START SHOPPING", callback_data='main_menu')]
    ]
    await update.message.reply_text(
        "👋 Welcome! Pehle channel join karein aur verify karein.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query: await query.answer()

    keyboard = [
        [InlineKeyboardButton("🛒 FB New Fresh (₹20)", callback_data='buy_fb_normal')],
        [InlineKeyboardButton("🔥 FF Level 8 (₹30)", callback_data='buy_ff_level8')],
        [InlineKeyboardButton("💰 ADD BALANCE", callback_data='add_funds')],
        [InlineKeyboardButton("📦 CHECK STOCK", callback_data='check_stock')],
        [InlineKeyboardButton("📞 CONTACT ADMIN", url="https://t.me/YourAdminUsername")]
    ]
    
    msg = "🛍️ **WELCOME TO SELLER BOT**\n\nApna account select karein aur turant pay karein!"
    if query:
        await query.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    item = query.data.replace('buy_', '')
    
    price = PRICE_FB_NORMAL if item == 'fb_normal' else PRICE_FF_LEVEL8
    display_name = "FB Normal" if item == 'fb_normal' else "FF Level 8"

    # Database check for stock & balance
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM stock WHERE item_name=?", (item,))
    stock_count = cursor.fetchone()[0]

    if stock_count <= 0:
        await query.answer("❌ Out of Stock!", show_alert=True)
        return

    # Purchase Logic (Simple Admin Contact version as requested)
    await query.message.reply_text(
        f"✅ Aapne select kiya: {display_name}\n"
        f"💵 Price: ₹{price}\n\n"
        "Abhi direct payment ke liye Admin ko message karein aur screenshot bhejein!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📩 SEND SCREENSHOT", url="https://t.me/YourAdminUsername")]])
    )

    # Notification to Channel
    remaining = stock_count - 1
    cursor.execute("UPDATE stock SET count=? WHERE item_name=?", (remaining, item))
    conn.commit()
    
    notif_text = (
        f"🔥 **NEW SALE ALERT!** 🔥\n\n"
        f"👤 User: {query.from_user.first_name}\n"
        f"📦 Item: {display_name}\n"
        f"✅ Status: Success\n"
        f"📉 Remaining Stock: {remaining}\n\n"
        f"👉 Aap bhi kharido: @{context.bot.username}"
    )
    await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=notif_text, parse_mode="Markdown")
    conn.close()

# --- ADMIN PANEL ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID: return
    
    await update.message.reply_text(
        "⚙️ **ADMIN CONTROL PANEL**\n\n"
        "Use commands:\n"
        "/setstock fb_normal 100\n"
        "/setstock ff_level8 50",
        parse_mode="Markdown"
    )

async def set_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID: return
    # Usage: /setstock item count
    item = context.args[0]
    count = context.args[1]
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE stock SET count=? WHERE item_name=?", (count, item))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Stock Updated: {item} = {count}")

# --- APP RUNNER ---
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("setstock", set_stock))
    app.add_handler(CallbackQueryHandler(main_menu, pattern='main_menu'))
    app.add_handler(CallbackQueryHandler(handle_purchase, pattern='buy_'))
    
    print("Bot is LIVE...")
    app.run_polling()

if __name__ == '__main__':
    main()
  
