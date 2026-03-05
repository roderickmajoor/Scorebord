import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

state = {
    "home": 0,
    "away": 0,
    "time": "00:00",
    "extra": 0,
    "homeLogo": "/static/laren.png",
    "awayLogo": "",
    "homeName": "SV Laren '99",
    "awayName": "Tegenstander",
    "sponsor": "",
    "running": False,
    "seconds": 0,
    "half": 1
}

def timer_loop():
    while True:
        socketio.sleep(1)

        if state["running"]:
            state["seconds"] += 1

            total_sec = state["seconds"]

            # BASIS TIJD
            if state["half"] == 1:
                base_limit = 45 * 60
            else:
                base_limit = 90 * 60

            if total_sec <= base_limit:
                # Normale tijd
                min_ = total_sec // 60
                sec_ = total_sec % 60

                state["time"] = f"{min_:02}:{sec_:02}"
                state["extra"] = 0

            else:
                # EXTRA TIJD
                extra_sec = total_sec - base_limit

                base_min = base_limit // 60
                state["time"] = f"{base_min:02}:00"

                extra_min = extra_sec // 60
                extra_s = extra_sec % 60

                # 👉 NU echte klok i.p.v. alleen +1
                state["extra"] = f"{extra_min:02}:{extra_s:02}"

            socketio.emit("update", state)

@socketio.on("start_first")
def start_first():
    state["seconds"] = 0
    state["half"] = 1
    state["running"] = True

@socketio.on("start_second")
def start_second():
    state["seconds"] = 45 * 60
    state["half"] = 2
    state["running"] = True

@socketio.on("stop_timer")
def stop_timer():
    state["running"] = False

@socketio.on("rust")
def rust():
    state["running"] = False
    state["seconds"] = 45 * 60
    state["half"] = 1
    state["time"] = "45:00"
    state["extra"] = 0
    socketio.emit("update", state)

@app.route("/display")
def display():
    return render_template("display.html")

@app.route("/control")
def control():
    return render_template("control.html")

@socketio.on("connect")
def on_connect():
    emit("update", state)  # 👈 bij verbinden direct huidige stand sturen

@socketio.on("update")
def update(data):
    state.update(data)
    emit("update", state, broadcast=True)

if __name__ == "__main__":
    socketio.start_background_task(timer_loop)
    socketio.run(app, host="0.0.0.0", port=3000)
