import os
import threading
import asyncio
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

# Render Port Binding အတွက် Dummy Server
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Telegram Bot Setup
TELEGRAM_BOT_TOKEN = "8673352691:AAFyMGC_P-bdELP6ivJqOU8AHHlxbYFj4xY"

active_chats = set()
current_bet_multiplier = 1
match_counter = 1000

async def auto_prediction_worker(app: Application):
    global current_bet_multiplier, match_counter
    while True:
        try:
            if active_chats:
                match_counter += 1
                raw_pred = random.choice(["BIG", "SMALL"])
                
                # Formula Result ပို့ပေးသည့် မက်ဆေ့ချ် Format
                msg = (
                    f"🔥 **WIN GO PREDICTION** 🔥\n\n"
                    f"🎯 **MATCH** : {match_counter}\n"
                    f"📍 **BUY**   : **{raw_pred}**\n"
                    f"💵 **BET**   : **{current_bet_multiplier} x**"
                )
                
                for chat_id in list(active_chats):
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                    except Exception as err:
                        print(f"Send Error ({chat_id}): {err}")
                        
        except Exception as e:
            print(f"Worker Exception: {e}")
            
        # စက္ကန့် ၃၀ တိုင်း မက်ဆေ့ချ် ပို့ပေးမည် (၁ မိနစ် လုပ်ချင်ပါက 60 ဟု ပြောင်းပါ)
        await asyncio.sleep(30)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    await update.message.reply_text("✅ VIP Prediction Bot စတင်ပါပြီ! Formula စာတွဲများ တက်လာပါတော့မည်။")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_chats:
        active_chats.remove(chat_id)
    await update.message.reply_text("⛔ Bot ကို ရပ်တန့်လိုက်ပါပြီ။")

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
    print("🤖 VIP Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()
