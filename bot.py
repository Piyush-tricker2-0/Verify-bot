import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== CONFIG =====
BOT_TOKEN = "8037000962:AAHlRWkhL3XAWWdWUZo7WeR0zUl3qQQWxAU"
ADMINS = [8334124528]  # apna telegram user id daalo
CHANNELS = ["@piyush_a2z_tricks", "@channel2", "@channel3"]

bot = telebot.TeleBot(BOT_TOKEN)

# ===== DATABASE =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
referrer INTEGER,
wallet INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS coupons (
code TEXT PRIMARY KEY,
amount INTEGER
)
""")

conn.commit()

# ===== ADMIN CHECK =====
def is_admin(uid):
    return uid in ADMINS

# ===== JOIN CHECK =====
def joined(uid):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, uid)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ===== JOIN MENU =====
def join_menu():
    kb = InlineKeyboardMarkup()
    for ch in CHANNELS:
        kb.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch[1:]}"))
    kb.add(InlineKeyboardButton("✅ Verify", callback_data="verify"))
    return kb

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):

    if not joined(msg.from_user.id):
        bot.send_message(
            msg.chat.id,
            "🔒 Bot use karne ke liye sab channel join karo:",
            reply_markup=join_menu()
        )
        return

    args = msg.text.split()

    ref = None
    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = None

    cur.execute("SELECT * FROM users WHERE user_id=?", (msg.from_user.id,))
    if not cur.fetchone():

        if ref and ref != msg.from_user.id:
            cur.execute(
                "UPDATE users SET wallet=wallet+10 WHERE user_id=?",
                (ref,)
            )

        cur.execute(
            "INSERT INTO users (user_id, referrer) VALUES (?, ?)",
            (msg.from_user.id, ref)
        )
        conn.commit()

    link = f"https://t.me/{bot.get_me().username}?start={msg.from_user.id}"

    bot.send_message(
        msg.chat.id,
        f"🔥 Welcome!\n\n👥 Referral link:\n{link}\nEarn ₹10 per join!"
    )

# ===== VERIFY BUTTON =====
@bot.callback_query_handler(func=lambda c: c.data == "verify")
def verify(c):
    if joined(c.from_user.id):
        bot.edit_message_text(
            "✅ Verified! Ab /start dabao",
            c.message.chat.id,
            c.message.message_id
        )
    else:
        bot.answer_callback_query(
            c.id,
            "❌ Pehle sab channel join karo",
            show_alert=True
        )

# ===== WALLET =====
@bot.message_handler(commands=['wallet'])
def wallet(msg):

    cur.execute(
        "SELECT wallet FROM users WHERE user_id=?",
        (msg.from_user.id,)
    )

    w = cur.fetchone()
    balance = w[0] if w else 0

    bot.send_message(msg.chat.id, f"💰 Wallet Balance: ₹{balance}")

# ===== COUPON USE =====
@bot.message_handler(commands=['use'])
def use_coupon(msg):

    parts = msg.text.split()

    if len(parts) < 2:
        bot.send_message(msg.chat.id, "Use: /use CODE")
        return

    code = parts[1]

    cur.execute("SELECT amount FROM coupons WHERE code=?", (code,))
    c = cur.fetchone()

    if not c:
        bot.send_message(msg.chat.id, "❌ Invalid coupon")
        return

    cur.execute(
        "UPDATE users SET wallet=wallet+? WHERE user_id=?",
        (c[0], msg.from_user.id)
    )

    conn.commit()

    bot.send_message(msg.chat.id, f"✅ Coupon applied! +₹{c[0]}")

# ===== ADMIN COUPON CREATE =====
@bot.message_handler(commands=['coupon'])
def coupon(msg):

    if not is_admin(msg.from_user.id):
        return

    parts = msg.text.split()

    if len(parts) < 3:
        bot.send_message(msg.chat.id, "Use: /coupon CODE AMOUNT")
        return

    code = parts[1]

    try:
        amount = int(parts[2])
    except:
        bot.send_message(msg.chat.id, "Amount number hona chahiye")
        return

    cur.execute(
        "INSERT OR REPLACE INTO coupons VALUES (?, ?)",
        (code, amount)
    )

    conn.commit()

    bot.send_message(msg.chat.id, "✅ Coupon created")

# ===== BROADCAST =====
@bot.message_handler(commands=['broadcast'])
def broadcast(msg):

    if not is_admin(msg.from_user.id):
        return

    text = msg.text.replace("/broadcast ", "")

    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    sent = 0

    for u in users:
        try:
            bot.send_message(u[0], text)
            sent += 1
        except:
            pass

    bot.send_message(msg.chat.id, f"✅ Broadcast sent: {sent}")

# ===== RUN =====
print("Bot running successfully...")
bot.infinity_polling()
