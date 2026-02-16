import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8037000962:AAHlRWkhL3XAWWdWUZo7WeR0zUl3qQQWxAU"
ADMIN_ID = 8334124528  # apna telegram user id daalo
CHANNEL = "@bkc_zone1312"  # apna channel username daalo

bot = telebot.TeleBot(TOKEN)

users_payment = {}

# ✅ Check user joined or not
def check_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# ✅ Start command
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Verify Join", callback_data="verify"))
    markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL.replace('@','')}"))

    text = f"""
🔥 *WELCOME TO PREMIUM SELLING BOT* 🔥

👉 Bot use karne ke liye pehle channel join karo:

📢 {CHANNEL}

Join karne ke baad VERIFY pe click karo ✅
"""

    bot.send_message(msg.chat.id, text, reply_markup=markup, parse_mode="Markdown")


# ✅ Verify join
@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    user_id = call.from_user.id

    if check_join(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💰 Buy Account", callback_data="buy"))

        bot.edit_message_text(
            "✅ *Verification Successful!*\n\nAb bot use kar sakte ho 🚀",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Join channel first!",
            show_alert=True
        )


# ✅ Buy button
@bot.callback_query_handler(func=lambda call: call.data == "buy")
def buy(call):
    text = """
💳 *PAYMENT DETAILS*

UPI ID: `yourupi@upi`

Payment karne ke baad UTR bhejo 👇
"""
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")


# ✅ Receive UTR
@bot.message_handler(func=lambda m: True)
def receive_utr(msg):
    user_id = msg.from_user.id
    utr = msg.text

    users_payment[user_id] = utr

    admin_text = f"""
💰 *New Payment Request*

User: {msg.from_user.first_name}
ID: `{user_id}`
UTR: `{utr}`

Approve?
"""

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    )

    bot.send_message(ADMIN_ID, admin_text, reply_markup=markup, parse_mode="Markdown")

    bot.reply_to(msg, "⏳ Payment submitted! Admin verifying...")


# ✅ Approve payment
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve(call):
    user_id = int(call.data.split("_")[1])

    bot.send_message(
        user_id,
        "✅ *Payment Approved!*\n\n🎁 Your account:\nUSERNAME: demo\nPASSWORD: 1234",
        parse_mode="Markdown"
    )

    bot.edit_message_text("✅ Approved", call.message.chat.id, call.message.message_id)


# ✅ Reject payment
@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject(call):
    user_id = int(call.data.split("_")[1])

    bot.send_message(user_id, "❌ Payment Rejected. Contact support.")
    bot.edit_message_text("❌ Rejected", call.message.chat.id, call.message.message_id)


print("Bot running...")
bot.infinity_polling()
