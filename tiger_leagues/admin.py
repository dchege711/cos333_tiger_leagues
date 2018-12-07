"""
admin.py

Exposes a blueprint that handles requests made to `/admin/*` endpoint

"""

from flask import (
    Blueprint, render_template, session, request, url_for, redirect, jsonify
)

from . import league, decorators, db
from datetime import date, timedelta

database = db.Database()
bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.before_request
def admin_status_required():
    """
    A decorator function that asserts that a user has admin privileges for the 
    requested URL.

    http://flask.pocoo.org/docs/1.0/api/#flask.Flask.before_request
    """
    parts = request.path.split("/admin/")
    if len(parts) < 2:
        return redirect(url_for("league.index"))

    league_id = parts[1].split("/")[0]
    associated_leagues = session.get("user")["associated_leagues"]
    if league_id not in associated_leagues or associated_leagues[league_id]["status"] != "admin":
        return redirect(url_for("league.index"))
    # If nothing has been returned, the request will be passed to its handler


@bp.route("/<int:league_id>/approve-members", methods=["GET", "POST"])
def league_requests(league_id):
    """
    @GET: The admin can view the requests to join the league and can choose
    to accept or reject the join requests
    """
    league_info = league.get_join_league_info(league_id)
    def __fetch_league_requests():
        league_response_table_name = "league_responses_{}".format(league_id)
        join_requests = database.execute(
            "SELECT {}.*, users.name FROM {}, users WHERE users.user_id = {}.user_id", 
            dynamic_table_or_column_names=[
                league_response_table_name,
                league_response_table_name,
                league_response_table_name
            ]
        )
        return join_requests

    if request.method == "GET":
        join_requests = __fetch_league_requests()
        return render_template(
            "/admin/approve_members.html", league_info=league_info, 
            join_requests=join_requests
        )
    
    if request.method == "POST":
        available_statuses = {
            league.STATUS_ADMIN, league.STATUS_DENIED, league.STATUS_MEMBER, 
            league.STATUS_PENDING
        }
        league_statuses = request.json # {1: "admin", 23: "member"}
        for value in league_statuses.values():
            if value not in available_statuses:
                return jsonify({
                    "success": False, "status": 200,
                    "message": "{} is not a valid status".format(value)
                })

        for user_id, user_status in league_statuses.items():
            database.execute(
                "UPDATE {} SET status=%s WHERE user_id=%s;",
                dynamic_table_or_column_names=["league_responses_{}".format(league_info["league_id"])],
                values=[user_status, user_id]
            )

        join_requests = __fetch_league_requests()
        user_id_to_status = {}
        for join_request in join_requests:
            user_id_to_status[join_request["user_id"]] = join_request["status"]

        return jsonify({
            "success": True, "status": 200, "message": user_id_to_status
        })

@bp.route("/<int:league_id>/", methods=["GET"])
@decorators.login_required
def league_homepage(league_id):
    return "Display League Admin Panel"

@bp.route("/<int:league_id>/approve", methods=["POST"])
@decorators.login_required
def approve_scores(league_id):
    latest_date = date.today() + timedelta(days = 7)
    earliest_date = date.today() - timedelta(days = 7)
    reported_matches = database.execute(
                "SELECT FROM match_info WHERE legaue_id= %s AND (deadline >= latest_date OR \
                deadline =< latest_date) AND (status = %s OR status = %s);",
                values=[league_id, league.STATUS_APPROVED, league.STATUS_PENDING]
            )
            
    return NotImplementedError()
