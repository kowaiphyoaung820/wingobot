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
                # CK Lottery 17-Digit Period Format (YYYYMMDD10005XXXX)
                now = datetime.now()
                seconds_today = now.hour * 3600 + now.minute * 60 + now.second
                period_index = (seconds_today // 30) + 1
                current_match = f"{now.strftime('%Y%m%d')}10005{period_index:04d}"
                
                # စက္ကန့် ၃၀ တိုင်း Match အသစ်အတွက် ပို့ပေးမည်
                if current_match != last_match:
                    win_loss_msg = ""
                    
                    if last_pred and last_match:
                        # Simulation: Correct logic tracking
                        is_win = random.choice([True, False])
                        if is_win:
                            win_loss_msg = f"📊 **LAST RESULT**: ✅ **WIN**\n"
                            current_bet_multiplier = 1
                        else:
                            win_loss_msg = f"📊 **LAST RESULT**: ❌ **LOSS**\n"
                            current_bet_multiplier *= 3

                    next_pred = random.choice(["BIG", "SMALL"])
                    
                    msg = (
                        f"{win_loss_msg}"
                        f"🔥 **WIN GO 30S PREDICTION** 🔥\n\n"
                        f"🎯 **MATCH** : `{current_match}`\n"
                        f"📍 **BUY**   : **{next_pred}**\n"
                        f"💵 **BET**   : **{current_bet_multiplier} x**"
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
    await update.message.reply_text("✅ WinGo 30S Predictor စတင်ပါပြီ!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_chats:
        active_chats.remove(chat_id)
    await update.message.reply_text("⛔ Bot ရပ်တန့်လိုက်ပါပြီ။")

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
    
