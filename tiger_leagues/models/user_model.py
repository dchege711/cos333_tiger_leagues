"""
user_model.py

Exposes functions that are used by the controller for the `/user/*` endpoint

"""

from . import db_model

db = db_model.Database()

def get_user(net_id):
    """
    @param `net_id` [str]: The Princeton Net ID of the user

    @returns `dict` representing a user in the database who has the specified 
    net ID, otherwise returns `None`
    """
    cursor = db.execute((
        "SELECT user_id, name, net_id, email, phone_num, room, league_ids "
        "FROM users WHERE net_id = %s"
    ), values=[net_id])
    user_profile = cursor.fetchone()
    if user_profile is None: return user_profile

    # Although psycopg2 allows us to change values already in the table, we 
    # cannot add new fields that weren't columns, thus the need for a new dict
    mutable_user_data = dict(**user_profile) # https://www.python.org/dev/peps/pep-0448/#abstract
    if user_profile["league_ids"] is None:
        mutable_user_data["league_ids"] = []
        mutable_user_data["associated_leagues"] = {}
    else:
        mutable_user_data["league_ids"] = [int(x) for x in user_profile["league_ids"].split(", ")]
        mutable_user_data["associated_leagues"] = __get_user_leagues_info(
            user_profile["user_id"], mutable_user_data["league_ids"]
        )
    return mutable_user_data

def update_user_profile(user_profile, net_id, submitted_data):
    """
    @param dict `user_profile`: usually obtained from session.get('user'). If 
    this is set to `None`, a new user will be created and added to the database.

    @param str `net_id`: the Princeton Net ID of the user

    @param dict `submitted_data`: Keys may include `name`, `email`, `phone_num`, 
    `room`

    @returns dict: the updated user profile

    """
    changeable_cols = ["name", "email", "phone_num", "room"]
    updated_col_names = []
    updated_col_values = []
    for column in changeable_cols:
        if column in submitted_data:
            updated_col_names.append(column)
            updated_col_values.append(submitted_data[column])

    if user_profile is None: 
        # Then we have a new user...
        updated_col_names += ["net_id"]
        updated_col_values += [net_id]
        db.execute(
            "INSERT INTO users ({}) VALUES ({})".format(
                ", ".join(["{}" for _ in updated_col_names]),
                ", ".join(["%s" for _ in updated_col_values])
            ),
            values=updated_col_values,
            dynamic_table_or_column_names=updated_col_names
        )
    else:
        db.execute(
            "UPDATE users SET {} WHERE user_id = %s".format(
                ",".join(["{}=%s" for _ in updated_col_names])
            ), 
            values=updated_col_values + [user_profile["user_id"]],
            dynamic_table_or_column_names=updated_col_names
        )

    return get_user(net_id)

def __get_user_leagues_info(user_id, league_ids):
    """
    @param int `user_id`: the ID of the associated user.

    @param List[int] `league_ids`: a list of all the league IDs that a user is associated with

    @return `Dict[dict]` containing all leagues that a user is associated with. 
    Expected keys: `league_name`, `league_id`, `status`.
    """
    user_leagues_info = {}
    for league_id in league_ids:
        cursor = db.execute(
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
