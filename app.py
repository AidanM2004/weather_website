from flask import Flask, render_template, request, redirect, session, jsonify
import requests
import random
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # for sessions

API_KEY = '4240cecffcff46c2a96202231251908'
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
        return temp, desc, time
    return None, None, None

def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return {}
    with open(LEADERBOARD_FILE, 'r') as f:
        lines = f.readlines()
    lb = {}
    for line in lines:
        name, score = line.strip().split(":")
        lb[name] = int(score)
    return lb

def save_leaderboard(lb):
    with open(LEADERBOARD_FILE, 'w') as f:
        for name, score in sorted(lb.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{name}:{score}\n")

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
    temp, desc, localtime = get_weather(city)

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
        lb = load_leaderboard()
        if name in lb:
            lb[name] = max(score, lb[name])
        else:
            lb[name] = score
        save_leaderboard(lb)
        return redirect("/")

    return render_template("gameover.html",
                           city=session.get("city"),
                           score=session.get("score"),
                           temp=session.get("final_temp"),
                           desc=session.get("final_desc"),
                           localtime=session.get("localtime"),
                           leaderboard=sorted(load_leaderboard().items(), key=lambda x: x[1], reverse=True)[:5])

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=10000)
