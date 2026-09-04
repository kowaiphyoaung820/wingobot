import os
import threading
import asyncio
import random
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

# Render Port Binding Dummy Server
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Bot Config
TELEGRAM_BOT_TOKEN = "8673352691:AAFyMGC_P-bdELP6ivJqOU8AHHlxbYFj4xY"

active_chats = set()
current_bet_multiplier = 1
last_pred = None
last_match = None

async def auto_prediction_worker(app: Application):
    global current_bet_multiplier, last_pred, last_match
    
    while True:
        try:
            if active_chats:
                now = datetime.now()
                seconds_today = now.hour * 3600 + now.minute * 60 + now.second
                period_index = (seconds_today // 30) + 1
                current_match = f"{now.strftime('%Y%m%d')}10005{period_index:04d}"
                
                if current_match != last_match:
                    next_pred = random.choice(["𝘽𝙄𝙂", "𝙎𝙈𝘼𝙇𝙇"])
                    
                    # Syntax Error များကို ပြင်ဆင်ထားသော Format
                    msg = (
                        f"⚡ **🎯 𝙒𝙄𝙉𝙂𝙊 𝟯𝟬𝙎 𝙋𝙍𝙀𝘿𝙄𝘾𝙏𝙄𝙊𝙉 🔮** ⚡\n\n"
                        f"🎯 𝐌𝐀𝐓𝐂𝐇  ;  `{current_match}`\n"
                        f"📍 𝐁𝐔𝐘        ;  **{next_pred}**\n"
                        f"💵 𝐁𝐄𝐓        ;  **{current_bet_multiplier} x**"
                    )
                    
                    for chat_id in list(active_chats):
                        try:
                            await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                        except Exception as err:
                            print(f"Send Error ({chat_id}): {err}")
                            
                    last_pred = next_pred
                    last_match = current_match

        except Exception as e:
            print(f"Worker Error: {e}")
            
        await asyncio.sleep(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    
    welcome_msg = (
        "မင်္ဂလာပါ 🤖𝘾𝙆 𝘽𝙊𝙏🤖မှကြိုဆိုပါတယ်\n\n"
        "🎯 𝙒𝙞𝙣𝙂𝙤 30 𝙎𝙚𝙘𝙤𝙣𝙙𝙨 ⏱️ စတင်ပါပြီ"
    )
    await update.message.reply_text(welcome_msg)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_chats:
        active_chats.remove(chat_id)
    await update.message.reply_text("⛔⚡ 𝘾𝙆 𝘽𝙊𝙏 ရပ်တန့်လိုက်ပါပြီ 🔒🚫။")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    
    async def post_init(application: Application):
        commands = [
            BotCommand("start", "Start predictor"),
            BotCommand("stop", "Stop predictor")
        ]
        await application.bot.set_my_commands(commands)
        asyncio.create_task(auto_prediction_worker(application))
        
    app.post_init = post_init
    app.run_polling()

if __name__ == "__main__":
    main()
    
