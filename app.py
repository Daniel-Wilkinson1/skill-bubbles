from flask import Flask, render_template, request, redirect
from markupsafe import Markup
import json
import os
from collections import defaultdict
from datetime import datetime
import pandas as pd
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
        name = request.form.get("name", "").strip().capitalize()
        new_skills = request.form.getlist("new_skill")
        knowledges = request.form.getlist("knowledge")
        experiences = request.form.getlist("experience")
        timestamp = datetime.now().isoformat()

        for skill, knowledge, experience in zip(new_skills, knowledges, experiences):
            skill = skill.strip().lower()
            if skill:
                if skill not in data["skills"]:
                    data["skills"].append(skill)
                data["entries"].append({
                    "user": name,
                    "skill": skill,
                    "knowledge": knowledge,
                    "experience": experience,
                    "timestamp": timestamp
                })

        save_data(data)
        return redirect("/")

    return render_template("index.html", data=data)

@app.route("/dashboard")
def dashboard():
    data = load_data()
    entries = data["entries"]

    if not entries:
        return "<h2>No skills added yet. <a href='/'>Go back</a></h2>"

    # Keep only the latest entry per user per skill
    latest_entries = {}
    for entry in entries:
        key = (entry["user"], entry["skill"])
        if key not in latest_entries or entry.get("timestamp", "") > latest_entries[key].get("timestamp", ""):
            latest_entries[key] = entry
    entries = list(latest_entries.values())

    level_map_knowledge = {"beginner": 1, "intermediate": 2, "expert": 3}
    level_map_experience = {"1-2 years": 1, "3-5 years": 2, "5+ years": 3}

    skill_to_x = {skill: i for i, skill in enumerate(sorted(set(entry["skill"] for entry in entries)))}

    x = []
    y = []
    sizes = []
    texts = []
    custom_data = []
    colors = []

    for entry in entries:
        skill = entry["skill"]
        user = entry["user"]
        knowledge = entry.get("knowledge")
        experience = entry.get("experience")

        if knowledge:
            score = level_map_knowledge.get(knowledge, 0)
            x.append(skill_to_x[skill])
            y.append(2)
            sizes.append(score * 30)
            texts.append("")
            custom_data.append(f"{skill}<br>{user} (Knowledge: {knowledge})")
            colors.append("Theoretical")

        if experience:
            score = level_map_experience.get(experience, 0)
            x.append(skill_to_x[skill])
            y.append(1)
            sizes.append(score * 30)
            texts.append("")
            custom_data.append(f"{skill}<br>{user} (Experience: {experience})")
            colors.append("Practical")

    df = pd.DataFrame({
        "x": x,
        "y": y,
        "size": sizes,
        "skill": texts,
        "hover": custom_data,
        "type": colors
    })

    fig = px.scatter(
        df,
        x="x",
        y="y",
        size="size",
        text="skill",
        custom_data=["hover"],
        color="type",
        size_max=100,
        color_discrete_map={"Theoretical": "blue", "Practical": "orange"}
    )
    fig.update_traces(
        textposition='top center',
        marker=dict(opacity=0.8),
        hovertemplate='%{customdata[0]}<extra></extra>'
    )
    fig.update_layout(
        title="Skill Bubbles: Theoretical (Top) vs Practical (Bottom)",
        showlegend=False,
        xaxis=dict(
            tickvals=list(skill_to_x.values()),
            ticktext=[skill.capitalize() for skill in skill_to_x.keys()],
            showgrid=False, zeroline=False, showticklabels=True, title=None
        ),
        yaxis=dict(
            tickvals=[1, 2],
            ticktext=["Practical", "Theoretical"],
            showgrid=False, zeroline=False, title=None
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=600
    )

    graph_html = pio.to_html(fig, full_html=False)
    return render_template("dashboard.html", graph_html=Markup(graph_html))

if __name__ == "__main__":
    app.run(debug=True)
