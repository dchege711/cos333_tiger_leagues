"""
player.py

Exposes a blueprint that handles requests made to `/user/*` endpoint

"""

from flask import Blueprint, render_template, session, request, flash
from . import db, decorators

database = db.Database()
bp = Blueprint("user", __name__, url_prefix="/user")

def get_user(net_id):
    """
    @param `net_id` [str]: The Princeton Net ID of the user
    @returns `dict` representing a user in the database. 
    @returns `None` If the user doesn't exist.
    """
    cursor = database.execute((
        "SELECT user_id, name, net_id, email, phone_num, room, league_ids "
        "FROM users WHERE net_id = %s"
    ), values=[net_id])
    user_data = cursor.fetchone()
    if user_data is None: return user_data

    # Although psycopg2 allows us to change values already in the table, we 
    # cannot add new fields that weren't columns, thus the need for a new dict
    mutable_user_data = dict(**user_data) # https://www.python.org/dev/peps/pep-0448/#abstract
    if user_data["league_ids"] is None:
        mutable_user_data["league_ids"] = []
        mutable_user_data["associated_leagues"] = {}
    else:
        mutable_user_data["league_ids"] = [int(x) for x in user_data["league_ids"].split(", ")]
        mutable_user_data["associated_leagues"] = __get_user_leagues_info(
            user_data["user_id"], mutable_user_data["league_ids"]
        )
    return mutable_user_data

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
    return render_template("/user/user_profile.html", user=session.get("user"))

@bp.route("/profile", methods=["POST"])
@decorators.login_required
def update_user_profile():
    """
    Update the information stored about a user. This method will most likely 
    receive POST requests from the template rendered by user.displayUserProfile

    """
    user_data = session.get("user")
    net_id = session.get("net_id")
    submitted_data = request.form
    changeable_cols = ["name", "email", "phone_num", "room"]
    updated_col_names = []
    updated_col_values = []
    for column in changeable_cols:
        if column in submitted_data:
            updated_col_names.append(column)
            updated_col_values.append(submitted_data[column])

    if user_data is None: 
        # Then we have a new user...
        updated_col_names += ["net_id"]
        updated_col_values += [net_id]
        database.execute(
            "INSERT INTO users ({}) VALUES ({})".format(
                ", ".join(["{}" for _ in updated_col_names]),
                ", ".join(["%s" for _ in updated_col_values])
            ),
            values=updated_col_values,
            dynamic_table_or_column_names=updated_col_names
        )
    else:
        database.execute(
            "UPDATE users SET {} WHERE user_id = %s".format(
                ",".join(["{}=%s" for _ in updated_col_names])
            ), 
            values=updated_col_values + [user_data["user_id"]],
            dynamic_table_or_column_names=updated_col_names
        )

    session["user"] = get_user(net_id)
    flash("User profile updated!")
    return render_template("/user/user_profile.html", user=session.get("user"))

def __create_user_profile(user_info):
    """
    Create a user from the supplied information and save them to the database.
    Expected keys: `name`, `net_id`, `email`, `phone_num`, `room`.

    @returns `Cursor` if transaction is successful.

    """

    return database.execute(
        (
            "INSERT INTO users (name, net_id, email, phone_num, room) "
            "VALUES (%s, %s, %s, %s, %s);"
        ),
        values=[
            user_info["name"], user_info["net_id"], user_info["email"], 
            user_info["phone_num"], user_info["room"]
        ]
    )

def __get_user_leagues_info(user_id, league_ids):
    """
    @param int `user_id`: the ID of the associated user.

    @param List[int] `league_ids`: a list of all the league IDs that a user is associated with

    @return `Dict[dict]` containing all leagues that a user is associated with. 
    Expected keys: `league_name`, `league_id`, `status`.
    """
    user_leagues_info = {}
    for league_id in league_ids:
        cursor = database.execute(
            (
                "SELECT league_info.league_id, league_name, status FROM league_info, {} "
                "WHERE {}.user_id = %s AND league_info.league_id = %s"
            ),
            values=[user_id, league_id],
            dynamic_table_or_column_names=[
                "league_responses_{}".format(league_id),
                "league_responses_{}".format(league_id)
            ]
        )
        info = cursor.fetchone()
        if info is not None:
            user_leagues_info[info["league_id"]] = dict(**info)
        
    return user_leagues_info
