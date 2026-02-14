import telebot
import sqlite3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8037000962:AAHlRWkhL3XAWWdWUZo7WeR0zUl3qQQWxAU"
ADMINS = [8334124528]  # add more admin ids
UPI_ID = "7043592870@nyes"

CHANNELS = ["https://t.me/piyush_a2z_tricks", "@ch2", "@ch3"]

bot = telebot.TeleBot(BOT_TOKEN)

# ===== DATABASE =====
conn = sqlite3.connect("shop.db", check_same_thread=False)
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

# ===== CHECK ADMIN =====
def is_admin(uid):
    return uid in ADMINS

# ===== CHECK JOIN =====
def joined(uid):
    for ch in CHANNELS:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status not in ["member","administrator","creator"]:
                return False
        except:
            return False
    return True

# ===== START + REFERRAL =====
@bot.message_handler(commands=['start'])
def start(msg):

    args = msg.text.split()

    if not joined(msg.from_user.id):
        kb = InlineKeyboardMarkup()
        for ch in CHANNELS:
            kb.add(InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch[1:]}"))
        kb.add(InlineKeyboardButton("✅ Verify", callback_data="verify"))

        bot.send_message(msg.chat.id,
        "🔒 Join all channels first:",
        reply_markup=kb)
        return

    # referral register
    cur.execute("SELECT * FROM users WHERE user_id=?",(msg.from_user.id,))
    if not cur.fetchone():

        ref = int(args[1]) if len(args)>1 else None

        if ref and ref != msg.from_user.id:
            cur.execute("UPDATE users SET wallet=wallet+10 WHERE user_id=?",(ref,))

        cur.execute(
        "INSERT INTO users (user_id,referrer) VALUES (?,?)",
        (msg.from_user.id,ref)
        )
        conn.commit()

    link = f"https://t.me/{bot.get_me().username}?start={msg.from_user.id}"

    bot.send_message(msg.chat.id,
    f"🔥 Welcome!\n\n👥 Referral link:\n{link}\nEarn ₹10 per join!")

# ===== VERIFY BUTTON =====
@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify(c):
    if joined(c.from_user.id):
        bot.edit_message_text("✅ Verified! Use /start",
        c.message.chat.id,
        c.message.message_id)
    else:
        bot.answer_callback_query(c.id,"❌ Join all first",show_alert=True)

# ===== WALLET =====
@bot.message_handler(commands=['wallet'])
def wallet(msg):
    cur.execute("SELECT wallet FROM users WHERE user_id=?",(msg.from_user.id,))
    w = cur.fetchone()
    bal = w[0] if w else 0

    bot.send_message(msg.chat.id,f"💰 Wallet: ₹{bal}")

# ===== COUPON USE =====
@bot.message_handler(commands=['use'])
def use_coupon(msg):
    code = msg.text.split()[1]

    cur.execute("SELECT amount FROM coupons WHERE code=?",(code,))
    c = cur.fetchone()

    if not c:
        bot.send_message(msg.chat.id,"❌ Invalid coupon")
        return

    cur.execute(
    "UPDATE users SET wallet=wallet+? WHERE user_id=?",
    (c[0],msg.from_user.id)
    )
    conn.commit()

    bot.send_message(msg.chat.id,f"✅ Coupon applied! +₹{c[0]}")

# ===== ADMIN COUPON CREATE =====
@bot.message_handler(commands=['coupon'])
def coupon(msg):
    if not is_admin(msg.from_user.id): return

    _, code, amt = msg.text.split()

    cur.execute(
    "INSERT OR REPLACE INTO coupons VALUES (?,?)",
    (code,int(amt))
    )
    conn.commit()

    bot.send_message(msg.chat.id,"✅ Coupon created")

# ===== BROADCAST =====
@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if not is_admin(msg.from_user.id): return

    text = msg.text.replace("/broadcast ","")

    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    for u in users:
        try: bot.send_message(u[0],text)
        except: pass

    bot.send_message(msg.chat.id,"✅ Broadcast done")

# ===== RUN =====
print("Ultimate upgrade running...")
bot.infinity_polling()
