import re
import requests

def parse_github_url(url):
    match = re.match(r"https://github.com/([^/]+)/([^/]+)", url)
    if not match:
        raise ValueError("Invalid GitHub URL")
    return match.group(1), match.group(2)


def get_workflow_files(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/.github/workflows"
    res = requests.get(url)

    if res.status_code != 200:
        raise Exception(f"Failed to fetch workflows: {res.status_code}")

    files = res.json()

    return [f for f in files if f["name"].endswith((".yml", ".yaml"))]