from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv
load_dotenv()

import requests
import random
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # replace with a strong secret key!

API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "http://api.weatherapi.com/v1/current.json?"

AMERICAN_CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
    "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville",
    "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis", "Seattle",
    "Denver", "Washington", "Boston", "El Paso", "Detroit", "Nashville", "Portland",
    "Memphis", "Oklahoma City", "Las Vegas", "Louisville", "Baltimore", "Milwaukee",
    "Albuquerque", "Tucson", "Fresno", "Sacramento", "Mesa", "Kansas City", "Atlanta",
    "Long Beach", "Colorado Springs", "Raleigh", "Miami", "Virginia Beach", "Omaha",
    "Oakland", "Minneapolis", "Tulsa", "Arlington", "Tampa", "New Orleans",
]

WORLDWIDE_CITIES = [
    "New York", "Los Angeles", "San Francisco", "Cincinnati", "Las Vegas", "Orlando",
    "Tampa", "London", "Paris", "Tokyo", "Sydney", "Moscow", "Rio de Janeiro", "Cape Town",
    "Toronto", "Dubai", "Beijing", "Mumbai", "Mexico City", "Berlin", "Buenos Aires",
    "Seoul", "Madrid", "Rome", "Bangkok", "Istanbul", "Singapore", "Hong Kong", "Cairo",
    "Lagos", "Jakarta", "Melbourne", "Athens", "Vancouver", "Lisbon", "Kuala Lumpur",
    "Stockholm", "Prague", "Helsinki", "Amsterdam", "Warsaw", "Lima", "Bogota",
    "Santiago", "Casablanca", "Budapest", "Dublin", "Oslo", "Havana", "Reykjavik",
    "Brussels", "Manila", "Kiev", "Tehran", "Jerusalem", "Baghdad", "Karachi"
]

DB_FILE = 'leaderboard.db'

def get_weather(city):
    if not API_KEY:
        print("ERROR: WEATHER_API_KEY environment variable is not set.")
        return None, None, None, None, None

    url = BASE_URL + f"key={API_KEY}&q={city}&aqi=no"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if response.status_code != 200:
            print(f"API error: {data}")
            return None, None, None, None, None

        temp = data['current']['temp_f']
        desc = data['current']['condition']['text']
        time = data['location']['localtime']
        country = data['location']['country']
        state = data['location'].get('region', '')
        return temp, desc, time, state, country

    except Exception as e:
        print(f"Error getting weather: {e}")
        return None, None, None, None, None

def load_leaderboard(limit=5):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT ?", (limit,))
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def save_leaderboard(name, score):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # We do NOT update if score is lower or equal; just keep the highest score per name
    cursor.execute("SELECT score FROM leaderboard WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        if score > row[0]:
            cursor.execute("UPDATE leaderboard SET score = ? WHERE name = ?", (score, name))
    else:
        cursor.execute("INSERT INTO leaderboard (name, score) VALUES (?, ?)", (name, score))

    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        difficulty = request.form.get("difficulty", "normal")
        cities = AMERICAN_CITIES if difficulty == "normal" else WORLDWIDE_CITIES
        city = random.choice(cities)
        session['difficulty'] = difficulty
        session['score'] = 0
        session['city'] = city
        return redirect("/game")
    return render_template("index.html")

@app.route("/game", methods=["GET", "POST"])
def game():
    if 'city' not in session or 'score' not in session:
        return redirect("/")

    city = session['city']
    score = session['score']
    temp, desc, localtime, state, country = get_weather(city)

    if request.method == "POST":
        guess = float(request.form.get("guess", 0))
        difference = abs(guess - temp)
        if difference <= 5:
            score += 1
            session['score'] = score
            cities = AMERICAN_CITIES if session.get("difficulty") == "normal" else WORLDWIDE_CITIES
            session['city'] = random.choice(cities)
            return redirect("/game")
        else:
            session['final_temp'] = temp
            session['final_desc'] = desc
            session['localtime'] = localtime
            session['country'] = country
            return redirect("/gameover")

    return render_template("game.html", city=city, state=state, country=country, score=score, localtime=localtime)

@app.route("/gameover", methods=["GET", "POST"])
def gameover():
    if request.method == "POST":
        name = request.form.get("name", "Anonymous")
        score = session.get('score', 0)
        save_leaderboard(name, score)
        return redirect("/")

    final_data = {
        "city": session.get("city", "Unknown City"),
        "country": session.get("country", "Unknown Country"),
        "score": session.get("score", 0),
        "temp": session.get("final_temp", "N/A"),
        "desc": session.get("final_desc", "N/A"),
        "localtime": session.get("localtime", "N/A"),
        "leaderboard": load_leaderboard()
    }

    session.clear()

    return render_template("gameover.html", **final_data)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
