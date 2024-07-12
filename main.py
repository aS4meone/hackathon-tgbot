import telebot
import os
import pandas as pd
import json

from app.utils.github_parser import get_github_repos
from app.utils.llm import reject_or_not, change_prompt, analyze_github_repo

API_TOKEN = '6937911252:AAFGQ9ZooSgXALNXmCqV5U4RgQTEeJqhS-4'

bot = telebot.TeleBot(API_TOKEN)

user_state = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me an Excel file to process.")


@bot.message_handler(commands=['first'])
def handle_first_command(message):
    bot.reply_to(message, "Отправьте файл для чегото там.")
    user_state[message.chat.id] = 'awaiting_first_file'


@bot.message_handler(commands=['mistake'])
def handle_mistake_command(message):
    bot.reply_to(message, "Введите номер строки.")
    user_state[message.chat.id] = 'awaiting_row_number'


@bot.message_handler(commands=['github'])
def handle_github_command(message):
    bot.reply_to(message, "Отправьте Excel файл с репозиториями GitHub.")
    user_state[message.chat.id] = 'awaiting_github_file'


@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == 'awaiting_row_number')
def handle_row_number(message):
    try:
        row_number = int(message.text)
        user_state[message.chat.id] = {'state': 'awaiting_message', 'row_number': row_number}
        bot.reply_to(message, "Введите сообщение, почему респонз неверный.")
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введите корректный номер строки.")


@bot.message_handler(
    func=lambda message: isinstance(user_state.get(message.chat.id), dict) and user_state[message.chat.id].get(
        'state') == 'awaiting_message')
def handle_mistake_message(message):
    row_number = user_state[message.chat.id]['row_number']
    mistake_message = message.text
    change_prompt(row_number, mistake_message)
    bot.reply_to(message, "Успешно запомнили ваши слова!")
    user_state[message.chat.id] = None


@bot.message_handler(content_types=['document'])
def handle_document(message):
    if user_state.get(message.chat.id) == 'awaiting_first_file':
        handle_first_file(message)
    elif user_state.get(message.chat.id) == 'awaiting_github_file':
        handle_github_file(message)
    else:
        bot.reply_to(message, "Пожалуйста, сначала отправьте команду /first или /github.")


def handle_first_file(message):
    try:
        bot.reply_to(message, "Файл принят, ожидайте.")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_path = os.path.join(message.document.file_name)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Process the file
        excel_data = pd.read_excel(file_path)
        data = excel_data.to_dict(orient='records')

        count = 0
        accepted_list = [None] * len(data)
        reasons_list = [None] * len(data)

        for idx, item in enumerate(data):
            print(count, "iteration")
            count += 1
            json_object = json.dumps(item, ensure_ascii=False, indent=4)
            github_link = item.get("Ссылка на GitHub", None)
            if not github_link:
                continue
            try:
                github = get_github_repos(github_link)
            except Exception as e:
                github = "error"
            json_save = reject_or_not(json_object, github)

            json_data = json.loads(json_save)

            accepted_list[idx] = json_data.get("accepted", None)
            reasons_list[idx] = json_data.get("reasons", None)

        excel_data["Accepted"] = accepted_list
        excel_data["Reasons"] = reasons_list

        updated_file_path = os.path.join('Updated_' + message.document.file_name)
        excel_data.to_excel(updated_file_path, index=False)

        with open(updated_file_path, 'rb') as updated_file:
            bot.send_document(message.chat.id, updated_file)

        bot.reply_to(message, "Файл обновленный.")
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

    user_state[message.chat.id] = None


def handle_github_file(message):
    try:
        bot.reply_to(message, "Файл принят, ожидайте.")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        file_path = os.path.join(message.document.file_name)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Process the file
        excel_data = pd.read_excel(file_path)
        data = excel_data.to_dict(orient='records')

        results = []

        for idx, item in enumerate(data):
            github_link = item.get("repositories", None)
            print(github_link)
            if not github_link:
                continue
            count_similar = analyze_github_repo(github_link)
            if count_similar > 0:
                results.append(github_link)

        if results:
            bot.reply_to(message,
                         f"Найдены репозитории с похожим кодом:\n{json.dumps(results, ensure_ascii=False, indent=4)}")
        else:
            bot.reply_to(message, "Проверка пройдена, похожий код не найден.")

        os.remove(file_path)
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {e}")

    user_state[message.chat.id] = None


bot.polling()
