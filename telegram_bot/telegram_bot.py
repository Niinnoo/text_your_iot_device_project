from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from prompt_processor import Prompt_Processor
import asyncio
import os
import json
from datetime import datetime, timedelta
from functools import wraps
from settings_handler import Settings

# Files to store user data
AUTH_LOG_FILE = "authenticated_users.json"
settings = Settings()

# Configuration
AUTH_PASSWORD = os.environ.get("BOT_AUTH_PASSWORD")  # Set this as environment variable
SESSION_TIMEOUT = timedelta(hours=1)  # Session expires after 1 hour
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_TIME = timedelta(minutes=30)

# Load authenticated users from file
def load_authenticated_users():
    if os.path.exists(AUTH_LOG_FILE):
        try:
            with open(AUTH_LOG_FILE, "r") as file:
                data = json.load(file)
                # Convert string dates back to datetime objects
                for user_id, session in data.items():
                    if "expires" in session:
                        session["expires"] = datetime.fromisoformat(session["expires"])
                    if "locked_until" in session:
                        session["locked_until"] = datetime.fromisoformat(session["locked_until"])
                return data
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}

# Save authenticated users to file
def save_authenticated_users():
    with open(AUTH_LOG_FILE, "w") as file:
        # Convert datetime objects to strings
        data = {}
        for user_id, session in authenticated_users.items():
            session_data = {**session}
            if "expires" in session:
                session_data["expires"] = session["expires"].isoformat()
            if "locked_until" in session:
                session_data["locked_until"] = session["locked_until"].isoformat()
            data[user_id] = session_data
        json.dump(data, file)

# Dictionary to store authenticated sessions
# Format: {user_id: {"expires": datetime, "attempts": int}}
authenticated_users = load_authenticated_users()

def check_auth(func):
    """Decorator to check if user is authenticated"""
    @wraps(func)
    async def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = str(update.effective_user.id)

        # Remove expired sessions
        now = datetime.now()
        expired_users = [uid for uid, session in authenticated_users.items() if "expires" in session and session["expires"] <= now]
        for uid in expired_users:
            del authenticated_users[uid]
        save_authenticated_users()

        # Check if user is authenticated and session is valid
        if user_id in authenticated_users:
            session = authenticated_users[user_id]
            if "expires" in session and session["expires"] > now:
                # Update session expiry time
                authenticated_users[user_id]["expires"] = now + SESSION_TIMEOUT
                save_authenticated_users()
                return await func(update, context, *args, **kwargs)
            else:
                # Session expired
                del authenticated_users[user_id]
                save_authenticated_users()

        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"not_authenticated"))
        return None
    return wrapped

async def login(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)

    # Delete the user's message
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)

    # Check if user is already authenticated
    if user_id in authenticated_users:
        session = authenticated_users[user_id]
        if "expires" in session and session["expires"] > datetime.now():
            await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"already_authenticated"))
            return

    # Check if user is locked out
    if user_id in authenticated_users and authenticated_users[user_id].get("locked_until"):
        if authenticated_users[user_id]["locked_until"] > datetime.now():
            await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"locked_out"))
            return
        else:
            # Reset lockout
            authenticated_users[user_id] = {"attempts": 0}

    # Get password from command
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"login_explanation"))
        return

    password = context.args[0]

    # Check password
    if password == AUTH_PASSWORD:
        authenticated_users[user_id] = {
            "expires": datetime.now() + SESSION_TIMEOUT,
            "attempts": 0
        }
        save_authenticated_users()
        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"login_success"))
    else:
        # Handle failed attempt
        if user_id not in authenticated_users:
            authenticated_users[user_id] = {"attempts": 1}
        else:
            authenticated_users[user_id]["attempts"] += 1

        # Check if max attempts reached
        if authenticated_users[user_id]["attempts"] >= MAX_LOGIN_ATTEMPTS:
            authenticated_users[user_id]["locked_until"] = datetime.now() + LOCKOUT_TIME
            save_authenticated_users()
            await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"locked_out"))
        else:
            save_authenticated_users()
            await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"login_failure"))

async def logout(update: Update, context: CallbackContext) -> None:
    user_id = str(update.effective_user.id)
    if user_id in authenticated_users:
        del authenticated_users[user_id]
        save_authenticated_users()
        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"logged_out"))
    else:
        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"not_authenticated"))

# Function that gets called on the /start command
@check_auth
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"greeting"))

# Function that gets called on the /help command
@check_auth
async def help(update: Update, context: CallbackContext, processor: Prompt_Processor) -> None:
    await update.message.reply_text(processor.help(user_id=context._user_id))

@check_auth
async def temp(update: Update, context: CallbackContext, processor: Prompt_Processor, resource) -> None:
    try:
        response = await processor.get_sensor_value(user_id=context._user_id, resource=resource)
        if "No suitable credentials" in response:
            if update.callback_query:
                await update.callback_query.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"connection_failed"))
            else:
                await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"connection_failed"))
        elif response is not None:
            if update.callback_query:
                await update.callback_query.message.reply_text(response)
            else:
                await update.message.reply_text(response)
        else:
            if update.callback_query:
                await update.callback_query.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"no_data"))
            else:
                await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"no_data"))
    
    except ValueError as e:
        if update.callback_query:
            await update.callback_query.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"network_error"))
        else:
            await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"network_error"))

    except Exception as e:
        if update.callback_query:
            await update.callback_query.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"unknown_error", error=str(e)))
        else:
            await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"unknown_error", error=str(e)))

