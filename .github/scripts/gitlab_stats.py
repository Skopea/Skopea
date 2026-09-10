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


def esc(value):
    return html.escape(str(value))


def format_number(value):
    return f"{int(value):,}"


def stat_tile(x, y, width, height, label, value, accent="#fca326"):
    return f"""
    <rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" fill="#161b22" stroke="#30363d" />
    <rect x="{x}" y="{y}" width="4" height="{height}" rx="2" fill="{accent}" />
    <text x="{x + 14}" y="{y + 18}" class="tile-label">{esc(label)}</text>
    <text x="{x + 14}" y="{y + 40}" class="tile-value">{esc(format_number(value))}</text>
    """


# Authenticated GitLab user
user = get("/user")
user_id = user["id"]
username = user["username"]

# Aggregate GitLab counts
counts = get(f"/users/{user_id}/associations_count")
projects = counts.get("projects_count", 0)
merge_requests = counts.get("merge_requests_count", 0)
issues = counts.get("issues_count", 0)

# Recent event-based activity
push_events = 0
commits = 0
active_projects = set()

page = 1

while True:
    events = get(
        f"/users/{urllib.parse.quote(username)}/events?per_page=100&page={page}"
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


svg = f"""<svg width="495" height="230" viewBox="0 0 495 230" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#fc6d26" />
            <stop offset="100%" stop-color="#fca326" />
        </linearGradient>
    </defs>

    <style>
        .title {{
            font: 700 20px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
            fill: #ffffff;
        }}

        .subtitle {{
            font: 500 13px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
            fill: #fca326;
        }}

        .muted {{
            font: 400 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
            fill: #8b949e;
        }}

        .tile-label {{
            font: 500 12px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
            fill: #8b949e;
        }}

        .tile-value {{
            font: 700 20px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
            fill: #ffffff;
        }}
    </style>

    <rect x="0.5" y="0.5" width="494" height="229" rx="12" fill="#0d1117" stroke="#30363d" />
    <rect x="24" y="22" width="110" height="6" rx="3" fill="url(#accentGradient)" />

    <text x="24" y="52" class="title">🦊 GitLab Activity</text>
    <text x="24" y="72" class="subtitle">@{esc(username)}</text>
    <text x="24" y="90" class="muted">Recent activity snapshot generated automatically</text>

    {stat_tile(24, 110, 141, 48, "Projects", projects)}
    {stat_tile(177, 110, 141, 48, "Merge Requests", merge_requests)}
    {stat_tile(330, 110, 141, 48, "Issues", issues)}

    {stat_tile(24, 170, 141, 48, "Recent commits", commits)}
    {stat_tile(177, 170, 141, 48, "Push events", push_events)}
    {stat_tile(330, 170, 141, 48, "Active projects", len(active_projects))}
</svg>
"""

Path("profile").mkdir(exist_ok=True)
Path("profile/gitlab-stats.svg").write_text(svg, encoding="utf-8")

print(f"Generated GitLab stats for @{username}")
print(f"Projects: {projects}")
print(f"Merge Requests: {merge_requests}")
print(f"Issues: {issues}")
print(f"Recent commits: {commits}")
print(f"Push events: {push_events}")
print(f"Active projects: {len(active_projects)}")
