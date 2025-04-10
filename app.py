from flask import Flask, render_template, request, redirect
from markupsafe import Markup
import json
import os
from collections import defaultdict
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)
DATA_FILE = 'data.json'

# Load data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"skills": [], "entries": []}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save data
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route("/", methods=["GET", "POST"])
def index():
    data = load_data()

    if request.method == "POST":
        name = request.form["name"].strip().capitalize()
        existing_skill = request.form.get("existing_skill", "").strip().lower()
        new_skill = request.form.get("new_skill", "").strip().lower()

        # Prefer new skill if provided
        skill = new_skill if new_skill else existing_skill

        if not skill:
            return render_template("index.html", data=data, error="Please select or add a skill.")
        level = int(request.form["level"])

        # Check if user already added this skill
        for entry in data["entries"]:
            if entry["user"] == name and entry["skill"] == skill:
                return render_template("index.html", data=data, error=f"{name} already added '{skill}'.")

        # Add skill to system if it doesn't exist yet
        if skill not in data["skills"]:
            data["skills"].append(skill)

        # Add entry
        data["entries"].append({"user": name, "skill": skill, "level": level})
        save_data(data)
        return redirect("/")

    return render_template("index.html", data=data)

@app.route("/dashboard")
def dashboard():
    data = load_data()
    entries = data["entries"]

    # Aggregate by skill
    skill_map = defaultdict(lambda: {"total": 0, "users": []})
    for entry in entries:
        skill = entry["skill"]
        skill_map[skill]["total"] += entry["level"]
        skill_map[skill]["users"].append(f"{entry['user']} (Level {entry['level']})")

    skills = []
    sizes = []
    hover_texts = []

    for skill, info in skill_map.items():
        skills.append(skill)
        sizes.append(info["total"] * 10)  # scale up
        hover_texts.append("<br>".join(info["users"]))

    fig = px.scatter(
        x=list(range(len(skills))),
        y=[1] * len(skills),
        size=sizes,
        text=skills,
        hover_name=skills,
        custom_data=[hover_texts],
        size_max=100
    )

    fig.update_traces(
        textposition='top center',
        marker=dict(opacity=0.6),
        hovertemplate='<b>%{text}</b><br>%{customdata[0]}<extra></extra>'
    )
    fig.update_layout(
        title="Skill Bubble Chart",
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            ticks='',
            title=None
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            ticks='',
            title=None
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    graph_html = pio.to_html(fig, full_html=False)
    return render_template("dashboard.html", graph_html=Markup(graph_html))

if __name__ == "__main__":
    app.run(debug=True)
