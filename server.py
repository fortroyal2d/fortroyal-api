import os
import sys
import time
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# ================= DATA =================

online_players = set()
player_ips = {}
shutdown_flag = False

announcement_message = ""
announcement_timer = 0

GAME_API_PORT = int(os.environ.get("PORT", 5055))


# ================= HELPERS =================

def load_players():
    if not os.path.exists(PLAYERS_DB):
        return {}
    import json
    with open(PLAYERS_DB, "r") as f:
        return json.load(f)

def save_players(data):
    import json
    with open(PLAYERS_DB, "w") as f:
        json.dump(data, f, indent=4)

def kick_player_runtime(user, reason):
    print(f"[KICK] {user} | {reason}")
    online_players.discard(user)

def ban_player_db(user, reason, admin):
    players = load_players()
    players.setdefault(user, {})
    players[user]["banned"] = True
    players[user]["ban_reason"] = reason
    players[user]["ban_admin"] = admin
    save_players(players)
    print(f"[BAN] {user} | {reason}")

def is_country_banned(ip):
    # placeholder
    return False, "Unknown"

# ================= API =================

@app.route("/announcement", methods=["POST"])
def api_announcement():
    global announcement_message, announcement_timer

    data = request.json
    announcement_message = data.get("message", "")
    announcement_timer = 600

    print("[WEB] Announcement:", announcement_message)

    return jsonify({"status": "ok"})


@app.route("/kick", methods=["POST"])
def api_kick():
    data = request.json
    user = data.get("user")

    if user in online_players:
        kick_player_runtime(user, "Kicked by admin")

    return jsonify({"status": "ok"})


@app.route("/ban", methods=["POST"])
def api_ban():
    data = request.json
    user = data.get("user")

    reason = data.get("reason", "No reason")
    admin = data.get("admin", "WebPanel")

    ban_player_db(user, reason, admin)
    kick_player_runtime(user, "You are banned")

    return jsonify({"status": "ok"})


@app.route("/restart", methods=["POST"])
def api_restart():
    print("[WEB] Restart requested")
    os.execl(sys.executable, sys.executable, *sys.argv)


@app.route("/shutdown", methods=["POST"])
def api_shutdown():
    global shutdown_flag

    shutdown_flag = True

    return jsonify({"status": "shutting down"})


@app.route("/online", methods=["GET"])
def api_online():
    return jsonify({
        "players": list(online_players)
    })


# ================= RANK =================

@app.route("/set_rank", methods=["POST"])
def api_set_rank():
    data = request.json

    user = data.get("user")
    rank = data.get("rank", "Player")

    players = load_players()
    players.setdefault(user, {})
    players[user]["rank"] = rank

    save_players(players)

    print(f"[RANK] {user} -> {rank}")

    return jsonify({"status": "ok"})


# ================= PASSWORD RESET =================

@app.route("/reset_password", methods=["POST"])
def api_reset_password():
    data = request.json

    user = data.get("user")
    new_pass = data.get("new_password")

    if not user or not new_pass:
        return jsonify({
            "status": "error",
            "msg": "Missing data"
        }), 400

    players = load_players()
    players.setdefault(user, {})

    players[user]["password"] = new_pass

    save_players(players)

    print(f"[PASSWORD RESET] {user}")

    return jsonify({"status": "ok"})


# ================= LOGIN =================

@app.route("/login", methods=["POST"])
def api_login():

    data = request.json
    user = data.get("user")

    ip = request.remote_addr

    banned, country = is_country_banned(ip)

    if banned:
        return jsonify({
            "status": "banned",
            "msg": f"Players from {country} are not allowed"
        }), 403

    online_players.add(user)
    player_ips[user] = ip

    print(f"[LOGIN] {user} | {ip}")

    return jsonify({"status": "ok"})


# ================= RUN SERVER =================

if __name__ == "__main__":

    print("FortRoyal API starting...")

    app.run(
        host="0.0.0.0",
        port=GAME_API_PORT
    )