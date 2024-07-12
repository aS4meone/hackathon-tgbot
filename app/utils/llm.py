import json

from openai import OpenAI
from dotenv import load_dotenv
from os import getenv

from app.utils.github_feedback import list_files_and_folders, get_file_content, find_similar_code
from app.utils.json_object_by_string import get_json_object_by_row

load_dotenv()

token = "GITHUB!!!!"  # Ваш персональный токен GitHub (если требуется)

client = OpenAI(api_key=getenv("API_KEY"))

count_similar = 0


def reject_or_not(json, github):
    output = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": f"GitHub repos - {github}. JSON of an Applicant - {json}"}
        ]
    )
    return output.choices[0].message.content


with open('prompt.txt', 'r', encoding='utf-8') as file:
    sys_prompt = file.read()


def change_prompt(number, message):
    global sys_prompt
    print("fa")
    json_object = get_json_object_by_row("Updated_Hackathon nf2024 incubator.xlsx", row_number=number)
    output = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "json_object"},
        temperature=0.5,
        messages=[
            {"role": "system", "content": """Ты профессиональный промпт инженер. Тебе скидывают промпт, который по какой-либо причине сработал неправильно, а также данные, на которых произошла ошибка. Ты учитываешь правки пользователя и ВОЗВРАЩАЕШЬ ОДНУ СТРОКУ ТО, ЧТО НУЖНО ДОБАВИТЬ В ПРОМПТ!
            ОТВЕТ НУЖНО ВЕРНУТЬ В ФОРМАТЕ {"add": "prompt"}!!!
            """},
            {"role": "user",
             "content": f"""Текущий промпт - "{sys_prompt}". Объект с ошибкой - {json_object}. Промпт нужно поменять потому что - {message}. Жду новый промпт коротко и понятно"""}
        ]
    )
    addition = output.choices[0].message.content

    addition_dict = json.loads(addition)
    add_value = addition_dict.get("add", "")

    sys_prompt = sys_prompt + add_value

    with open('prompt.txt', 'a', encoding='utf-8') as file:
        file.write(add_value + '\n')

    return addition


def extract_github_info(url):
    if url.startswith("https://"):
        url = url[len("https://"):]
    elif url.startswith("http://"):
        url = url[len("http://"):]

    parts = url.split('/')
    if len(parts) >= 3:
        owner = parts[1]
        repo_name = parts[2]
        return owner, repo_name
    else:
        raise ValueError("Invalid GitHub URL format")


def is_plagiated(filee):
    output = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": """
            Твоя задача проверить код на плагиат и на AI Generated. Используй проценты и ответ предоставляй в них. В json всего 3 поля - ai_generated, plagiarism значения просто int, но максимум 100. Поле "reason" для причин почему ты так оценил.
            поле ai_generated 100 означает, что код сгенерировала нейросеть. если в коде просто присутствуют запросы на openai api или подобные api, это не значит, что код ai generated.
                """},
            {"role": "user",
             "content": f"""{filee}"""}
        ]
    )

    plagiated = output.choices[0].message.content
    plagiated_dict = json.loads(plagiated)

    ai_generated = plagiated_dict["ai_generated"]
    plagiarism = plagiated_dict["plagiarism"]
    reason = plagiated_dict["reason"]

    return ai_generated, plagiarism, reason


def analyze_github_repo(url):
    global count_similar
    print("c")
    owner, repo = extract_github_info(url)
    file_paths = list_files_and_folders(owner, repo, "", token)
    output = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": """
            Твоя задача - проверить в каких файлах из репозитория github наиболее лучше взять код, чтобы проверить его на плагиат и AI generated.
            json нужно вернуть в формате {"paths": []} МАКСИМУМ 3 ФАЙЛА
                """},
            {"role": "user",
             "content": f"""{file_paths}"""}
        ]
    )
    addition = output.choices[0].message.content
    print(addition)
    addition_dict = json.loads(addition)

    addition = addition_dict["paths"]
    print(addition)

    results = []

    for path in addition:
        try:
            file_content = get_file_content(owner, repo, path, token)
            plagiated_result = is_plagiated(file_content)
            similar_code_results = find_similar_code(owner, file_content)

            for result in similar_code_results:
                print(result)
            count_similar += len(similar_code_results)
            results.append(plagiated_result)
        except Exception as e:
            print(f"An error occurred while processing {path}: {e}")
            results.append(None)

    return count_similar
