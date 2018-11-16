"""
league.py

Exposes a blueprint that handles requests made to `/league/*` endpoint

"""

from random import randint
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from . import db

database = db.Database()
bp = Blueprint("league", __name__, url_prefix="/league")

@bp.route("/")
@bp.route("/<int:leagueID>/")
def league_homepage(leagueID):
    """
    @returns [List] where each item has the fields `player_name, wins, draws, 
    losses, goals_formed, goals_allowed, goal_diff, points' (sorted by points)
    """
    standings = []
    total_num_games = 40

    league_info_list = database.getLeagueInfoList(userID=1)

    for _ in range(10): 

        goals_formed = randint(0, 60)
        goals_allowed = randint(0, 40)
        wins = randint(0, 30)
        losses = randint(0, 9)
        draws = total_num_games - wins - losses
        goal_diff = goals_formed - goals_allowed

        standings.append({
            "player_name": "Dummy",
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_formed": goals_formed,
            "goals_allowed": goals_allowed,
            "goal_diff": goal_diff,
            "points": (wins * 3) + draws 
        })

    return render_template(
        "/league/league_homepage.html", 
        standings=standings, upcoming_matches=[],
        past_matches=[], league_info_list=league_info_list
    )

@bp.route("/create", methods=("GET", "POST"))
def create_league():
    if request.method == "GET":
        return render_template("/league/create_league.html")
    elif request.method == "POST":
        createLeagueInfo = request.json
        createLeagueInfo["UserId"] = 0
        results = database.createLeague(createLeagueInfo)
        if results["success"]:
            return jsonify(results)
        else:
            return "500. Internal Server Error"

@bp.route("/<int:leagueID>/join", methods=("GET", "POST"))
def join_league(leagueID):
    if request.method == "GET":
        leagueInfo = database.getJoinLeagueInfo(leagueID)
        return render_template(
            "/league/join_league.html", leagueInfo=leagueInfo["message"]
        )
    elif request.method == "POST":
        receivedInfo = request.form
        for key, val in receivedInfo.items():
            print(key, "->", val)
        return redirect(url_for(".league_homepage", leagueID=1, alertMsg="Request submitted!"))