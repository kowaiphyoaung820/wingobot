import os
import threading
import asyncio
import requests
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
last_processed_period = None
current_bet_multiplier = 1
history_results = {}

# API မှ Result ရယူခြင်း (CK/WinGo API Endpoint)
def fetch_history():
    try:
        # WinGo 30s / 1m API URL (Public Result Endpoint)
        url = "https://api.singaporepredict.com/api/wingo30"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"API Fetch Error: {e}")
    return []

async def auto_prediction_worker(app: Application):
    global last_processed_period, current_bet_multiplier
    
    while True:
        try:
            if active_chats:
                history = await asyncio.to_thread(fetch_history)
                if history and len(history) > 0:
                    latest_item = history[0]
                    latest_period = str(latest_item.get("issueNumber"))
                    
                    # Match Number အသစ် ထွက်လာမှသာ အလုပ်လုပ်မည်
                    if latest_period != last_processed_period:
                        last_num = int(latest_item.get("number", 0))
                        actual_result = "BIG" if last_num >= 5 else "SMALL"
                        
                        # ၁။ ယခင်ထွက်ထားသော Prediction ကို ရှုံး/နိုင် (Win/Loss) စစ်ဆေးခြင်း
                        result_status = ""
                        if last_processed_period in history_results:
                            predicted = history_results[last_processed_period]
                            if predicted == actual_result:
                                result_status = f"✅ **WIN** (Result: {actual_result} - {last_num})"
                                current_bet_multiplier = 1 # နိုင်လျှင် ၁ ဆ သို့ ပြန်လျှော့မည်
                            else:
                                result_status = f"❌ **LOSS** (Result: {actual_result} - {last_num})"
                                current_bet_multiplier *= 3 # ရှုံးလျှင် ၃ ဆ တိုးမည်

                        # ၂။ Match အသစ်အတွက် Prediction တွက်ချက်ခြင်း
                        next_period = str(int(latest_period) + 1)
                        next_pred = "BIG" if last_num >= 5 else "SMALL" # Pattern Formula Logic
                        
                        # Result ကို မှတ်ထားခြင်း
                        history_results[next_period] = next_pred
                        
                        # မက်ဆေ့ချ် Format တည်ဆောက်ခြင်း
                        msg_lines = []
                        if result_status:
                            msg_lines.append(f"📊 **LAST MATCH RESULT**: {result_status}\n")
                        
                        msg_lines.append(
                            f"🔥 **WIN GO PREDICTION** 🔥\n\n"
                            f"🎯 **MATCH** : {next_period}\n"
                            f"📍 **BUY**   : **{next_pred}**\n"
                            f"💵 **BET**   : **{current_bet_multiplier} x**"
                        )
                        
                        msg = "\n".join(msg_lines)
                        
                        for chat_id in list(active_chats):
                            try:
                                await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                            except Exception as err:
                                print(f"Send Error ({chat_id}): {err}")
                        
                        last_processed_period = latest_period
        except Exception as e:
            print(f"Worker Error: {e}")
            
        await asyncio.sleep(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    await update.message.reply_text("✅ VIP Predictor စတင်ပါပြီ! Match အမှန်နှင့် Win/Loss ပြသပေးပါမည်။")

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
    