# Function that gets called on the /internal_temp command
@check_auth
async def internal_temp(update: Update, context: CallbackContext, processor: Prompt_Processor) -> None:
    await temp(update, context, processor, "internal_temp")

# Function that gets called on the /external_temp command
@check_auth
async def external_temp(update: Update, context: CallbackContext, processor: Prompt_Processor) -> None:
    await temp(update, context, processor, "external_temp")

# Function that gets called on the /humidity command
@check_auth
async def get_humidity(update: Update, context: CallbackContext, processor: Prompt_Processor) -> None:
    await temp(update, context, processor, "hum")

# Function for reacting on text messages
@check_auth
async def handle_message(update: Update, context: CallbackContext, processor: Prompt_Processor) -> None:
    text_received = update.message.text.lower()
    async def send_typing_action():
      try:
        await update.message.chat.send_action("typing")
        await asyncio.sleep(3)
        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"loading"))
        await update.message.chat.send_action("typing")
        await asyncio.sleep(5)
        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"extended_loading"))
        while True:
            await update.message.chat.send_action("typing")
            await asyncio.sleep(5)  # send typing action every 5 seconds
      except asyncio.CancelledError:
            pass

    typing_task = asyncio.create_task(send_typing_action())

    try:
      # Answer should be given within 15 seconds, otherwise -> error
        action = await asyncio.wait_for(
            processor.process(text_received),
            timeout=25
        )
        response = await processor.process_action(action,user_id=context._user_id)
    except asyncio.TimeoutError:
        await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"timeout_error"))
        await update.message.chat.send_sticker('CAACAgIAAxkBAAExH49nlOhu-7i3UqCcXRmVkKTsGxBNFgAC8wADVp29Cmob68TH-pb-NgQ')
        return
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    if response == "choose_temperature_sensor":
        await choose_temperature_sensor(update, context, processor)
    else:
        await update.message.reply_text(response)


# Function that gets called on the /temp command
@check_auth
async def choose_temperature_sensor(update: Update, context: CallbackContext, processor: Prompt_Processor) -> None:
    keyboard = [
        [InlineKeyboardButton(settings.get_translation(settings.get_user_language(str(context._user_id)),"external_temp"), callback_data='temp_external' )],
        [InlineKeyboardButton(settings.get_translation(settings.get_user_language(str(context._user_id)),"internal_temp"), callback_data='temp_internal')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"choose_temperature_sensor"), reply_markup=reply_markup)

# Function that gets called on the /lang command
@check_auth
async def language(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en' )],
        [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='lang_de')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)),"choose_language"), reply_markup=reply_markup)

@check_auth
async def tempunit(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("°C", callback_data='tempunit_c')],
        [InlineKeyboardButton("°F", callback_data='tempunit_f')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(settings.get_translation(settings.get_user_language(str(context._user_id)), "choose_temp_unit"), reply_markup=reply_markup)

langs = {
    "en": "English",
    "de": "Deutsch",
}
tempunits = {
    "c": "°C",
    "f": "°F"
}

@check_auth
async def button(update: Update, context: CallbackContext, processor: Prompt_Processor) -> None:
    """Handles button clicks for language selection and temperature unit selection."""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    data = query.data.split('_')
    if data[0] == "lang":
        lang_code = data[1].lower()
        language = langs.get(lang_code, "English")
        # Set the user's language preference using your language handler
        settings.set_user_language(user_id, lang_code)
        await query.edit_message_text(text=settings.get_translation(settings.get_user_language(user_id), "language_set", language=language))
    elif data[0] == "tempunit":
        # For temperature unit selection:
        tempunit = data[1].lower()  # Expecting 'C' or 'F'
        temp = tempunits.get(tempunit, "°C")
        settings.set_user_temp_unit(user_id, tempunit)
        # Confirm the selection with the user (the translation can include a placeholder for the unit)
        await query.edit_message_text(text=settings.get_translation(settings.get_user_language(user_id), "tempunit_set", unit=temp))
    elif data[0] == "temp":
        if data[1] == "internal":
            await query.edit_message_text(text=settings.get_translation(settings.get_user_language(user_id), "internal_temp_requested"))
            await internal_temp(update, context, processor)
        elif data[1] == "external":
            await query.edit_message_text(text=settings.get_translation(settings.get_user_language(user_id), "external_temp_requested"))
            await external_temp(update, context, processor)

def main() -> None:
    processor = Prompt_Processor()

    application = Application.builder().token("YOUR_TOKEN").build()

    # authentication handlers
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("logout", logout))

    # Telegram command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", lambda update, context: help(update, context, processor)))
    application.add_handler(CommandHandler("temp", lambda update, context: choose_temperature_sensor(update, context, processor)))
    application.add_handler(CommandHandler("lang", language))
    application.add_handler(CommandHandler("tempunit", tempunit))
    application.add_handler(CommandHandler("internal_temp", lambda update, context: internal_temp(update, context, processor)))
    application.add_handler(CommandHandler("external_temp", lambda update, context: external_temp(update, context, processor)))
    application.add_handler(CommandHandler("humidity", lambda update, context: get_humidity(update, context, processor)))

    # Callback query handler for button presses (handles both language and temperature unit)
    application.add_handler(CallbackQueryHandler(lambda update, context: button(update, context, processor)))

    # Text message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda update, context: handle_message(update, context, processor)))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
