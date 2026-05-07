import telebot
from telebot import types
import sqlite3
import os

# --- CONFIGURATION ---
# On Koyeb, we set these in the "Environment Variables" settings
TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_ID = int(os.getenv('ADMIN_ID')) 

bot = telebot.TeleBot(TOKEN)

# --- DATABASE ---
def get_db():
    # SQLite works fine on Koyeb, but note: files reset on redeploy
    conn = sqlite3.connect('store_data.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)''')
    conn.commit()

init_db()

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛍️ Shop", "💰 Wallet")
    markup.add("📦 My Orders", "🎁 Refer & Earn")
    if user_id == ADMIN_ID:
        markup.add("⚙️ Admin Panel")
    
    bot.send_message(message.chat.id, "👋 **Welcome to Flassy Mods Store!**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [
        types.InlineKeyboardButton("📊 Stats", callback_data="stats"),
        types.InlineKeyboardButton("👤 Check User", callback_data="check_user"),
        types.InlineKeyboardButton("💰 Add Bal", callback_data="add_bal"),
        types.InlineKeyboardButton("💸 Deduct Bal", callback_data="deduct_bal"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="bc")
    ]
    markup.add(*btns)
    bot.send_message(message.chat.id, "🛠 **Admin Control Panel**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "stats":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        bot.answer_callback_query(call.id, f"Total Users: {total}", show_alert=True)
    
    elif call.data == "add_bal":
        msg = bot.send_message(call.message.chat.id, "💰 Send: `UserID Amount` (e.g. 12345 500)")
        bot.register_next_step_handler(msg, process_balance, "add")

def process_balance(message, mode):
    try:
        uid, amt = message.text.split()
        conn = get_db()
        cursor = conn.cursor()
        if mode == "add":
            cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (int(amt), int(uid)))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Success!")
    except:
        bot.send_message(message.chat.id, "❌ Error. Use correct format.")

# Run
if __name__ == "__main__":
    print("Bot is running on Koyeb...")
    bot.infinity_polling()
