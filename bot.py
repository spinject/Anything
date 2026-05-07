import telebot
from telebot import types
import sqlite3
import os

# --- CONFIGURATION ---
# We use 'os.getenv' so your token is hidden and safe
TOKEN = os.getenv('BOT_TOKEN') 
ADMIN_ID = int(os.getenv('ADMIN_ID')) 

bot = telebot.TeleBot(TOKEN)

# --- DATABASE SETUP ---
def get_db():
    # Note: On Render's free tier, the database resets when the bot restarts.
    conn = sqlite3.connect('store.db', check_same_thread=False)
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

# --- ADMIN PANEL ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Panel")
def admin_panel(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [
        types.InlineKeyboardButton("📊 Stats", callback_data="stats"),
        types.InlineKeyboardButton("📦 Orders", callback_data="orders"),
        types.InlineKeyboardButton("✅ Mark Done", callback_data="done"),
        types.InlineKeyboardButton("👤 Check User", callback_data="check"),
        types.InlineKeyboardButton("💰 Add Bal", callback_data="add"),
        types.InlineKeyboardButton("💸 Deduct Bal", callback_data="sub"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="bc")
    ]
    markup.add(*btns)
    bot.send_message(message.chat.id, "🛠 **Admin Control Panel**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "stats":
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        bot.answer_callback_query(call.id, f"Total Users: {count}", show_alert=True)
    # Add other logics here as needed

if __name__ == "__main__":
    print("Bot is starting on Render...")
    bot.infinity_polling()
