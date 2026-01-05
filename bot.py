import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
import sqlite3


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_ID = int(os.environ.get("API_ID", 29033249))
API_HASH = os.environ.get("API_HASH", "682f28f83a90b82025f4f7bb7ae1ef1c")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8466098625:AAGmKlIgj5oYBo33dLFnB60OGTqy9YNJCtM")


DB_NAME = "bot_settings.db"


CREATORS = [601668306, 8588773170]  # ایدی شما و سازنده دوم

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (admin_id INTEGER PRIMARY KEY, group_id INTEGER, channel_id INTEGER, is_active INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sent_messages
                 (message_key TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def get_settings(admin_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT group_id, channel_id, is_active FROM settings WHERE admin_id=?", (admin_id,))
    result = c.fetchone()
    conn.close()
    return result if result else (None, None, 0)

def update_settings(admin_id, group_id=None, channel_id=None, is_active=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    current = get_settings(admin_id)
    new_group = group_id if group_id is not None else current[0]
    new_channel = channel_id if channel_id is not None else current[1]
    new_active = is_active if is_active is not None else current[2]
    
    c.execute('''REPLACE INTO settings (admin_id, group_id, channel_id, is_active)
                 VALUES (?, ?, ?, ?)''', (admin_id, new_group, new_channel, new_active))
    conn.commit()
    conn.close()

def is_message_sent(message):
    """بررسی می‌کند پیام قبلاً ارسال شده یا نه"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    
    if message.forward_from_chat:
        message_key = f"{message.forward_from_chat.id}_{message.forward_from_message_id}"
    elif message.forward_from:
        message_key = f"{message.forward_from.id}_{message.forward_from_message_id}"
    else:
        message_key = f"{message.chat.id}_{message.id}"
    
    c.execute("SELECT 1 FROM sent_messages WHERE message_key=?", (message_key,))
    result = c.fetchone()
    conn.close()
    
    return result is not None

def mark_message_sent(message):
    """علامت گذاری پیام به عنوان ارسال شده"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    
    if message.forward_from_chat:
        message_key = f"{message.forward_from_chat.id}_{message.forward_from_message_id}"
    elif message.forward_from:
        message_key = f"{message.forward_from.id}_{message.forward_from_message_id}"
    else:
        message_key = f"{message.chat.id}_{message.id}"
    
    c.execute("INSERT OR IGNORE INTO sent_messages (message_key) VALUES (?)", (message_key,))
    conn.commit()
    conn.close()


app = Client("forward_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def creators_filter(_, __, message: Message):
    return message.from_user and message.from_user.id in CREATORS

creators_only = filters.create(creators_filter)

@app.on_message(filters.command("start") & creators_only)
async def start_cmd(client, message: Message):
    await message.reply_text(
        "🤖 **ربات فوروارد فعال شد!**\n\n"
        "📋 **دستورات:**\n"
        "• `/setgroup [ایدی]` - تنظیم گروه\n"
        "• `/setchannel [ایدی]` - تنظیم کانال\n"
        "• `/startbot` - شروع فوروارد\n"
        "• `/stopbot` - توقف فوروارد\n"
        "• `/status` - وضعیت فعلی\n"
        "• `/clearcache` - پاکسازی حافظه پیام‌ها"
    )

@app.on_message(filters.command("setgroup") & creators_only)
async def set_group(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("❌ لطفا ایدی گروه را وارد کنید:\n`/setgroup -1001234567890`")
            return
        
        group_id = int(message.command[1])
        update_settings(message.from_user.id, group_id=group_id)
        
        await message.reply_text(f"✅ گروه تنظیم شد: `{group_id}`")
        
    except ValueError:
        await message.reply_text("❌ ایدی گروه باید عددی باشد")

@app.on_message(filters.command("setchannel") & creators_only)
async def set_channel(client, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("❌ لطفا ایدی کانال را وارد کنید:\n`/setchannel -1001234567890`")
            return
        
        channel_id = int(message.command[1])
        update_settings(message.from_user.id, channel_id=channel_id)
        
        await message.reply_text(f"✅ کانال تنظیم شد: `{channel_id}`")
        
    except ValueError:
        await message.reply_text("❌ ایدی کانال باید عددی باشد")

@app.on_message(filters.command("startbot") & creators_only)
async def start_bot(client, message: Message):
    group_id, channel_id, is_active = get_settings(message.from_user.id)
    
    if not group_id or not channel_id:
        await message.reply_text("❌ لطفا ابتدا گروه و کانال را تنظیم کنید")
        return
    
    update_settings(message.from_user.id, is_active=1)
    await message.reply_text("✅ ربات شروع به کار کرد!")

@app.on_message(filters.command("stopbot") & creators_only)
async def stop_bot(client, message: Message):
    update_settings(message.from_user.id, is_active=0)
    await message.reply_text("⏹ ربات متوقف شد!")

@app.on_message(filters.command("status") & creators_only)
async def status_cmd(client, message: Message):
    group_id, channel_id, is_active = get_settings(message.from_user.id)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sent_messages")
    sent_count = c.fetchone()[0]
    conn.close()
    
    status_text = (
        f"📊 **وضعیت ربات:**\n\n"
        f"• **گروه:** `{group_id or 'تنظیم نشده'}`\n"
        f"• **کانال:** `{channel_id or 'تنظیم نشده'}`\n"
        f"• **وضعیت:** {'🟢 فعال' if is_active else '🔴 غیرفعال'}\n"
        f"• **پیام‌های ذخیره شده:** {sent_count}"
    )
    
    await message.reply_text(status_text)

@app.on_message(filters.command("clearcache") & creators_only)
async def clear_cache(client, message: Message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM sent_messages")
    conn.commit()
    conn.close()
    await message.reply_text("✅ حافظه پیام‌ها پاکسازی شد!")

@app.on_message(filters.group & ~filters.service)
async def handle_forwarded_messages(client, message: Message):
    try:
        
        if not message.forward_from_chat and not message.forward_from:
            return
        
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT group_id, channel_id, is_active FROM settings LIMIT 1")
        result = c.fetchone()
        conn.close()
        
        if not result:
            return
            
        group_id, channel_id, is_active = result
        

        if not is_active or message.chat.id != group_id:
            return
        

        if is_message_sent(message):
            logger.info(f"پیام تکراری شناسایی شد، فوروارد نشد: {message.id}")
            return
        

        await message.forward(channel_id)
        

        mark_message_sent(message)
        
        logger.info(f"پیام فوروارد شده از {message.chat.id} به {channel_id}")
        
    except Exception as e:
        logger.error(f"خطا در فوروارد: {e}")


if __name__ == "__main__":
    init_db()
    logger.info("ربات در حال راه‌اندازی...")
    app.run()
