import logging
import re
import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    MessageHandler, 
    CallbackQueryHandler,
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

# ----------------------------------------------------
# 1. មុខងារស្វាគមន៍សមាជិកថ្មី (លុបអូតូក្រោយ ១០ វិនាទី)
# ----------------------------------------------------
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        chat_id = update.message.chat_id
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                continue
            user_mention = member.mention_html()
            welcome_text = (
                f"✨ <b>សួស្តី {user_mention}!</b> ✨\n"
                f"សូមស្វាគមន៍យ៉ាងកក់ក្តៅមកកាន់គ្រួសាររបស់យើង! 💖\n\n"
                f"💬 <i>ទីនេះគ្មានច្បាប់តឹងរ៉ឹងទេ និយាយគ្នាលេងកម្សាន្ត និងរាប់អានមិត្តភក្តិថ្មីៗដោយសេរីណា!</i>"
            )
            try:
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    parse_mode="HTML"
                )
                # រង់ចាំ ១០ វិនាទី រួចលុបសារស្វាគមន៍
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

# ----------------------------------------------------
# 2. មុខងារពិនិត្យសារ និងលុប Link/ពាក្យហាមឃាត់ (លុបលើគ្រប់គ្នា រួមទាំង Admin)
# ----------------------------------------------------
async def handle_chat_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    message = update.message
    chat_id = message.chat_id
    message_id = message.message_id
    user_text = message.text or message.caption or ""

    # ពិនិត្យមើល Link គ្រប់ប្រភេទ (t.me, http, https, www)
    has_link = re.search(
        r'(t\.me/|telegram\.me/|https?://|www\.)', 
        user_text, 
        re.IGNORECASE
    )

    # ពិនិត្យពាក្យអសុរោះ
    has_bad_word = any(re.search(re.escape(word), user_text, re.IGNORECASE) for word in BAD_WORDS)
    
    # ពិនិត្យសេវាកម្មខល / Call សេវា
    has_bad_service_call = re.search(
        r'(សេវា|សេវាកម្ម|ទិញ|ប្ដូរ|ជួប|រក).*?(call|ខល|ខ)|(call|ខល|ខ).*?(សេវា|សេវាកម្ម|ទិញ|ជួប|រក)', 
        user_text, 
        re.IGNORECASE
    )
    
    # ពិនិត្យពាក្យ ខល$ / Call$
    has_call_dollar = re.search(r'(call|ខល|ខ)\s*\$', user_text, re.IGNORECASE)
    
    # ពិនិត្យពាក្យ ខល + Emoji 💧
    has_call_with_emoji = re.search(r'(call|ខល|ខ)\s*💧', user_text, re.IGNORECASE)

    # ប្រសិនបើចូលលក្ខខណ្ឌណាមួយខាងលើ គឺលុបសារភ្លាមៗ
    if has_link or has_bad_word or has_bad_service_call or has_call_dollar or has_call_with_emoji:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"បានលុបសារហាមឃាត់/Link ដោយជោគជ័យ!")
        except Exception as e:
            print(f"មិនអាចលុបសារបាន: {e}")

# ----------------------------------------------------
# 3. មុខងារផ្ញើសារអញ្ជើញចូល Group បែប Premium
# ----------------------------------------------------
async def send_group_invite(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    
    # សាររចនាបែប Premium & Clean
    invite_text = (
        "💎 *— « គ្រួសាររីករាយ » —* 💎\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "✨ *តើអ្នកកំពុងស្វែងរកបរិយាកាសកក់ក្តៅ និងរីករាយមែនទេ?*\n\n"
        "ចូលរួមជាមួយពួកយើងដើម្បី៖\n"
        "🔹 ជជែកកម្សាន្ត និងចែករំលែកបទពិសោធន៍\n"
        "🔹 រាប់អានមិត្តភក្តិថ្មីៗ ប្រកបដោយភាពស្និទ្ធស្នាល\n"
        "🔹 បន្ធូរអារម្មណ៍ពីការងារ និងការសិក្សា\n\n"
        "💌 *ពួកយើងរង់ចាំស្វាគមន៍អ្នកជានិច្ច! ចុចប៊ូតុងខាងក្រោមដើម្បីចូលរួម៖*"
    )
    
    # ប៊ូតុង Join និងប៊ូតុងសម្រាប់ Admin ចុចលុបសារ
    keyboard = [
        [InlineKeyboardButton("✨ ចូលរួមគ្រុបឥឡូវនេះ (JOIN NOW) ✨", url=GROUP_LINK)],
        [InlineKeyboardButton("🗑️ លុបសារនេះ (Admin តែប៉ុណ្ណោះ)", callback_data="delete_promo_msg")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=invite_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        print("បានផ្ញើសារ Premium Promo ដោយជោគជ័យ!")
    except Exception as e:
        print(f"មិនអាចផ្ញើសារផ្សព្វផ្សាយបានទេ: {e}")

# ----------------------------------------------------
# 4. មុខងារដំណើរការការចុចប៊ូតុង "លុបសារ" (Delete Button Handler)
# ----------------------------------------------------
async def handle_delete_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "delete_promo_msg":
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        # ពិនិត្យមើលថាតើអ្នកចុចជា Admin ឬ Creator ដែរឬទេ?
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ["administrator", "creator"]:
                await query.message.delete()
                print("Admin បានចុចលុបសារផ្សព្វផ្សាយដោយជោគជ័យ!")
            else:
                await query.answer(text="⚠️ មានតែ Admin ទេទើបអាចចុចលុបសារនេះបាន!", show_alert=True)
        except Exception as e:
            print(f"មានបញ្ហាក្នុងការពិនិត្យសិទ្ធិ ឬលុបសារ: {e}")

# ----------------------------------------------------
# 5. Main Execution Function
# ----------------------------------------------------
def main():
    cambodia_tz = pytz.timezone('Asia/Phnom_Penh')
    application = ApplicationBuilder().token(TOKEN).build()

    # កំណត់ម៉ោងផ្ញើអូតូ ( 07:00 AM, 10:00 AM, 02:00 AM )
    job_queue = application.job_queue
    
    job_queue.run_daily(
        send_group_invite, 
        time=datetime.time(hour=7, minute=0, second=0, tzinfo=cambodia_tz)
    )
    job_queue.run_daily(
        send_group_invite, 
        time=datetime.time(hour=10, minute=0, second=0, tzinfo=cambodia_tz)
    )
    job_queue.run_daily(
        send_group_invite, 
        time=datetime.time(hour=2, minute=0, second=0, tzinfo=cambodia_tz)
    )

    # ដាក់ Handlers
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(CallbackQueryHandler(handle_delete_button))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_chat_messages))

    print("Bot កំពុងដំណើរការពេញលេញហើយ...")
    application.run_polling()

if __name__ == '__main__':
    main()
