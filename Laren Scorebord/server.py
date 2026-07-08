import json
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)


# Load season player database
with open("players.json") as f:
    players = json.load(f)


state = {
    "home": 0,
    "away": 0,

    "time": "00:00",
    "extra": 0,

    "homeLogo": "/static/laren.png",
    "awayLogo": "",
    "sponsor": "",

    "homeName": "SV Laren '99",
    "awayName": "Tegenstander",

    "running": False,
    "seconds": 0,
    "half": 1,

    "lineup": [],
    "subs": [],
    "lineupVersion": 0,

    "goals": [],

    "screen": "display"
}


def timer_loop():

    while True:

        socketio.sleep(1)

        if state["running"]:

            state["seconds"] += 1

            total = state["seconds"]

            if state["half"] == 1:
                limit = 45 * 60
            else:
                limit = 90 * 60


            if total <= limit:

                m = total // 60
                s = total % 60

                state["time"] = f"{m:02}:{s:02}"
                state["extra"] = 0

            else:

                extra = total - limit

                state["time"] = f"{limit//60:02}:00"

                state["extra"] = (
                    f"{extra//60:02}:{extra%60:02}"
                )


            socketio.emit("update", state)



@app.route("/display")
def display():
    return render_template("display.html")


@app.route("/control")
def control():
    return render_template("control.html")


@app.route("/lineup")
def lineup():
    return render_template("lineup.html")



@socketio.on("connect")
def connect():

    emit("update", state)



@socketio.on("get_players")
def get_players():

    emit("players", players)



@socketio.on("update")
def update(data):

    state.update(data)

    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("save_lineup")
def save_lineup(data):

    state["lineup"] = data["lineup"]
    state["subs"] = data["subs"]

    # Increase version only when lineup changes
    state["lineupVersion"] += 1

    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("show_lineup")
def show_lineup():

    state["screen"] = "lineup"

    # Force a fresh animation when opening lineup screen
    state["lineupVersion"] += 1

    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("show_display")
def show_display():

    state["screen"] = "display"

    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("goal_home")
def goal_home(data):

    player = data["player"]

    total_sec = state["seconds"]


    # Determine match minute
    if state["half"] == 1:

        if total_sec >= 45 * 60:
            minute = "45+"

        else:
            minute = str((total_sec // 60) + 1)


    else:

        if total_sec >= 90 * 60:
            minute = "90+"

        else:
            minute = str((total_sec // 60) + 1)



    state["home"] += 1


    state["goals"].append({

        "player": player,

        "minute": minute

    })


    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("undo_goal_home")
def undo_goal_home():

    if state["home"] > 0:
        state["home"] -= 1

    if state["goals"]:
        state["goals"].pop()

    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("undo_goal_away")
def undo_goal_away():

    if state["away"] > 0:
        state["away"] -= 1

    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("reset_match")
def reset():

    state["home"] = 0
    state["away"] = 0
    state["seconds"] = 0
    state["time"] = "00:00"
    state["goals"] = []

    emit(
        "update",
        state,
        broadcast=True
    )



@socketio.on("start_first")
def start_first():

    state["seconds"] = 0
    state["half"] = 1
    state["running"] = True



@socketio.on("start_second")
def start_second():

    state["seconds"] = 45*60
    state["half"] = 2
    state["running"] = True



@socketio.on("start_timer")
def start_timer():

    state["running"] = True



@socketio.on("stop_timer")
def stop_timer():

    state["running"] = False



@socketio.on("rust")
def rust():

    state["running"] = False
    state["seconds"] = 45*60
    state["time"] = "45:00"

    emit(
        "update",
        state,
        broadcast=True
    )



if __name__ == "__main__":

    socketio.start_background_task(timer_loop)

    socketio.run(
        app,
        host="0.0.0.0",
        port=3000
    )