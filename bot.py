import logging
import re
import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    MessageHandler, 
    filters
)

# កំណត់ Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8830422453:AAFV-03sYZo8Rh_6DWpdXsBgSUVcDhRDtq4"
GROUP_LINK = "https://t.me/wetv57"

# បញ្ជីពាក្យអសុរោះ ឬពាក្យហាមឃាត់ និងពាក្យជេរប្រមាថ
BAD_WORDS = [
    "ខុសសព្ទ", "ខលសាប់", "call សាប់", "ខ សព្វ", "ខសព្វ", "ចុយ",
    "ជេរម៉ែ", "ម៉ែហែង", "ឪហែង", "អាម៉ែ", "មីម៉ែ", "អញម៉ែ", "អញឪ",
    "អាក្បត់", "មីងាប់", "អាងាប់"
]

# មុខងារស្វាគមន៍សមាជិកថ្មី (លុបអូតូក្រោយ ១០ វិនាទី)
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        chat_id = update.message.chat_id
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                continue
            user_mention = member.mention_html()
            welcome_text = (
                f"សួស្តី {user_mention}! សូមស្វាគមន៍មកកាន់ group យើងខ្ញុំ។ ❤️️\n"
                f"group នេះអត់មានច្បាប់អីទេ អាចនិយាយគ្នា និងរាប់អានមិត្តភាពថ្មីៗបាន!"
            )
            try:
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    parse_mode="HTML"
                )
                # រង់ចាំ ១០ វិនាទី រួចលុបសារ
                context.job_queue.run_once(
                    delete_welcome_msg, 
                    10, 
                    data={"chat_id": chat_id, "message_id": sent_message.message_id}
                )
            except Exception as e:
                print(f"មានបញ្ហាក្នុងការផ្ញើសារស្វាគមន៍: {e}")

async def delete_welcome_msg(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.data["chat_id"], message_id=job.data["message_id"])
    except Exception as e:
        print(f"មិនអាចលុបសារស្វាគមន៍បាន: {e}")

# មុខងារពិនិត្យសារ និងលុប Link/ពាក្យហាមឃាត់ (អនុវត្តលើគ្រប់គ្នា រួមទាំង Admin)
async def handle_chat_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    message = update.message
    chat_id = message.chat_id
    message_id = message.message_id
    user_text = message.text or message.caption or ""

    # 1. ពិនិត្យមើល Link គ្រប់ប្រភេទ ( Telegram links, http/https URLs ) - លុបទាំងអស់ មិនថា Admin ឬអត់
    has_link = re.search(
        r'(t\.me/|telegram\.me/|https?://|www\.)', 
        user_text, 
        re.IGNORECASE
    )

    # 2. ពិនិត្យពាក្យអសុរោះ / ជេរប្រមាថ
    has_bad_word = any(re.search(re.escape(word), user_text, re.IGNORECASE) for word in BAD_WORDS)
    
    # 3. ពិនិត្យសេវាកម្មខល / ខលសេវា / call សាប់
    has_bad_service_call = re.search(
        r'(សេវា|សេវាកម្ម|ទិញ|ប្ដូរ|ជួប|រក).*?(call|ខល|ខ)|(call|ខល|ខ).*?(សេវា|សេវាកម្ម|ទិញ|ជួប|រក)', 
        user_text, 
        re.IGNORECASE
    )
    
    # 4. ពិនិត្យពាក្យ ខល$ ឬ Call$ ឬ ខ$
    has_call_dollar = re.search(r'(call|ខល|ខ)\s*\$', user_text, re.IGNORECASE)
    
    # 5. ពិនិត្យពាក្យ ខល + Emoji 💧
    has_call_with_emoji = re.search(r'(call|ខល|ខ)\s*💧', user_text, re.IGNORECASE)

    # ប្រសិនបើចូលលក្ខខណ្ឌណាមួយខាងលើ គឺលុបសារភ្លាមៗ
    if has_link or has_bad_word or has_bad_service_call or has_call_dollar or has_call_with_emoji:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"បានលុបសារហាមឃាត់/Link ដោយជោគជ័យ!")
        except Exception as e:
            print(f"មិនអាចលុបសារបាន (សូមពិនិត្យមើលសិទ្ធិ Admin របស់ Bot): {e}")

# មុខងារផ្ញើសារអញ្ជើញចូល Group តាមម៉ោង ( Scheduled Broadcast )
async def send_group_invite(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    
    # សារផ្សព្វផ្សាយបែបទំនង និងទាក់ទាញ
    invite_text = (
        "🌟 **សូមអញ្ជើញចូលរួមគ្រុប «គ្រួសាររីករាយ»** 🌟\n\n"
        "✨ ចង់បានមិត្តភក្តិនិយាយលេងកម្សាន្ត? រាប់អានមិត្តភាពថ្មីៗ និយាយគ្នាសប្បាយៗដោយគ្មានសម្ពាធ?\n"
        "👉 **ចូលរួមជាមួយយើងឥឡូវនេះ!** គ្រុបយើងបើករង់ចាំស្វាគមន៍អ្នកជានិច្ច 💖\n\n"
        "👇 *ចុចប៊ូតុងខាងក្រោមដើម្បីចូលរួមគ្រុប:*"
    )
    
    keyboard = [
        [InlineKeyboardButton("👉 ចុចចូលគ្រុប «គ្រួសាររីករាយ» 👈", url=GROUP_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=invite_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        print("បានផ្ញើសារផ្សព្វផ្សាយគ្រុបតាមម៉ោងដោយជោគជ័យ!")
    except Exception as e:
        print(f"មិនអាចផ្ញើសារផ្សព្វផ្សាយបានទេ: {e}")

def main():
    # កំណត់ Timezone កម្ពុជា ( Asia/Phnom_Penh )
    cambodia_tz = pytz.timezone('Asia/Phnom_Penh')

    application = ApplicationBuilder().token(TOKEN).build()

    # កំណត់ម៉ោងផ្ញើអូតូ ( 07:00 ព្រឹក, 10:00 ព្រឹក, 02:00 យប់ )
    job_queue = application.job_queue
    
    # ម៉ោង 07:00 AM
    job_queue.run_daily(
        send_group_invite, 
        time=datetime.time(hour=7, minute=0, second=0, tzinfo=cambodia_tz)
    )
    # ម៉ោង 10:00 AM
    job_queue.run_daily(
        send_group_invite, 
        time=datetime.time(hour=10, minute=0, second=0, tzinfo=cambodia_tz)
    )
    # ម៉ោង 02:00 AM (រំលងអធ្រាត្រ)
    job_queue.run_daily(
        send_group_invite, 
        time=datetime.time(hour=2, minute=0, second=0, tzinfo=cambodia_tz)
    )

    # ដាក់ Handler
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_chat_messages))

    print("Bot កំពុងដំណើរការពេញលេញហើយ...")
    application.run_polling()

if __name__ == '__main__':
    main()
