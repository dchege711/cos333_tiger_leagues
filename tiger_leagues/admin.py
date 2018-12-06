"""
admin.py

Exposes a blueprint that handles requests made to `/admin/*` endpoint

"""

from flask import Blueprint

from . import league

bp = Blueprint("admin", __name__, url_prefix="/admin")

def __approve_request(user_id, league_id):
    database.execute(
        "UPDATE league_responses_{} \
        SET status = %s WHERE user_id = %s".format(league_id),
        STATUS_APPROVED, user_id
    )



def __deny_request(user_id, league_id):
    database.execute(
        "UPDATE league_responses_{} \
        SET status = %s WHERE user_id = %s".format(league_id),
        STATUS_DENIED, user_id
    )

def league_requests(league_id):
    """
    The admin can view the requests to join the league and can choose
    to accept or reject the request_actions
    
    """
    
    league_requests = "SELECT * FROM league_responses_{}".format(league_id)

@bp.route("/<int:league_id>/approve", methods=["POST"])
@decorators.login_required   
def approve_scores(match_id):
    
    
    
    