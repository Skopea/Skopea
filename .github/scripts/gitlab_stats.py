import html
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


TOKEN = os.environ["GITLAB_TOKEN"]
BASE_URL = "https://gitlab.com/api/v4"


def get(path):
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={
            "PRIVATE-TOKEN": TOKEN,
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


# Get authenticated GitLab account
user = get("/user")
user_id = user["id"]
username = user["username"]

# GitLab provides aggregate counts for the authenticated user
counts = get(f"/users/{user_id}/associations_count")

projects = counts.get("projects_count", 0)
merge_requests = counts.get("merge_requests_count", 0)
issues = counts.get("issues_count", 0)

# Count push activity from GitLab's contribution-event history.
push_events = 0
commits = 0
active_projects = set()

page = 1

while True:
    events = get(
        f"/users/{urllib.parse.quote(username)}/events"
        f"?per_page=100&page={page}"
    )

    if not events:
        break

    for event in events:
        push_data = event.get("push_data")

        if push_data:
            push_events += 1
            commits += push_data.get("commit_count", 0)

            project_id = event.get("project_id")
            if project_id:
                active_projects.add(project_id)

    if len(events) < 100:
        break

    page += 1


def esc(value):
    return html.escape(str(value))


svg = f"""<svg width="495" height="195" viewBox="0 0 495 195"
xmlns="http://www.w3.org/2000/svg">

<style>
    .title {{
        font: 600 17px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
        fill: #ffffff;
    }}

    .label {{
        font: 400 14px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
        fill: #c9d1d9;
    }}

    .value {{
        font: 600 14px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
        fill: #ffffff;
    }}

    .username {{
        font: 400 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
        fill: #8b949e;
    }}
</style>

<rect
    width="494"
    height="194"
    x="0.5"
    y="0.5"
    rx="6"
    fill="#0d1117"
    stroke="#30363d"
/>

<text x="25" y="35" class="title">🦊 GitLab Stats</text>
<text x="25" y="55" class="username">@{esc(username)}</text>

<text x="25" y="88" class="label">Projects</text>
<text x="220" y="88" class="value">{projects}</text>

<text x="25" y="112" class="label">Merge Requests</text>
<text x="220" y="112" class="value">{merge_requests}</text>

<text x="25" y="136" class="label">Issues</text>
<text x="220" y="136" class="value">{issues}</text>

<text x="280" y="88" class="label">Recent commits</text>
<text x="450" y="88" text-anchor="end" class="value">{commits}</text>

<text x="280" y="112" class="label">Push events</text>
<text x="450" y="112" text-anchor="end" class="value">{push_events}</text>

<text x="280" y="136" class="label">Active projects</text>
<text x="450" y="136" text-anchor="end" class="value">{len(active_projects)}</text>

</svg>
"""

Path("profile").mkdir(exist_ok=True)
Path("profile/gitlab-stats.svg").write_text(svg, encoding="utf-8")

print(f"Generated GitLab stats for @{username}")
print(f"Projects: {projects}")
print(f"Merge Requests: {merge_requests}")
print(f"Issues: {issues}")
print(f"Recent commits: {commits}")
