"""
player.py

Exposes a blueprint that handles requests made to `/user/*` endpoint

"""

from flask import Blueprint
from . import db, decorators

database = db.Database()
bp = Blueprint("user", __name__, url_prefix="/user")

def get_user(net_id):
    """
    @returns `dict` representing a user in the database. 
    
    @returns `None` If the user doesn't exist.
    """
    return {
        "user_id": 0, "name": "Chege Gitau", "net_id": net_id, 
        "email": "dgitau@princeton.edu", "phone_num": "555-555-5555",
        "room": "Henry Hall A34", 
        "associated_leagues": __get_user_league_info_list(0)
    }

@bp.route("/profile", methods=["GET"])
@decorators.login_required
def display_user_profile():
    """
    Render a template that contains user information. The user should be able to 
    request an update some of the displayed information. The userid will be in 
    the sessions object.
    
    Sample information might include:

    Read-Only: NetID
    Editables: Preferred Name, Preferred Email, Phone Number, Room Number
    Links to leagues that a user is involved in

    """
    return "Display user profile"

@bp.route("/update", methods=["POST"])
@decorators.login_required
def update_user_profile():
    """
    Update the information stored about a user. This method will most likely 
    receive POST requests from the template rendered by user.displayUserProfile

    """
    return NotImplementedError()

def __create_user_profile(user_info):
    """
    Create a user from the supplied information and save them to the database.

    @returns `Cursor` if transaction is successful.

    """

    return database.execute(
        (
            "INSERT INTO users (name, net_id, email, phone_number, room) "
            "VALUES (%s, %s, %s, %s, %s, %s);"
        ),
        values=[
            user_info["name"], user_info["net_id"], user_info["email"], 
            user_info["phone_number"], user_info["room"]
        ]
    )

def __get_user_league_info_list(user_id):
    """
    @return `List[dict]` containing all leagues that a user is associated with.
    
    """
    return [
        {"league_name": "FIFA League", "league_id": 0, "status": "joined"},
        {"league_name": "Table Tennis", "league_id": 1, "status": "pending"},
        {"league_name": "Dragonball Z", "league_id": 2, "status": "pending"},
    ]
