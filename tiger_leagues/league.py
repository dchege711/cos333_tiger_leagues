"""
league.py

Exposes a blueprint that handles requests made to `/league/*` endpoint

"""

from random import randint
from flask import Blueprint, render_template

bp = Blueprint("league", __name__, url_prefix="/league")

@bp.route("/")
@bp.route("/1/standings")
def league_standings():
    """
    @returns [List] where each item has the fields `player_name, wins, draws, 
    losses, goals_formed, goals_allowed, goal_diff, points' (sorted by points)
    """
    standings = []
    total_num_games = 40

    for _ in range(20): 

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
        "/league/home.html", 
        standings=standings, upcoming_matches=[],
        past_matches=[]
    )

@bp.route("/create")
def create_league():
    return render_template("/league/create_league.html")


    
