import requests
from bs4 import BeautifulSoup
import json


def get_github_repos(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        repos_data = []

        for repo_div in soup.find_all('div', class_='col-10 col-lg-9 d-inline-block'):
            repo_info = {}

            repo_name_tag = repo_div.find('a', itemprop='name codeRepository')
            if repo_name_tag:
                repo_info['name'] = repo_name_tag.get_text(strip=True)
            else:
                repo_info['name'] = None

            # Извлечение описания репозитория
            description_tag = repo_div.find('p', itemprop='description')
            if description_tag:
                repo_info['description'] = description_tag.get_text(strip=True)
            else:
                repo_info['description'] = None

            repos_data.append(repo_info)

        return json.dumps(repos_data, ensure_ascii=False, indent=4)
    else:
        return json.dumps({"error": f"Failed to retrieve the page. Status code: {response.status_code}"},
                          ensure_ascii=False, indent=4)
