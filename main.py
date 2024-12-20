import telebot
import json

API_TOKEN = 'BOT_TOKEN'
USER_ID_1 = 1231231231
USER_ID_2 = 12312312312
MESSAGES_FILE = 'messages.json'
USER_STATES_FILE = 'user_states.json'
BLOCKED_USERS_FILE = 'blocked_users.json'
bot = telebot.TeleBot(API_TOKEN)
messages = {}
user_states = {}
blocked_users = []

def load_messages():
    global messages
    try:
        with open(MESSAGES_FILE, 'r') as f:
            messages = json.load(f)
    except FileNotFoundError:
        messages = {}


def save_messages():
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f)


def load_user_states():
    global user_states
    try:
        with open(USER_STATES_FILE, 'r') as f:
            user_states = json.load(f)
    except FileNotFoundError:
        user_states = {}


def save_user_states():
    with open(USER_STATES_FILE, 'w') as f:
        json.dump(user_states, f)


def load_blocked_users():
    global blocked_users
    try:
        with open(BLOCKED_USERS_FILE, 'r') as f:
            blocked_users = json.load(f)
    except FileNotFoundError:
        blocked_users = []


def save_blocked_users():
    with open(BLOCKED_USERS_FILE, 'w') as f:
        json.dump(blocked_users, f)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для анонимных вопросов. "
                         "Отправь мне свой вопрос, фото или видео, и я перешлю его двум другим пользователям.")
@bot.message_handler(commands=['block', 'unblock'], content_types=['text', 'photo', 'video'])
def handle_block_unblock(message):
    if message.chat.id in [USER_ID_1, USER_ID_2]:
        if message.reply_to_message is not None:
            try:
                # Ищем ID отправителя по ID пересланного сообщения
                sender_id = None
                for sender, message_ids in messages.items():
                    if message.reply_to_message.message_id in message_ids:
                        sender_id = int(sender)
                        break

                if sender_id is not None:
                    if message.text.startswith('/block'):
                        if sender_id not in blocked_users:
                            blocked_users.append(sender_id)
                            save_blocked_users()
                            bot.reply_to(message, f"Пользователь заблокирован.")
                        else:
                            bot.reply_to(message, f"Пользователь уже заблокирован.")

                    elif message.text.startswith('/unblock'):
                        if sender_id in blocked_users:
                            blocked_users.remove(sender_id)
                            save_blocked_users()
                            bot.reply_to(message, f"Пользователь разблокирован.")
                        else:
                            bot.reply_to(message, f"Пользователь не заблокирован.")
                else:
                    bot.reply_to(message, "Не удалось найти отправителя этого сообщения.")

            except ValueError:
                bot.reply_to(message, "Ошибка при обработке команды.")
        else:
            bot.reply_to(message, "Чтобы заблокировать/разблокировать пользователя, "
                                 "ответьте на его сообщение командой /block или /unblock.")
    else:
        bot.reply_to(message, "У вас нет прав для блокировки/разблокировки пользователей.")

@bot.message_handler(func=lambda message: message.chat.id in user_states)
def handle_confirmation(message):                                                                              
    if message.text == 'Отправить':
        original_message = user_states[message.chat.id]
        if original_message['content_type'] == 'text':
            sent_message_1 = bot.send_message(USER_ID_1, f"Анонимный вопрос: {original_message['text']}")
            sent_message_2 = bot.send_message(USER_ID_2, f"Анонимный вопрос: {original_message['text']}")
            

        elif original_message['content_type'] == 'photo':
            sent_message_1 = bot.send_photo(USER_ID_1, photo=original_message['photo'], 
                           caption=f"Анонимное фото: {(original_message.get('caption') if original_message.get('caption') else '')}")  
            sent_message_2 = bot.send_photo(USER_ID_2, photo=original_message['photo'], 
                           caption=f"Анонимное фото: {(original_message.get('caption') if original_message.get('caption') else '')}")  
                                                       

        elif original_message['content_type'] == 'video':
            sent_message_1 = bot.send_video(USER_ID_1, video=original_message['video'], 
                           caption=f"Анонимное видео: {(original_message.get('caption') if original_message.get('caption') else '')}")  
            sent_message_2 = bot.send_video(USER_ID_2, video=original_message['video'], 
                           caption=f"Анонимное видео: {(original_message.get('caption') if original_message.get('caption') else '')}")  
        bot.send_message(message.chat.id, "Доставлено!", reply_markup=telebot.types.ReplyKeyboardRemove())
        if str(message.chat.id) not in messages:
            messages[str(message.chat.id)] = []
        messages[str(message.chat.id)].extend([sent_message_1.message_id, sent_message_2.message_id])
        save_messages()
    elif message.text == 'Отмена':
        bot.send_message(message.chat.id, "Отправка отменена.",reply_markup=telebot.types.ReplyKeyboardRemove())

    del user_states[message.chat.id]
    save_user_states()


@bot.message_handler(content_types=['text', 'photo', 'video'])
def handle_question(message):
    if message.chat.id not in blocked_users:
        user_states[message.chat.id] = {
            'content_type': message.content_type,
            'message_id': message.message_id,
            'text': message.text,
            'photo': message.photo[-1].file_id if message.photo else None,
            'video': message.video.file_id if message.video else None,
            'caption': message.caption
        }
        save_user_states()
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(telebot.types.KeyboardButton('Отправить'),
                     telebot.types.KeyboardButton('Отмена'))
        bot.send_message(message.chat.id, "Вы хотите отправить это сообщение анонимно?", reply_markup=keyboard)
    else:
        bot.reply_to(message, "Вы заблокированы.")

load_messages()
load_blocked_users()
load_user_states()
bot.polling(none_stop=True)