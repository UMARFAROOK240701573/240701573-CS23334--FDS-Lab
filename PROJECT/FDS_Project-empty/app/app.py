from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import json
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"

API_KEY = "over_here_vro"
MODEL = "gemini-2.5-flash-lite"


def evaluate_goal_progress(goal, skills):
    """Call Google Generative Language to evaluate progress.
    Returns a tuple: (progress_int_or_None, roadmap_list_or_empty, raw_text)
    """
    if not API_KEY:
        return None, [], "Error: API key not set (GLC_API_KEY)."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    headers = {"Content-Type": "application/json"}

    prompt = f"""You are a goal progress evaluator.

Input: a user's goal and their current skills.
Output:
1️⃣ PROGRESS RATING — a number from 1 to 100 representing how close the user is to achieving the goal.
2️⃣ ROADMAP — a concise array of clear next steps in order to reach the goal based on their current skills. Make sure the steps are under 2 words each.

Guidelines:
- Keep your response short and structured exactly as below.
- Do not explain or acknowledge the instructions.
- Focus only on the progress rating and roadmap.

Response Format:
PROGRESS RATING: <number out of 100>
ROADMAP: [Step 1, Step 2, Step 3, ...]
GOAL: {goal}, SKILLS: {skills}"""

    data = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)
        resp.raise_for_status()
        result = resp.json()
        text = result.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
        print(text)
    except Exception as e:
        text = f"Error: {str(e)}"

    # Parse progress
    progress = None
    roadmap = []

    # Try to find PROGRESS RATING: number
    m = re.search(r"PROGRESS RATING:\s*(\d{1,3})", text)
    if m:
        try:
            progress = max(0, min(100, int(m.group(1))))
        except:
            progress = None

    # Try to find ROADMAP: [ ... ]
    m2 = re.search(r"ROADMAP:\s*\[(.*?)\]", text, re.DOTALL)
    if m2:
        # split by comma but keep short items
        items_raw = m2.group(1)
        # remove quotes and extra spaces
        items = [s.strip().strip('"\' )') for s in items_raw.split(',') if s.strip()]
        roadmap = items

    return progress, roadmap, text


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        goal = request.form.get('goal', '').strip()
        skills = request.form.get('skills', '').strip()

        if not goal:
            flash('Please enter a goal.')
            return redirect(url_for('index'))

        progress, roadmap, raw = evaluate_goal_progress(goal, skills)
        return render_template('result.html', goal=goal, skills=skills, progress=progress, roadmap=roadmap, raw=raw)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
