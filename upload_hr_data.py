import pandas as pd
import json

# Load Excel file
df = pd.read_excel("hr_skills_template.xlsx")

# Build initial skill entries with no ratings yet
entries = []
for _, row in df.iterrows():
    entries.append({
        "user": row["name"].strip().capitalize(),
        "skill": row["skill"].strip().lower(),
        "knowledge": None,
        "experience": None
    })

# Create a global skill list from the unique values in the Excel sheet
skills = sorted(list(set(df["skill"].str.lower())))

# Save to data.json
data = {
    "skills": skills,
    "entries": entries
}

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ HR data imported into data.json")
