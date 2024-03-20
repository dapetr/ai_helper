import telebot
from telebot import types
from config import token
from gpt import *
import logging


#logging.basicConfig(filename='log_file.txt',
 #                   level=logging.DEBUG,
  #                  format="%(asctime)s %(message)s")

bot = telebot.TeleBot(token)


history_limit = 20
chat_history = {}


def menu_keyboard(options):
    buttons = (types.KeyboardButton(text=option) for option in options)
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True,
                                         one_time_keyboard=True)
    keyboard.add(*buttons)
    return keyboard


@bot.message_handler(commands=["start"])
def start_message(message):
    logging.debug(f"User {message.from_user.id} started the bot")
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}!\n"
                          f"Выбери команду /solve_task, напиши мне любой вопрос, я на него отвечу.\n"
                          "Если ответ не отправится полностью, выбери комнаду /continue.",
                     reply_markup=menu_keyboard(["/solve_task", "/help", "/history"])
                     )


@bot.message_handler(commands=["help"])
def start_message(message):
    logging.debug(f"User {message.from_user.id} asked the bot for help")
    bot.send_message(message.chat.id,
                     text=f"/solve_task - начать новое решение.\n"
                          f"/history - просмотр истории\n"
                          f"/continue - продолжить решение\n"
                          f'/end - закончить решение',
                     reply_markup=menu_keyboard(["/solve_task", "/help", "/history"])
                     )


@bot.message_handler(commands=["history"])
def send_history(message):
    logging.debug(f"User {message.from_user.id} requested chat history")

    user_id = message.from_user.id
    if user_id in chat_history and len(chat_history[user_id]) > 0:
        history = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in chat_history[user_id]]
        )
        bot.reply_to(message, f"Ваша история сообщений:\n{history}")
    else:
        bot.reply_to(message, "У вас нет истории сообщений.")


#@bot.message_handler(commands=['debug'])
#def logs(message):
 #   with open("log_file.txt", "rb") as f:
  #      bot.send_document(message.chat.id, f)


@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    bot.send_message(message.chat.id, "Напиши условие новой задачи:")
    bot.register_next_step_handler(message, handle_message)


def handle_message(message):
    user_id = message.from_user.id

    logging.debug(f"User {message.from_user.id} sent a message: {message.text}")

    if message.content_type != "text":
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, handle_message)

    if len(message.text) > max_tokens:
        bot.send_message(message.chat.id, "Слишком большая задача, сократите ее размер для того, чтобы бот смог на неё ответить.")
        bot.register_next_step_handler(message, handle_message)

    user_id = message.from_user.id
    if user_id not in chat_history:
        chat_history[user_id] = []

    response = ask_chatgpt(message.text)

    if response is None:
        logging.debug("Failed to get a response from GPT")
        bot.reply_to(
            message, "Извините, что-то не так с доступом к GPT. Попробуйте позже. "
        )
    else:
        logging.debug(f"Saving messages for user {user_id}")
        chat_history[user_id].append({"role": "user", "content": message.text})

        chat_history[user_id].append({"role": "assistant", "content": response})

        if len(chat_history[user_id]) > history_limit:
            logging.debug(f"Trimming chat history for user {user_id}")
            chat_history[user_id] = chat_history[user_id][-history_limit:]

        bot.reply_to(message, response, reply_markup=menu_keyboard(["/end", "/help", "/history", "/continue"]))

@bot.message_handler(commands=['continue'])
def continue_function(message):
    user_id = message.from_user.id

    if user_id in chat_history:
        last_resp = chat_history[user_id][-2]['content'] + " " + chat_history[user_id][-1]['content']
        response = ask_chatgpt(last_resp)

        if response is not None:
            logging.debug(f"Saving messages for user {user_id}")
            chat_history[user_id].append({"role": "assistant", "content": response})

            if len(chat_history[user_id]) > history_limit:
                logging.debug(f"Trimming chat history for user {user_id}")
                chat_history[user_id] = chat_history[user_id][-history_limit:]

        bot.send_message(user_id, response)

@bot.message_handler(commands=['end'])
def end(message):
    user_id = message.from_user.id

    logging.debug(f"Trimming chat history for user {user_id}")
    chat_history[user_id] = []

    bot.send_message(user_id, "Текущие решение завершено", reply_markup=menu_keyboard(["/solve_task", "/help", "/history"]))

bot.infinity_polling()
