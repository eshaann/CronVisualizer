import re
import requests
import yaml
import time_helpers


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

def fetch_yaml(download_url):
    res = requests.get(download_url)
    if res.status_code != 200:
        raise Exception("Failed to download file")
    return res.text

def normalize_on_field(on_field):
    if isinstance(on_field, str):
        return {on_field: None}
    elif isinstance(on_field, list):
        return {item: None for item in on_field}
    elif isinstance(on_field, dict):
        return on_field
    return {}

def extract_cron(on_field):
    schedules = []

    if "schedule" in on_field:
        for item in on_field["schedule"]:
            cron_expr = item.get("cron")
            if cron_expr:
                schedules.append(cron_expr)

    return schedules

def extract_dependencies(on_field):
    deps = []

    if "workflow_run" in on_field:
        workflows = on_field["workflow_run"].get("workflows", [])

        if isinstance(workflows, str):
            workflows = [workflows]

        deps.extend(workflows)

    return deps

def parse_repo(url):
    owner, repo = parse_github_url(url)

    files = get_workflow_files(owner, repo)

    parsed_workflows = []

    for f in files:
        content = fetch_yaml(f["download_url"])
        data = yaml.safe_load(content) or {}

        name = data.get("name", f["name"])

        on_field_raw = data.get("on") or data.get(True) or {}
        on_field = normalize_on_field(on_field_raw)

        cron_schedules = extract_cron(on_field)
        dependencies = extract_dependencies(on_field)

        parsed_workflows.append({
            "name": name,
            "file": f["name"],
            "cron": cron_schedules,
            "depends_on": dependencies
        })

    return parsed_workflows


if __name__ == "__main__":
    url = "https://github.com/eshaann/CronVisualizer"

    workflows = parse_repo(url)

    from pprint import pprint
    pprint(workflows)

    run_map = time_helpers.build_run_map(workflows)
    run_map = time_helpers.propagate_dependencies(workflows, run_map)

    events = time_helpers.build_events(run_map)
    print(len(events))
    for e in events:
        print(f"{e['time']} → {e['workflow']}")