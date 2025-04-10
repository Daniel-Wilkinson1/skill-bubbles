import plotly.express as px

# Sample data
skills_data = {
    "Python": [
        {"name": "Alice", "level": 3},
        {"name": "Bob", "level": 2}
    ],
    "JavaScript": [
        {"name": "Charlie", "level": 1},
        {"name": "Alice", "level": 2}
    ],
}

# Prepare data for Plotly
skills = []
sizes = []
hover_texts = []

for skill, users in skills_data.items():
    total_level = sum(user["level"] for user in users)
    hover_text = "<br>".join([f"{user['name']} (Level {user['level']})" for user in users])

    skills.append(skill)
    sizes.append(total_level * 10)  # multiply for visual effect
    hover_texts.append(hover_text)

fig = px.scatter(
    x=[1] * len(skills), y=[1] * len(skills),
    size=sizes,
    text=skills,
    hover_name=skills,
    hover_data={"Details": hover_texts},
    size_max=100
)

fig.update_traces(textposition='top center', marker=dict(opacity=0.6))
fig.update_layout(showlegend=False, xaxis=dict(showgrid=False, zeroline=False),
                  yaxis=dict(showgrid=False, zeroline=False))
fig.show()
