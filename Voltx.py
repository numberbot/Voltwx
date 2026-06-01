import requests
import time
import threading
import re
import json
import os
import base64
from datetime import datetime
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import pyotp

# ==================== কনফিগারেশন ====================
TELEGRAM_TOKEN = "8073094767:AAGcUgULUjTCw5vHHe_XM0HLlPIapkgmv8E"
ADMIN_ID = 7461687719

API_BASE_URL = "https://2oo9.cloud/api/MXS47FLFX0U/project/tetragonexvoltxsms/@public/api"
API_KEY = "MMOVHYMBXU3"

HEADERS = {
    "mauthapi": API_KEY,
    "Content-Type": "application/json"
}

LOG_GROUP_ID = "-1003988424162"
OTP_GROUP_URL = "https://t.me/da_marketing_oto"

# ==================== আপনার নাম এনকোডেড (বেস64) ====================
_ENCODED_NAME = "RGV2ZWxvcGVyIEFSQUZBVDo="

def get_footer():
    try:
        decoded_name = base64.b64decode(_ENCODED_NAME).decode('utf-8')
        clean_name = decoded_name.replace(":", "")
        return f"\n\n━━━━━━━━━━━━━━━━━━━━\n{clean_name}"
    except:
        return ""

# ==================== ডাটাবেস ====================
USER_DB = "users.json"
USER_DATA_DB = "user_data.json"
SETTINGS_DB = "settings.json"
WITHDRAWALS_DB = "withdrawals.json"
ACTIVE_NUMBERS_DB = "active_numbers.json"

def init_databases():
    files = {
        USER_DB: [],
        USER_DATA_DB: {},
        SETTINGS_DB: {"otp_price": 5.0, "min_withdraw": 50.0},
        WITHDRAWALS_DB: [],
        ACTIVE_NUMBERS_DB: {}
    }
    for file, default in files.items():
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump(default, f)

init_databases()

def get_user_balance(user_id):
    with open(USER_DATA_DB, "r") as f:
        data = json.load(f)
    return data.get(str(user_id), {}).get("balance", 0.0)

def update_user_balance(user_id, amount):
    with open(USER_DATA_DB, "r") as f:
        data = json.load(f)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"balance": 0.0}
    data[uid]["balance"] = round(data[uid]["balance"] + amount, 2)
    with open(USER_DATA_DB, "w") as f:
        json.dump(data, f)

def get_all_users():
    with open(USER_DB, "r") as f:
        return json.load(f)

def add_user(user_id):
    with open(USER_DB, "r") as f:
        users = json.load(f)
    if user_id not in users:
        users.append(user_id)
        with open(USER_DB, "w") as f:
            json.dump(users, f)
    
    with open(USER_DATA_DB, "r") as f:
        data = json.load(f)
    if str(user_id) not in data:
        data[str(user_id)] = {"balance": 0.0}
        with open(USER_DATA_DB, "w") as f:
            json.dump(data, f)

def get_settings():
    with open(SETTINGS_DB, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_DB, "w") as f:
        json.dump(settings, f)

def get_withdrawals():
    with open(WITHDRAWALS_DB, "r") as f:
        return json.load(f)

def save_withdrawals(withdraws):
    with open(WITHDRAWALS_DB, "w") as f:
        json.dump(withdraws, f)

def get_active_numbers():
    with open(ACTIVE_NUMBERS_DB, "r") as f:
        return json.load(f)

def save_active_numbers(numbers):
    with open(ACTIVE_NUMBERS_DB, "w") as f:
        json.dump(numbers, f)

