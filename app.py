from flask import Flask, render_template, request, redirect, session, jsonify
import requests
import random
import os

import sqlite3


app = Flask(__name__)
app.secret_key = 'your-secret-key'  # for sessions

API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "http://api.weatherapi.com/v1/current.json?"
LEADERBOARD_FILE = "leaderboard.txt"

AMERICAN_CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington",
    "Boston", "El Paso", "Detroit", "Nashville", "Portland",
    "Memphis", "Oklahoma City", "Las Vegas", "Louisville", "Baltimore",
    "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento",
    "Mesa", "Kansas City", "Atlanta", "Long Beach", "Colorado Springs",
    "Raleigh", "Miami", "Virginia Beach", "Omaha", "Oakland",
    "Minneapolis", "Tulsa", "Arlington", "Tampa", "New Orleans",
]

WORLDWIDE_CITIES = [
    "New York", "Los Angeles", "San Francisco", "Cincinnati", "Las Vegas", "Orlando", "Tampa",
    "London", "Paris", "Tokyo", "Sydney", "Moscow", "Rio de Janeiro", "Cape Town",
    "Toronto", "Dubai", "Beijing", "Mumbai", "Mexico City", "Berlin", "Buenos Aires",
    "Seoul", "Madrid", "Rome", "Bangkok", "Istanbul", "Singapore", "Hong Kong",
    "Cairo", "Lagos", "Jakarta", "Melbourne", "Athens", "Vancouver", "Lisbon",
    "Kuala Lumpur", "Stockholm", "Prague", "Helsinki", "Amsterdam", "Warsaw",
    "Lima", "Bogota", "Santiago", "Casablanca", "Budapest", "Dublin", "Oslo",
    "Havana", "Reykjavik", "Brussels", "Manila", "Kiev", "Tehran", "Jerusalem",
    "Baghdad", "Karachi"
]

def get_weather(city):
    url = BASE_URL + f"key={API_KEY}&q={city}&aqi=no"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['current']['temp_f']
        desc = data['current']['condition']['text']
        time = data['location']['localtime']
        country = data['location']['country']
        state = data['location'].get('region', '')
        return temp, desc, time, state, country
    return None, None, None, None, None

DB_FILE = 'leaderboard.db'

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

    # Check if user exists
    cursor.execute("SELECT score FROM leaderboard WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        # Update score only if it's higher
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
    city = session.get('city')
    score = session.get('score', 0)
    temp, desc, localtime, state, country = get_weather(city)

    if request.method == "POST":
        guess = float(request.form.get("guess", 0))
        difference = abs(guess - temp)
        if difference <= 5:
            # Correct enough
            score += 1
            session['score'] = score
            # Pick new city
            cities = AMERICAN_CITIES if session.get("difficulty") == "normal" else WORLDWIDE_CITIES
            session['city'] = random.choice(cities)
            return redirect("/game")
        else:
            # Game over
            session['final_temp'] = temp
            session['final_desc'] = desc
            session['localtime'] = localtime
            return redirect("/gameover")

    return render_template("game.html", city=city, score=score, localtime=localtime)

@app.route("/gameover", methods=["GET", "POST"])
def gameover():
    if request.method == "POST":
        name = request.form.get("name", "Anonymous")
        score = session.get('score', 0)
        save_leaderboard(name, score)
        return redirect("/")

    return render_template("gameover.html",
                           city=session.get("city"),
                           score=session.get("score"),
                           temp=session.get("final_temp"),
                           desc=session.get("final_desc"),
                           localtime=session.get("localtime"),
                           leaderboard=load_leaderboard())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
