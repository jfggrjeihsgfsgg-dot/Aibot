import logging
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "8830422453:AAFV-03sYZo8Rh_6DWpdXsBgSUVcDhRDtq4"

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
                f"សួស្តី {user_mention}! សូមស្វាគមន៍មកកាន់ group យើងខ្ញុំ។ "
                f"group នេះអត់មានច្បាប់អីទេ អាចនិយាយគ្នា និងរាប់អានមិត្តភាពថ្មីៗបាន!"
            )
            try:
                sent_message = await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    parse_mode="HTML"
                )
                await asyncio.sleep(10)
                await context.bot.delete_message(chat_id=chat_id, message_id=sent_message.message_id)
            except Exception as e:
                print(f"មានបញ្ហាក្នុងការផ្ញើ ឬលុបសារស្វាគមន៍: {e}")

# មុខងារពិនិត្យសារធម្មតា
async def handle_chat_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user:
        message = update.message
        chat_id = message.chat_id
        message_id = message.message_id
        user = message.from_user
        user_text = message.text or message.caption or ""
        
        # 1. ពិនិត្យមើលថាតើអ្នកផ្ញើសារគឺជា Admin ដែរឬទេ?
        is_admin = False
        if message.chat.type in ["group", "supergroup"]:
            try:
                member_status = await context.bot.get_chat_member(chat_id=chat_id, user_id=user.id)
                if member_status.status in ["administrator", "creator"]:
                    is_admin = True
            except Exception as e:
                print(f"មិនអាចពិនិត្យសិទ្ធិ Admin បាន: {e}")
        
        # ប្រសិនបើមិនមែនជា Admin ទេ ត្រូវធ្វើការពិនិត្យពាក្យហាមឃាត់
        if not is_admin:
            # ពិនិត្យពាក្យអសុរោះ / ជេរប្រមាថ
            has_bad_word = any(re.search(re.escape(word), user_text, re.IGNORECASE) for word in BAD_WORDS)
            
            # ពិនិត្យសេវាកម្មខល / ខលសេវា / ទិញខល / ជួបខល (ទម្រង់ផ្សេងៗគ្នា)
            has_bad_service_call = re.search(
                r'(សេវា|សេវាកម្ម|ទិញ|ប្ដូរ|ជួប|រក).*?(call|ខល|ខ)|(call|ខល|ខ).*?(សេវា|សេវាកម្ម|ទិញ|ជួប|រក)', 
                user_text, 
                re.IGNORECASE
            )
            
            # ពិនិត្យពាក្យ ខល$ ឬ Call$ ឬ ខ$ ជាប់គ្នា ឬដកឃ្លាបន្តិចបន្តួច
            has_call_dollar = re.search(r'(call|ខល|ខ)\s*\$', user_text, re.IGNORECASE)
            
            # ពិនិត្យពាក្យ ខល ប្រើ Emoji ទឹក ឬសញ្ញាផ្សេងៗ
            has_call_with_emoji = re.search(r'(call|ខល|ខ)\s*💧', user_text, re.IGNORECASE)
            
            # ពិនិត្យតំណភ្ជាប់ Telegram Link
            is_telegram_link = re.search(r'(t\.me/|telegram\.me/)', user_text, re.IGNORECASE)

            # ប្រសិនបើត្រូវលក្ខខណ្ឌណាមួយ គឺលុបសារចោលភ្លាមៗ
            if has_bad_word or has_bad_service_call or has_call_dollar or has_call_with_emoji or is_telegram_link:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    print(f"បានលុបសារហាមឃាត់/សេវាកម្មខលរបស់សមាជិកដោយជោគជ័យ!")
                    return
                except Exception as e:
                    print(f"មិនអាចលុបសារបាន (សូមពិនិត្យសិទ្ធិ Admin របស់ Bot): {e}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_chat_messages))

    print("Bot កំពុងដំណើរការពេញលេញហើយ...")
    application.run_polling()

if __name__ == '__main__':
    main()
    