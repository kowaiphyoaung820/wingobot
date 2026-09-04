import os
import threading
import asyncio
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

# Render Free Tier Port Error မပြစေရန် Dummy HTTP Server ကို အရင်ဆုံး စတင်ခြင်း
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Bot Token & Configuration
TELEGRAM_BOT_TOKEN = "8673352691:AAFyMGC_P-bdELP6ivJqOU8AHHlxbYFj4xY"

active_chats = set()
last_processed_period = None
current_bet_multiplier = 1
history_results = {}

def fetch_history():
    try:
        url = "https://api.singaporepredict.com/api/wingo30"  # မိမိအသုံးပြုသော API URL ထည့်ရန်
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"API Error: {e}")
    return []

def calculate_prediction(history):
    if not history:
        return None
    latest = history[0]
    period = str(latest.get("issueNumber"))
    last_num = int(latest.get("number", 0))
    
    # Prediction Logic
    raw_pred = "BIG" if last_num >= 5 else "SMALL"
    next_period = str(int(period) + 1)
    
    return {
        "current_period": period,
        "next_period": next_period,
        "raw_pred": raw_pred,
        "last_num": last_num
    }

async def auto_prediction_worker(app: Application):
    global last_processed_period, current_bet_multiplier
    while True:
        try:
            if active_chats:
                history = await asyncio.to_thread(fetch_history)
                if history:
                    latest_period = str(history[0].get("issueNumber"))
                    
                    if latest_period != last_processed_period:
                        res = calculate_prediction(history)
                        if res:
                            last_num = int(res["last_num"])
                            last_bs = "BIG" if last_num >= 5 else "SMALL"
                            
                            if res["current_period"] in history_results:
                                prev_pred = history_results[res["current_period"]]
                                if prev_pred == last_bs:
                                    current_bet_multiplier = 1
                                else:
                                    current_bet_multiplier *= 3
                            
                            history_results[res["next_period"]] = res["raw_pred"]
                            
                            msg = (
                                f"🔥 **WIN GO 30S** 🔥\n\n"
                                f"🎯 **MATCH** : {res['next_period'][-3:]}\n"
                                f"📍 **BUY**   : **{res['raw_pred']}**\n"
                                f"💵 **BET**   : **{current_bet_multiplier} x**"
                            )
                            
                            for chat_id in list(active_chats):
                                try:
                                    await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                                except Exception as err:
                                    print(f"Send Error ({chat_id}): {err}")
                            
                            last_processed_period = latest_period
        except Exception as e:
            print(f"Worker Exception: {e}")
            
        await asyncio.sleep(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    await update.message.reply_text("VIP Bot Started! Prediction များ စတင်ပေးပို့ပါတော့မည်။")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_chats:
        active_chats.remove(chat_id)
    await update.message.reply_text("Bot ကို ရပ်တန့်လိုက်ပါပြီ။")

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
        