def add_active_number(phone, chat_id, service, range_code):
    data = get_active_numbers()
    data[str(phone)] = {
        "chat_id": chat_id,
        "service": service,
        "range": range_code,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_active_numbers(data)
    print(f"✅ Added: {phone}")

def remove_active_number(phone):
    data = get_active_numbers()
    if str(phone) in data:
        del data[str(phone)]
        save_active_numbers(data)
    print(f"🗑️ Removed: {phone}")

def mask_number(phone):
    phone_str = str(phone)
    if len(phone_str) >= 10:
        return phone_str[:7] + "XXX" + phone_str[-2:]
    return phone_str

def extract_otp_from_text(text):
    clean_text = re.sub(r'[-\s]', '', text)
    patterns = [
        r'\b(\d{8})\b', r'\b(\d{7})\b', r'\b(\d{6})\b',
        r'\b(\d{5})\b', r'\b(\d{4})\b', r'\b(\d{3})\b',
        r'code[:\s]*(\d+)', r'OTP[:\s]*(\d+)', r'(\d+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, clean_text, re.IGNORECASE)
        if match and len(match.group(1)) >= 3:
            return match.group(1)
    return "N/A"

def get_service_name_from_msg(msg):
    msg_lower = msg.lower()
    if 'facebook' in msg_lower:
        return "Facebook"
    elif 'whatsapp' in msg_lower:
        return "WhatsApp"
    elif 'instagram' in msg_lower:
        return "Instagram"
    return "Unknown"

# ==================== OTP নোটিফিকেশন (বাটন ছাড়া) ====================
def send_otp_notification(chat_id, phone, service, otp, message, price):
    masked = mask_number(phone)
    footer = get_footer()
    
    dm_msg = f"""✅ OTP RECEIVED!
━━━━━━━━━━━━━━━━━━━━
📱 Number: `{phone}`
🎯 Service: {service}
🌍 Panel: VOLTX
━━━━━━━━━━━━━━━━━━━━
🔐 OTP Code: `{otp}`
━━━━━━━━━━━━━━━━━━━━
📩 Full SMS:
`{message[:200]}`
━━━━━━━━━━━━━━━━━━━━
💰 Income: +{price} BDT{footer}"""
    
    group_msg = f"""✅ OTP RECEIVED!
━━━━━━━━━━━━━━━━━━━━
📱 Number: `{masked}`
🎯 Service: {service}
🌍 Panel: VOLTX
━━━━━━━━━━━━━━━━━━━━
🔐 OTP Code: `{otp}`
━━━━━━━━━━━━━━━━━━━━
📩 Full SMS:
`{message[:200]}`
━━━━━━━━━━━━━━━━━━━━
💰 Income: +{price} BDT{footer}"""
    
    try:
        bot.send_message(chat_id, dm_msg, parse_mode="Markdown")
        bot.send_message(LOG_GROUP_ID, group_msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Send error: {e}")

# ==================== নাম্বার রিসিভ নোটিফিকেশন (বাটন সহ) ====================
def send_number_received_notification(chat_id, numbers, service_name):
    numbers_text = "\n".join([f"✅ `{num}`" for num in numbers])
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.row(InlineKeyboardButton("📢 OTP GROUP", url=OTP_GROUP_URL))
    markup.row(InlineKeyboardButton("🔄 Change Number", callback_data=f"change_number_{service_name}"))
    markup.row(InlineKeyboardButton("🔙 Back to Ranges", callback_data="back_to_ranges"))
    
    msg = f"""🎯 Number Received!

{numbers_text}

🎯 Service: {service_name}

💡 OTP will appear here automatically!
💰 Earn {get_settings()['otp_price']} BDT per OTP"""
    
    bot.send_message(chat_id, msg, parse_mode="Markdown", reply_markup=markup)

# ==================== VOLTX API ফাংশন ====================
def voltx_get_live_services():
    url = f"{API_BASE_URL}/liveaccess"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                services = data.get("data", {}).get("services", [])
                if services:
                    return services
    except:
        pass
    
    return [
        {"sid": "Facebook", "ranges": ["8801XXX", "22501XXX"]},
        {"sid": "WhatsApp", "ranges": ["8801XXX", "447XXX"]}
    ]

def voltx_get_ranges_for_service(service_name):
    services = voltx_get_live_services()
    for s in services:
        if s.get("sid", "").lower() == service_name.lower():
            ranges = s.get("ranges", [])
            if ranges:
                return ranges
    return ["8801XXX", "22501XXX"]

def voltx_fetch_number(range_code):
    rid = range_code.replace("XXX", "").replace("X", "").strip()
    if not rid:
        rid = "8801"
    
    url = f"{API_BASE_URL}/getnum"
    payload = {"rid": rid}
    
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            
            if data.get("meta", {}).get("code") == 200:
                number_data = data.get("data", {})
                full_number = number_data.get("full_number") or number_data.get("no_plus_number")
                if full_number:
                    return str(full_number).replace("+", "").strip()
            elif data.get("success") and data.get("data", {}).get("full_number"):
                return data["data"]["full_number"].replace("+", "").strip()
    except:
        pass
    return None

def voltx_check_otp():
    url = f"{API_BASE_URL}/success-otp"
    results = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if data.get("meta", {}).get("code") == 200:
                otps = data.get("data", {}).get("otps", [])
                active = get_active_numbers()
                
                for phone in active:
                    for otp in otps:
                        otp_number = otp.get("number", "").replace("+", "").strip()
                        if phone == otp_number or phone in otp_number:
                            message = otp.get("message", "")
                            if message:
                                otp_code = extract_otp_from_text(message)
                                service_name = get_service_name_from_msg(message)
                                if service_name == "Unknown":
                                    service_name = active[phone].get("service", "Unknown")
                                if otp_code != "N/A":
                                    results.append({
                                        "phone": phone,
                                        "message": message,
                                        "otp": otp_code,
                                        "service": service_name,
                                    })
                                    break
    except:
        pass
    return results

# ==================== কীবোর্ড ====================
def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🎲 GET NUMBER"), KeyboardButton("🔐 2FA CODE"))
    markup.row(KeyboardButton("💰 BALANCE"), KeyboardButton("💳 WITHDRAWAL"))
    markup.row(KeyboardButton("📩 CONTACT ADMIN"))
    return markup

def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("📢 Broadcast"), KeyboardButton("📊 Stats"))
    markup.row(KeyboardButton("💵 Price Edit"), KeyboardButton("📥 Pending Withdrawals"))
    markup.row(KeyboardButton("🔙 Back Main Menu"))
    return markup

def get_service_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    services = voltx_get_live_services()
    
    for s in services[:4]:
        sid = s.get("sid", "Unknown")
        markup.add(InlineKeyboardButton(f"📘 {sid}", callback_data=f"service_{sid.lower()}"))
    
    markup.row(InlineKeyboardButton("🔄 Refresh Services", callback_data="refresh_services"))
    markup.row(InlineKeyboardButton("🔙 Back Main Menu", callback_data="back_main_menu"))
    return markup

def get_range_keyboard(ranges, service):
    markup = InlineKeyboardMarkup(row_width=2)
    for r in ranges[:10]:
        markup.add(InlineKeyboardButton(f"📱 {r}", callback_data=f"get_number_{service}_{r}"))
    markup.row(InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_ranges_{service}"))
    markup.row(InlineKeyboardButton("🔙 Back to Services", callback_data="back_to_services"))
    return markup

def get_2fa_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🔄 Regenerate"))
    markup.row(KeyboardButton("🔙 Back Main Menu"))
    return markup

# ==================== বট হ্যান্ডলারস ====================
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_service = {}
user_last_range = {}

@bot.message_handler(commands=['start'])
def start(message):
    add_user(message.chat.id)
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "👋 Welcome Admin!", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(
            message.chat.id,
            f"✨ Welcome {message.from_user.first_name}! ✨\n\n💰 Balance: {get_user_balance(message.chat.id)} BDT",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🔧 Admin Panel", reply_markup=get_admin_keyboard())

@bot.message_handler(func=lambda m: m.text == "🎲 GET NUMBER")
def handle_get_number(message):
    bot.send_message(message.chat.id, "🔍 Select Service:", reply_markup=get_service_keyboard())

# ==================== ইনলাইন কলব্যাক ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data
    
    if data == "back_main_menu":
        bot.edit_message_text("🏠 Main Menu", chat_id, msg_id, reply_markup=get_main_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data == "back_to_services":
        bot.edit_message_text("🔍 Select Service:", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data == "back_to_ranges":
        service_name = user_service.get(chat_id, "facebook")
        ranges = voltx_get_ranges_for_service(service_name)
        if ranges:
            bot.edit_message_text(f"🔥 Live Ranges for {service_name.capitalize()}:", chat_id, msg_id, reply_markup=get_range_keyboard(ranges, service_name))
        else:
            bot.edit_message_text("❌ No live ranges found!", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data == "refresh_services":
        bot.edit_message_text("🔄 Refreshing services...", chat_id, msg_id)
        time.sleep(1)
        bot.edit_message_text("🔍 Select Service:", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("refresh_ranges_"):
        service_name = data.replace("refresh_ranges_", "")
        ranges = voltx_get_ranges_for_service(service_name)
        if ranges:
            bot.edit_message_text(f"🔥 Live Ranges for {service_name.capitalize()} (Refreshed):", chat_id, msg_id, reply_markup=get_range_keyboard(ranges, service_name))
        else:
            bot.edit_message_text("❌ No live ranges found!", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    if data.startswith("service_"):
        service_name = data.replace("service_", "")
        user_service[chat_id] = service_name
        
        ranges = voltx_get_ranges_for_service(service_name)
        
        if ranges:
            bot.edit_message_text(f"🔥 Live Ranges for {service_name.capitalize()}:", chat_id, msg_id, reply_markup=get_range_keyboard(ranges, service_name))
        else:
            bot.edit_message_text(f"❌ No live ranges found!", chat_id, msg_id, reply_markup=get_service_keyboard())
        bot.answer_callback_query(call.id)
        return
    
    # নাম্বার নেওয়া - ২টি নাম্বার (ডিফল্ট ২)
    if data.startswith("get_number_"):
        parts = data.split("_")
        service_name = parts[2]
        range_code = parts[3]
        
        user_last_range[chat_id] = range_code
        user_service[chat_id] = service_name
        
        bot.delete_message(chat_id, msg_id)
        loading_msg = bot.send_message(chat_id, f"⏳ Requesting number from `{range_code}`...", parse_mode="Markdown")
        
        numbers_found = []
        number = voltx_fetch_number(range_code)
        if number:
            numbers_found.append(number)
            add_active_number(number, chat_id, service_name.capitalize(), range_code)
        
        if numbers_found:
            bot.delete_message(chat_id, loading_msg.message_id)
            send_number_received_notification(chat_id, numbers_found, service_name.capitalize())
        else:
            bot.delete_message(chat_id, loading_msg.message_id)
            bot.send_message(
                chat_id,
                f"❌ No numbers available!\n\nTry another range.",
                reply_markup=get_range_keyboard(voltx_get_ranges_for_service(service_name), service_name)
            )
        bot.answer_callback_query(call.id)
        return
    
    # চেঞ্জ নাম্বার (Change Number) - ২টি নাম্বার
    if data.startswith("change_number_"):
        service_name = data.replace("change_number_", "")
        range_code = user_last_range.get(chat_id)
        
        if not range_code:
            bot.answer_callback_query(call.id, "Select range first!", show_alert=True)
            return
        
        bot.delete_message(chat_id, msg_id)
        loading_msg = bot.send_message(chat_id, f"⏳ Requesting new number...", parse_mode="Markdown")
        
        numbers_found = []
        number = voltx_fetch_number(range_code)
        if number:
            numbers_found.append(number)
            add_active_number(number, chat_id, service_name, range_code)
        
        if numbers_found:
            bot.delete_message(chat_id, loading_msg.message_id)
            send_number_received_notification(chat_id, numbers_found, service_name)
        else:
            bot.delete_message(chat_id, loading_msg.message_id)
            bot.send_message(chat_id, f"❌ No numbers available!")
        bot.answer_callback_query(call.id)
        return

# ==================== রিপ্লাই কীবোর্ড হ্যান্ডলার ====================
@bot.message_handler(func=lambda m: m.text == "🔙 Back Main Menu")
def back_main(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🏠 Main Menu", reply_markup=get_admin_keyboard())
    else:
        bot.send_message(message.chat.id, "🏠 Main Menu", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "💰 BALANCE")
def handle_balance(message):
    bal = get_user_balance(message.chat.id)
    bot.send_message(message.chat.id, f"💰 Balance: `{bal}` BDT", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 WITHDRAWAL")
def handle_withdraw(message):
    bal = get_user_balance(message.chat.id)
    settings = get_settings()
    if bal < settings["min_withdraw"]:
        bot.send_message(message.chat.id, f"❌ Failed! Min: {settings['min_withdraw']} BDT\nYour balance: {bal} BDT", parse_mode="Markdown")
    else:
        msg = bot.send_message(message.chat.id, "💳 Enter Bkash number:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_withdraw_req, bal)

@bot.message_handler(func=lambda m: m.text == "📩 CONTACT ADMIN")
def contact_admin(message):
    msg = bot.send_message(message.chat.id, "📝 Write your message:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, forward_to_admin)

@bot.message_handler(func=lambda m: m.text == "🔐 2FA CODE")
def handle_2fa(message):
    msg = bot.send_message(message.chat.id, "🔐 Send 2FA Secret Key:\nExample: JBSWY3DPEHPK3PXP", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_2fa)

def process_withdraw_req(message, amount):
    bkash = message.text.strip()
    if len(bkash) < 11 or not bkash.isdigit():
        bot.send_message(message.chat.id, "❌ Invalid Bkash number!", parse_mode="Markdown")
        return
    
    withdrawals = get_withdrawals()
    req_id = len(withdrawals) + 1
    
    new_req = {
        "id": req_id,
        "user_id": message.chat.id,
        "bkash": bkash,
        "amount": amount,
        "status": "pending",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    withdrawals.append(new_req)
    save_withdrawals(withdrawals)
    update_user_balance(message.chat.id, -amount)
    
    bot.send_message(message.chat.id, f"✅ Withdrawal Request Submitted!\n💰 Amount: {amount} BDT\n📱 Bkash: {bkash}", parse_mode="Markdown")
    bot.send_message(ADMIN_ID, f"🔔 New Withdrawal!\nUser: {message.chat.id}\nAmount: {amount} BDT\nBkash: {bkash}")

def forward_to_admin(message):
    if message.text:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💬 Reply", callback_data=f"reply_{message.chat.id}"))
        bot.send_message(ADMIN_ID, f"📩 New Message from {message.from_user.first_name}\nID: {message.chat.id}\n\n{message.text}", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ Message sent to admin!")

def process_2fa(message):
    secret = message.text.strip().replace(" ", "")
    try:
        totp = pyotp.TOTP(secret)
        otp = totp.now()
        bot.send_message(message.chat.id, f"🔐 Your 2FA Code:\n\n`{otp}`", parse_mode="Markdown", reply_markup=get_2fa_keyboard())
    except:
        bot.send_message(message.chat.id, "❌ Invalid Secret Key!", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "🔄 Regenerate")
def regenerate_2fa(message):
    msg = bot.send_message(message.chat.id, "🔐 Send 2FA Secret Key:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_2fa)

# ==================== এডমিন ====================
@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text in ["📢 Broadcast", "📊 Stats", "💵 Price Edit", "📥 Pending Withdrawals"])
def admin_buttons(message):
    if message.text == "📢 Broadcast":
        msg = bot.send_message(message.chat.id, "📢 Send broadcast:")
        bot.register_next_step_handler(msg, broadcast_msg)
    elif message.text == "📊 Stats":
        users = len(get_all_users())
        active = len(get_active_numbers())
        settings = get_settings()
        bot.send_message(message.chat.id, f"📊 Stats\n👥 Users: {users}\n📱 Active: {active}\n💰 Price: {settings['otp_price']} BDT\n💳 Min: {settings['min_withdraw']} BDT")
    elif message.text == "💵 Price Edit":
        msg = bot.send_message(message.chat.id, "💰 New OTP price:")
        bot.register_next_step_handler(msg, edit_price)
    elif message.text == "📥 Pending Withdrawals":
        withdrawals = get_withdrawals()
        pending = [w for w in withdrawals if w["status"] == "pending"]
        if not pending:
            bot.send_message(message.chat.id, "📭 No pending!")
            return
        for w in pending:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{w['id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{w['id']}")
            )
            bot.send_message(message.chat.id, f"📥 Request\nID: {w['id']}\nUser: {w['user_id']}\nAmount: {w['amount']} BDT\nBkash: {w['bkash']}", reply_markup=markup)

def broadcast_msg(message):
    users = get_all_users()
    success = 0
    for uid in users:
        try:
            bot.send_message(uid, f"📢 Broadcast\n\n{message.text}")
            success += 1
            time.sleep(0.05)
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ Sent to {success} users!")

def edit_price(message):
    try:
        price = float(message.text)
        settings = get_settings()
        settings["otp_price"] = price
        save_settings(settings)
        bot.send_message(message.chat.id, f"✅ Price set to {price} BDT!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid!")

# ==================== এডমিন কলব্যাক ====================
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_") or call.data.startswith("reply_"))
def admin_callback(call):
    if call.data.startswith("approve_"):
        wd_id = int(call.data.split("_")[1])
        withdrawals = get_withdrawals()
        for w in withdrawals:
            if w["id"] == wd_id and w["status"] == "pending":
                w["status"] = "approved"
                save_withdrawals(withdrawals)
                bot.edit_message_text(f"✅ Approved! ID: {wd_id}", call.message.chat.id, call.message.message_id)
                try:
                    bot.send_message(w["user_id"], f"🎉 Withdrawal of {w['amount']} BDT approved!")
                except:
                    pass
                break
        bot.answer_callback_query(call.id)
    elif call.data.startswith("reject_"):
        wd_id = int(call.data.split("_")[1])
        withdrawals = get_withdrawals()
        for w in withdrawals:
            if w["id"] == wd_id and w["status"] == "pending":
                w["status"] = "rejected"
                update_user_balance(w["user_id"], w["amount"])
                save_withdrawals(withdrawals)
                bot.edit_message_text(f"❌ Rejected! ID: {wd_id}", call.message.chat.id, call.message.message_id)
                try:
                    bot.send_message(w["user_id"], f"❌ Withdrawal rejected. Amount refunded.")
                except:
                    pass
                break
        bot.answer_callback_query(call.id)
    elif call.data.startswith("reply_"):
        user_id = int(call.data.split("_")[1])
        msg = bot.send_message(call.message.chat.id, f"✍️ Reply to {user_id}:")
        bot.register_next_step_handler(msg, send_reply, user_id)
        bot.answer_callback_query(call.id)

def send_reply(message, user_id):
    try:
        bot.send_message(user_id, f"👨‍💻 Admin Reply:\n\n{message.text}")
        bot.send_message(message.chat.id, f"✅ Reply sent!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Failed: {e}")

# ==================== OTP মনিটর ====================
sent_otps = set()

def otp_monitor():
    global sent_otps
    print("🔄 OTP Monitor Started")
    while True:
        try:
            settings = get_settings()
            price = settings.get("otp_price", 5.0)
            otps = voltx_check_otp()
            
            for otp in otps:
                phone = otp["phone"]
                unique_key = f"{phone}_{otp['otp']}"
                
                if unique_key not in sent_otps:
                    sent_otps.add(unique_key)
                    
                    active = get_active_numbers()
                    if str(phone) in active:
                        chat_id = active[str(phone)]["chat_id"]
                        update_user_balance(chat_id, price)
                        send_otp_notification(chat_id, phone, otp["service"], otp["otp"], otp["message"], price)
                        remove_active_number(phone)
            
            if len(sent_otps) > 2000:
                sent_otps.clear()
                
        except Exception as e:
            print(f"Monitor Error: {e}")
        time.sleep(5)

# ==================== মেইন ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 VOLTX OTP BOT")
    print("✅ 1 number will be fetched at once")
    print("✅ Buttons shown when numbers received")
    print("✅ No buttons when OTP received")
    print("=" * 60)
    
    threading.Thread(target=otp_monitor, daemon=True).start()
    
    print("✅ Bot Running!")
    print("=" * 60)
    
    bot.infinity_polling(timeout=60)