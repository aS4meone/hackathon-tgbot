import base64
import requests
import time

from typing import List

GITHUB_TOKEN = 'GITHUBTOKEN'
GITHUB_API_URL = 'https://api.github.com/search/code'


def get_repo_contents(owner, repo, path="", token=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    contents = response.json()
    return contents


def list_files_and_folders(owner, repo, path="", token="", file_paths=None):
    if file_paths is None:
        file_paths = []
    contents = get_repo_contents(owner, repo, path, token)
    for item in contents:
        if item['type'] == 'file':
            file_paths.append(item['path'])
        elif item['type'] == 'dir':
            list_files_and_folders(owner, repo, item['path'], token, file_paths)

    return file_paths


def get_file_content(owner, repo, path, token=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    content = response.json()
    if content['type'] == 'file':
        file_content = base64.b64decode(content['content']).decode('utf-8')
        return file_content
    else:
        raise ValueError(f"{path} is not a file")


HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}


def split_code(code: str, chunk_size: int = 100) -> List[str]:
    return [code[i:i + chunk_size] for i in range(0, len(code), chunk_size)]


count = 0


def search_github_code(query: str) -> dict:
    params = {
        'q': query,
        'per_page': 5  # Установите нужное количество результатов на страницу
    }
    response = requests.get(GITHUB_API_URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None


def find_similar_code(owner, code: str, chunk_size: int = 255, sleep_time: int = 3):
    chunks = split_code(code, chunk_size)
    results = []

    for chunk in chunks:
        result = search_github_code(chunk)

        if result:
            if result["items"][0]["repository"]["owner"]["login"] != owner:
                results.append(result)
        time.sleep(sleep_time)  # Задержка между запросами

    return results

# # Пример использования:
# input_code = """
# import mongoose from 'mongoose';
# const connectDB = async () => {
#     try {
#         await mongoose.connect(process.env.MONGODB_URL || 'mongodb://localhost:27017/lecture1');
#         console.log('MongoDB connected...');
#     } catch (err:any) {
#         console.error(err.message);
#         process.exit(1);
#     }
# };
# export default connectDB;
# """
#
# similar_code_results = find_similar_code(input_code)
# print(len(similar_code_results))
#
# for result in similar_code_results:
#     print(result)
