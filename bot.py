import os
import threading
import asyncio
import random
import requests
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

# Bot Token (Render Environment Variable မှ ရယူရန်)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

active_chats = set()
current_bet_multiplier = 1
last_pred = None
last_match = None

def fetch_game_result(period):
    """
    WinGo Game API မှ ရလဒ် ရယူသည့် Function ဖြစ်ပါသည်။
    သင့် Game API Endpoint ရှိပါက ဤနေရာတွင် တိုက်ရိုက် ချိတ်ဆက်နိုင်ပါသည်။
    """
    try:
        # API ချိတ်ဆက်လိုပါက အောက်ပါ လိုင်းများကို Un-comment လုပ်ပါ:
        # response = requests.get(f"https://your-game-api.com/result?period={period}", timeout=5)
        # return response.json().get("result") # "BIG" သို့မဟုတ် "SMALL" ပြန်ရပါမည်
        
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

async def auto_prediction_worker(app: Application):
    global current_bet_multiplier, last_pred, last_match
    
    base_bet_amount = 100  # အခြေခံ လောင်းကြေး ၁ ဆ = 100 KS
    
    while True:
        try:
            if active_chats:
                now = datetime.now()
                
                # ၁ ရက်တာတွင် ကုန်လွန်ခဲ့သော စက္ကန့် စုစုပေါင်း (30s Period index အတွက်)
                seconds_today = now.hour * 3600 + now.minute * 60 + now.second
                period_index = (seconds_today // 30) + 1
                
                # Match ID Formula: YYYYMMDD + GameType Code (10005) + Period Number
                current_match = f"{now.strftime('%Y%m%d')}10005{period_index:04d}"
                
                if current_match != last_match:
                    # ယခင် Period ၏ Win/Loss ကို စစ်ဆေးခြင်း
                    if last_match and last_pred:
                        actual_result = fetch_game_result(last_match)
                        
                        if actual_result:
                            if last_pred == actual_result:
                                current_bet_multiplier = 1  # နိုင်လျှင် 1x သို့ ပြန်စမည်
                            else:
                                current_bet_multiplier *= 3  # ရှုံးလျှင် 3 ဆ တိုးမည်
                        else:
                            # API မရှိသေးပါက ယာယီ Simulation စစ်ဆေးခြင်း Logic (ရလဒ် အမှန်ရှိလျှင် အလိုအလျောက် ပိတ်သွားမည်)
                            simulated_win = random.choice([True, False])
                            if simulated_win:
                                current_bet_multiplier = 1
                            else:
                                current_bet_multiplier *= 3

                    next_pred = random.choice(["𝘽𝙄𝙂", "𝙎𝙈𝘼𝙇𝙇"])
                    
                    # BET နေရာတွင် Multiplier နှင့် အမောက်ကို တွဲရက် ပြသထားသည်
                    calculated_amount = current_bet_multiplier * base_bet_amount
                    bet_display = f"{current_bet_multiplier}x ({calculated_amount:,} KS)"
                    
                    msg = (
                        f"⚡ **🎯 𝙒𝙄𝙉𝙂𝙊 𝟯𝟬𝙎 𝙋𝙍𝙀𝘿𝙄𝘾𝙏𝙄𝙊𝙉 🔮** ⚡\n\n"
                        f"🎯 𝐌𝐀𝐓𝐂𝐇  ;  `{current_match}`\n"
                        f"📍 𝐁𝐔𝐘        ;  **{next_pred}**\n"
                        f"💵 𝐁𝐄𝐓        ;  **{bet_display}**"
                    )
                    
                    for chat_id in list(active_chats):
                        try:
                            await app.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                        except Exception as err:
                            print(f"Send Error ({chat_id}): {err}")
                            
                    last_pred = "BIG" if "𝘽𝙄𝙂" in next_pred else "SMALL"
                    last_match = current_match

        except Exception as e:
            print(f"Worker Error: {e}")
            
        await asyncio.sleep(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_chats.add(chat_id)
    
    welcome_msg = (
        "မင်္ဂလာပါ 🤖 𝘾𝙆 𝘽𝙊𝙏 🤖 မှ ကြိုဆိုပါတယ်\n\n"
        "🎯 𝙒𝙞𝙣𝙂𝙤 30 𝙎𝙚𝙘𝙤𝙣𝙙𝙨 ⏱️ Prediction စတင်ပါပြီ။"
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
    
