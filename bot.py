import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

TOKEN = "8037000962:AAHlRWkhL3XAWWdWUZo7WeR0zUl3qQQWxAU"
ADMIN_ID = 8334124528
CHANNEL = "@bkc_zone1312"
UPI = "7043592870@nyes"

bot = telebot.TeleBot(TOKEN)

# ===== DATABASE =====
conn = sqlite3.connect("ultra_shop.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS stock(
product TEXT,
account TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
user_id INTEGER,
product TEXT,
utr TEXT,
status TEXT
)
""")

conn.commit()

prices = {
    "fresh": 50,
    "number": 80,
    "old": 120
}

waiting_payment = {}

# ===== JOIN CHECK =====
def joined(uid):
    try:
        m = bot.get_chat_member(CHANNEL, uid)
        return m.status in ["member","administrator","creator"]
    except:
        return False

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📢 Join Channel", url="https://t.me/bkc_zone1312"),
        InlineKeyboardButton("✅ Verify", callback_data="verify")
    )

    bot.send_message(
        msg.chat.id,
        "🔥 WELCOME TO ULTRA SHOP BOT 🔥\n\nJoin channel & verify to continue ✅",
        reply_markup=kb
    )

# ===== VERIFY =====
@bot.callback_query_handler(func=lambda c: c.data=="verify")
def verify(c):

    if not joined(c.from_user.id):
        bot.answer_callback_query(c.id,"❌ Join channel first!",show_alert=True)
        return

    menu = InlineKeyboardMarkup(row_width=2)
    menu.add(
        InlineKeyboardButton("🆕 Fresh ₹50", callback_data="buy_fresh"),
        InlineKeyboardButton("📱 Number ₹80", callback_data="buy_number"),
        InlineKeyboardButton("♻️ Old ₹120", callback_data="buy_old"),
    )
    menu.add(
        InlineKeyboardButton("🆘 Help", callback_data="help"),
        InlineKeyboardButton("☎️ Support", url="https://t.me/bkc_zone1312")
    )

    bot.edit_message_text(
        "✅ VERIFIED!\n\n💰 Select account type 👇",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=menu
    )

# ===== BUY =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy(c):

    product = c.data.split("_")[1]
    waiting_payment[c.from_user.id] = product

    bot.send_message(
        c.message.chat.id,
        f"💳 Pay ₹{prices[product]} to:\n\nUPI: {UPI}\n\nSend screenshot + UTR 👇"
    )

# ===== SCREENSHOT =====
@bot.message_handler(content_types=['photo'])
def photo(msg):

    if msg.from_user.id not in waiting_payment:
        return

    bot.reply_to(msg,"✅ Screenshot received\nNow send UTR number")

# ===== UTR =====
@bot.message_handler(func=lambda m: m.from_user.id in waiting_payment)
def utr(msg):

    uid = msg.from_user.id
    product = waiting_payment.pop(uid)

    cur.execute(
        "INSERT INTO orders VALUES (?,?,?,?)",
        (uid, product, msg.text, "pending")
    )
    conn.commit()

    text = f"""
🛒 NEW ORDER

User ID: {uid}
Product: {product}
UTR: {msg.text}
"""

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"ok_{uid}_{product}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"no_{uid}")
    )

    bot.send_message(ADMIN_ID, text, reply_markup=kb)
    bot.reply_to(msg,"⏳ Waiting admin approval...")

# ===== APPROVE =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_"))
def approve(c):

    if c.from_user.id != ADMIN_ID:
        return

    _, uid, product = c.data.split("_")
    uid = int(uid)

    cur.execute("SELECT account FROM stock WHERE product=? LIMIT 1", (product,))
    item = cur.fetchone()

    if not item:
        bot.answer_callback_query(c.id,"❌ Out of stock!",show_alert=True)
        return

    account = item[0]

    cur.execute("DELETE FROM stock WHERE account=?", (account,))
    cur.execute(
        "UPDATE orders SET status='approved' WHERE user_id=? AND status='pending'",
        (uid,)
    )
    conn.commit()

    bot.send_message(
        uid,
        f"✅ Payment approved!\n\n🎁 Your account:\n{account}"
    )

    bot.edit_message_text("✅ Delivered",c.message.chat.id,c.message.message_id)

# ===== REJECT =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("no_"))
def reject(c):

    if c.from_user.id != ADMIN_ID:
        return

    uid = int(c.data.split("_")[1])

    bot.send_message(uid,"❌ Payment rejected")
    bot.edit_message_text("❌ Rejected",c.message.chat.id,c.message.message_id)

# ===== ADMIN COMMANDS =====

@bot.message_handler(commands=['addstock'])
def addstock(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    try:
        _, product, account = msg.text.split(" ",2)
        cur.execute("INSERT INTO stock VALUES (?,?)",(product,account))
        conn.commit()
        bot.reply_to(msg,"✅ Stock added")
    except:
        bot.reply_to(msg,"Use:\n/addstock fresh email:pass")

@bot.message_handler(commands=['stock'])
def stock(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    text = "📦 Stock:\n"

    for p in prices:
        cur.execute("SELECT COUNT(*) FROM stock WHERE product=?", (p,))
        count = cur.fetchone()[0]
        text += f"{p}: {count}\n"

    bot.reply_to(msg,text)

@bot.message_handler(commands=['orders'])
def orders(msg):

    if msg.from_user.id != ADMIN_ID:
        return

    cur.execute("SELECT * FROM orders ORDER BY rowid DESC LIMIT 10")
    rows = cur.fetchall()

    text = "🧾 Orders:\n\n"
    for r in rows:
        text += f"User {r[0]} → {r[1]} ({r[3]})\n"

    bot.reply_to(msg,text)

print("ULTRA SHOP BOT RUNNING 🚀")
bot.infinity_polling()
