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
    name = request.form.get("name", "").strip().capitalize()

    # If POST, process form submission
    if request.method == "POST" and "submit_levels" in request.form:
        for entry in data["entries"]:
            if entry["user"] == name:
                skill = entry["skill"]
                entry["knowledge"] = request.form.get(f"knowledge_{skill}")
                entry["experience"] = request.form.get(f"experience_{skill}")

        # Handle new skill
        new_skill = request.form.get("new_skill", "").strip().lower()
        if new_skill:
            knowledge = request.form.get("knowledge_new")
            experience = request.form.get("experience_new")
            if new_skill not in data["skills"]:
                data["skills"].append(new_skill)
            data["entries"].append({
                "user": name,
                "skill": new_skill,
                "knowledge": knowledge,
                "experience": experience
            })
        save_data(data)
        return redirect("/")

    # Filter skills assigned to this user
    user_skills = [e for e in data["entries"] if e["user"] == name]

    return render_template("index.html", data=data, user=name, user_skills=user_skills)

@app.route("/dashboard")
def dashboard():
    data = load_data()
    entries = data["entries"]

    if not entries:
        return "<h2>No skills added yet. <a href='/'>Go back</a></h2>"

    def prepare_data(field):
        skill_map = defaultdict(lambda: {"total": 0, "users": []})
        for entry in entries:
            if entry[field]:
                level_map = {"beginner": 1, "intermediate": 2, "expert": 3}
                skill_map[entry["skill"]]["total"] += level_map.get(entry[field], 0)
                skill_map[entry["skill"]]["users"].append(f"{entry['user']} ({entry[field].capitalize()})")
        skills = []
        sizes = []
        hover_texts = []
        for skill, info in skill_map.items():
            skills.append(skill)
            sizes.append(info["total"] * 10)
            hover_texts.append("<br>".join(info["users"]))
        return skills, sizes, hover_texts

    skills_k, sizes_k, hovers_k = prepare_data("knowledge")
    skills_e, sizes_e, hovers_e = prepare_data("experience")

    fig_k = px.scatter(
        x=list(range(len(skills_k))), y=[2]*len(skills_k),
        size=sizes_k, text=skills_k, custom_data=[hovers_k],
        size_max=100
    )
    fig_k.update_traces(
        textposition='top center',
        marker=dict(opacity=0.6),
        hovertemplate='%{customdata[0]}<extra></extra>'
    )

    fig_e = px.scatter(
        x=list(range(len(skills_e))), y=[1]*len(skills_e),
        size=sizes_e, text=skills_e, custom_data=[hovers_e],
        size_max=100
    )
    fig_e.update_traces(
        textposition='top center',
        marker=dict(opacity=0.6),
        hovertemplate='%{customdata[0]}<extra></extra>'
    )

    fig_k.add_trace(fig_e.data[0])
    fig_k.update_layout(
        title="Skill Bubbles: Theoretical (Top) vs Practical (Bottom)",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=None),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=None),
        margin=dict(l=40, r=40, t=60, b=40),
        height=600
    )

    graph_html = pio.to_html(fig_k, full_html=False)
    return render_template("dashboard.html", graph_html=Markup(graph_html))
