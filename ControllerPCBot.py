import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from PIL import ImageGrab

#Вставьте сюда ваш токен/Paste your token here
TELEGRAM_TOKEN = 'YOUR_TOKEN'
ADMIN_ID = 12345678

waiting_for_time = False


texts = {
    'ru': {
        'start_message': "Выберите команду:",
        'reboot': "Перезагрузить ПК",
        'screenshot': "Сделать скриншот",
        'off': "Выключить ПК",
        'offthen': "Выключить ПК позже",
        'cancel_shutdown': "Отменить выключение",
        'language': "Язык/Language",
        'choose_language': "Выберите язык:",
        'rebooting': "Перезагрузка компьютера...",
        'taking_screenshot': "Делаю скриншот...",
        'screenshot_sent': "Скриншот отправлен!",
        'shutting_down': "Выключение компьютера...",
        'shutdown_cancelled': "Выключение отменено!",
        'ask_time': "Через сколько минут вы хотите выключить компьютер?",
        'shutdown_scheduled': "Компьютер будет выключен через {} минут.",
        'invalid_time': "Пожалуйста, введите корректное число минут.",
        'sleep': "Перевести компьютер в спящий режим",
        'sleeping': "Перевод компьютера в спящий режим..."
    },
    'en': {
        'start_message': "Select a command:",
        'reboot': "Reboot PC",
        'screenshot': "Take a Screenshot",
        'off': "Shut Down PC",
        'offthen': "Shut Down Later",
        'cancel_shutdown': "Cancel Shutdown",
        'language': "Language/Язык",
        'choose_language': "Choose a language:",
        'rebooting': "Rebooting the computer...",
        'taking_screenshot': "Taking a screenshot...",
        'screenshot_sent': "Screenshot sent!",
        'shutting_down': "Shutting down the computer...",
        'shutdown_cancelled': "Shutdown cancelled!",
        'ask_time': "How many minutes until shutdown?",
        'shutdown_scheduled': "The computer will shut down in {} minutes.",
        'invalid_time': "Please enter a valid number of minutes.",
        'sleep': "Put PC to Sleep",
        'sleeping': "Putting the computer to sleep..."
    }
}


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


async def send_start_message(update_or_query, context: ContextTypes.DEFAULT_TYPE, language: str) -> None:
    keyboard = [
        [InlineKeyboardButton(texts[language]['reboot'], callback_data='reboot')],
        [InlineKeyboardButton(texts[language]['screenshot'], callback_data='screenshot')],
        [InlineKeyboardButton(texts[language]['off'], callback_data='off')],
        [InlineKeyboardButton(texts[language]['offthen'], callback_data='offthen')],
        [InlineKeyboardButton(texts[language]['cancel_shutdown'], callback_data='cancel_shutdown')],
        [InlineKeyboardButton(texts[language]['sleep'], callback_data='sleep')],
        [InlineKeyboardButton(texts[language]['language'], callback_data='change_language')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(update_or_query, Update):
        await update_or_query.message.reply_text(texts[language]['start_message'], reply_markup=reply_markup)
    else:
        await update_or_query.edit_message_text(texts[language]['start_message'], reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    language = context.user_data.get('language', 'ru')
    await send_start_message(update, context, language)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global waiting_for_time
    query = update.callback_query
    await query.answer()

    
    if not is_admin(query.from_user.id):
        await query.edit_message_text("You are not authorized to use this bot.")
        return

  
    language = context.user_data.get('language', 'ru')

    if query.data == 'reboot':
        await query.edit_message_text(text=texts[language]['rebooting'])
        if os.name == 'nt':
            subprocess.call('shutdown /r /t 1', shell=True)
        else:
            subprocess.call('sudo reboot', shell=True)

    elif query.data == 'screenshot':
        await query.edit_message_text(text=texts[language]['taking_screenshot'])
        screenshot_path = 'screenshot.png'
        if os.name == 'nt':
            img = ImageGrab.grab()
            img.save(screenshot_path)
        else:
            subprocess.call(['gnome-screenshot', '-f', screenshot_path])

        await context.bot.send_photo(chat_id=query.message.chat_id, photo=open(screenshot_path, 'rb'))
        os.remove(screenshot_path)
        await query.edit_message_text(text=texts[language]['screenshot_sent'])

    elif query.data == 'off':
        await query.edit_message_text(text=texts[language]['shutting_down'])
        if os.name == 'nt':
            subprocess.call('shutdown /s /t 1', shell=True)
        else:
            subprocess.call('sudo shutdown now', shell=True)

    elif query.data == 'offthen':
        waiting_for_time = True
        await query.edit_message_text(text=texts[language]['ask_time'])

    elif query.data == 'cancel_shutdown':
        await query.edit_message_text(text=texts[language]['shutdown_cancelled'])
        if os.name == 'nt':
            subprocess.call('shutdown /a', shell=True)
        else:
            subprocess.call('sudo shutdown -c', shell=True)

    elif query.data == 'sleep':
        await query.edit_message_text(text=texts[language]['sleeping'])
        if os.name == 'nt':
            
            subprocess.call('rundll32.exe powrprof.dll,SetSuspendState 0,1,0', shell=True)
        else:
            
            subprocess.call('systemctl suspend', shell=True)

    elif query.data == 'change_language':
        keyboard = [
            [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_language:ru')],
            [InlineKeyboardButton("🇬🇧 English", callback_data='set_language:en')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=texts[language]['choose_language'], reply_markup=reply_markup)

    elif query.data.startswith('set_language:'):
        new_language = query.data.split(':')[1]
        context.user_data['language'] = new_language
        await send_start_message(query, context, new_language)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global waiting_for_time
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return

    language = context.user_data.get('language', 'ru')
    if waiting_for_time:
        try:
            minutes = int(update.message.text)
            seconds = minutes * 60
            if os.name == 'nt':
                subprocess.call(f'shutdown /s /t {seconds}', shell=True)
            else:
                subprocess.call(f'sudo shutdown +{minutes}', shell=True)
            await update.message.reply_text(texts[language]['shutdown_scheduled'].format(minutes))
            waiting_for_time = False
        except ValueError:
            await update.message.reply_text(texts[language]['invalid_time'])


def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
