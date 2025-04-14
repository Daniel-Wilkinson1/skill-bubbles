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

    # Prepare data for heatmap
    heatmap_data = defaultdict(lambda: {"Theoretical": [], "Practical": [], "Hover_Theoretical": [], "Hover_Practical": []})

    for entry in entries:
        skill = entry["skill"]
        user = entry["user"]
        if entry.get("knowledge"):
            level = level_map_knowledge.get(entry["knowledge"], 0)
            heatmap_data[skill]["Theoretical"].append(level)
            heatmap_data[skill]["Hover_Theoretical"].append(f"{user} ({entry['knowledge']})")
        if entry.get("experience"):
            level = level_map_experience.get(entry["experience"], 0)
            heatmap_data[skill]["Practical"].append(level)
            heatmap_data[skill]["Hover_Practical"].append(f"{user} ({entry['experience']})")

    records = []
    for skill, values in heatmap_data.items():
        for kind, levels_key, hover_key in [("Theoretical", "Theoretical", "Hover_Theoretical"), ("Practical", "Practical", "Hover_Practical")]:
            levels = values[levels_key]
            hovers = values[hover_key]
            if levels:
                avg_score = sum(levels) / len(levels)
                hover_text = "<br>".join(hovers)
                records.append({
                    "Skill": skill.capitalize(),
                    "Type": kind,
                    "Score": round(avg_score, 1),
                    "Hover": hover_text
                })

    df = pd.DataFrame(records)
    pivot_df = df.pivot(index="Type", columns="Skill", values="Score")
    hover_df = df.pivot(index="Type", columns="Skill", values="Hover")

    fig = px.imshow(
        pivot_df,
        color_continuous_scale="Blues",
        labels=dict(x="Skill", y="Type", color="Skill Level"),
        aspect="auto"
    )

    # Add hover info manually and format scores
    for i, row in enumerate(pivot_df.index):
        for j, col in enumerate(pivot_df.columns):
            fig.data[0].text[i][j] = f"{pivot_df.loc[row, col]:.1f}" if not pd.isna(pivot_df.loc[row, col]) else ""
            hovertext = hover_df.at[row, col] if (row in hover_df.index and col in hover_df.columns) else ""
            fig.data[0].hovertext[i][j] = hovertext

    fig.update_layout(
        title="Skill Heatmap: Theoretical vs Practical",
        margin=dict(l=40, r=40, t=60, b=40),
        height=500,
        xaxis=dict(showticklabels=True, title=None),
        yaxis=dict(showticklabels=True, title=None),
        showlegend=False
    )

    graph_html = pio.to_html(fig, full_html=False)
    return render_template("dashboard.html", graph_html=Markup(graph_html))

if __name__ == "__main__":
    app.run(debug=True)
