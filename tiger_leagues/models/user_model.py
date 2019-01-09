"""
user_model.py

Exposes functions that are used by the controller for the `/user/*` endpoint

"""

from . import db_model

db = db_model.Database()

NOTIFICATION_STATUS_SEEN = "seen"
NOTIFICATION_STATUS_DELIVERED = "delivered"
NOTIFICATION_STATUS_ARCHIVED = "archived"

def get_user(net_id, user_id=None):
    """
    :param net_id: str
    
    The Princeton Net ID of the user

    :kwarg user_id: int

    The ID of the user as assigned in Tiger Leagues

    :return: ``dict`` 
    
    A representation of the user as stored in the database. Keys include: 
    ``user_id, name, net_id, email, phone_num, room, league_ids, 
    associated_leagues, unread_notifications``
    
    :return: ``NoneType``

    If there is no user in the database with the provided net id
    """
    if net_id is not None:
        cursor = db.execute((
            "SELECT user_id, name, net_id, email, phone_num, room, league_ids "
            "FROM users WHERE net_id = %s"
        ), values=[net_id])
    else:
        cursor = db.execute((
            "SELECT user_id, name, net_id, email, phone_num, room, league_ids "
            "FROM users WHERE user_id = %s"
        ), values=[user_id])

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
    
    mutable_user_data["unread_notifications"] = read_notifications(user_profile["user_id"])
    return mutable_user_data

def update_user_profile(user_profile, net_id, submitted_data):
    """
    :param user_profile: dict 
    
    A representation of the user, usually obtained from ``get_user(net_id)``. If 
    set to ``None``, a new user will be created and added to the database.

    :param net_id: str
    
    The Princeton Net ID of the user

    :param submitted_data: dict
    
    Keys may include `name`, `email`, `phone_num`, `room`

    :return: dict
    
    The updated user profile

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
    :param user_id: int
    
    The ID of the associated user.

    :param league_ids: list[int]
    
    A list of all the league IDs that a user is associated with

    :return: `dict[dict]`
    
    Contains all leagues that a user is associated with. Each dict is keyed by: 
    ``league_name``, ``league_id``, ``status``.
    
    """
    user_leagues_info = {}
    for league_id in league_ids:
        league_responses_tablename = "league_responses_{}".format(league_id)
        cursor = db.execute(
            (
                "SELECT league_info.league_id, league_name, status, {}.division_id "
                "FROM league_info, {} "
                "WHERE {}.user_id = %s AND league_info.league_id = %s"
            ),
            values=[user_id, league_id],
            dynamic_table_or_column_names=[
                league_responses_tablename,
                league_responses_tablename,
                league_responses_tablename
            ]
        )
        info = cursor.fetchone()
        if info is not None:
            user_leagues_info[int(league_id)] = dict(**info)
        
    return user_leagues_info

def send_notification(user_id, notification):
    """
    Send a notification to this user

    :param user_id: int

    The ID of the associated user

    :param notification: dict

    Expected keys include: ``league_id, notification_text``

    :return: ``int``

    The notification ID if the notification is successfully delivered to the user's 
    mailbox.

    :return: ``NoneType``

    If the method failed

    """

    if "league_id" not in notification or "notification_text" not in notification:
        return None
    
    return db.execute(
        (
            "INSERT INTO notifications ("
            "user_id, league_id, notification_status, notification_text)"
            "VALUES (%s, %s, %s, %s) RETURNING notification_id;"
        ), 
        values=[user_id, notification["league_id"], NOTIFICATION_STATUS_DELIVERED, notification["notification_text"]]
    ).fetchone()["notification_id"]

def read_notifications(user_id, notification_status=None):
    """
    :param user_id: int

    The ID of the associated user

    :kwarg notification_status: str

    The status of the notifications that are to be read. If ``None``, this defaults 
    to notifications that have not been archived.

    :return: ``cursor``

    An iterable cursor where each item keyed by ``notification_id``, 
    ``notification_status``, ``notification_text``, ``created_at``, ``league_name``.

    """
    if notification_status is None:
        return db.execute(
            (
                "SELECT notifications.*, league_info.league_name FROM notifications, league_info "
                "WHERE user_id = %s AND notification_status != %s AND league_info.league_id = notifications.league_id "
                "ORDER BY created_at DESC;"
            ),
            values=[user_id, NOTIFICATION_STATUS_ARCHIVED]
        ).fetchall()

    return db.execute(
        (
            "SELECT notifications.*, league_info.league_name FROM notifications, league_info "
            "WHERE user_id = %s AND notification_status = %s AND league_info.league_id = notifications.league_id "
            "ORDER BY created_at DESC;"
        ),
        values=[user_id, notification_status]
    ).fetchall()

def update_notification_status(user_id, notification_obj):
    """
    :param user_id: int

    The ID of the user making this request

    :param notification_obj: dict

    Expected keys: ``notification_id``, ``notification_status``

    :return: ``dict``

    Keyed by ``success`` and ``message``. 
    If ``success`` is ``False``, ``message`` contains a description of why the 
    request failed.
    If ``success`` is ``True``, ``message`` contains the new status of the 
    notification.

    """
    allowed_statuses = set([
        NOTIFICATION_STATUS_ARCHIVED, NOTIFICATION_STATUS_DELIVERED, 
        NOTIFICATION_STATUS_SEEN, "deleted"
    ])

    if "notification_id" not in notification_obj or "notification_status" not in notification_obj:
        return {
            "success": False, "message": "Missing parameters: notification_id, notification_status"
        }
    
    submitted_status = notification_obj["notification_status"] 
    if submitted_status not in allowed_statuses:
        return {
            "success": False, "message": "Invalid value for 'notification_status'"
        }

    if submitted_status == "delete":
        deleted_notification_id = db.execute(
            "DELETE FROM notifications WHERE notification_id = %s AND user_id = %s RETURNING notification_id;",
            values=[notification_obj["notification_id"], user_id]
        ).fetchone()["notification_id"]

        if deleted_notification_id == notification_obj["notification_id"]:
            return {"success": True, "message": "deleted"}
        return {"success": True, "message": "Notification not found"}
        

    new_status = db.execute(
        (
            "UPDATE notifications SET notification_status = %s "
            "WHERE notification_id = %s AND user_id = %s RETURNING notification_status;"
        ),
        values=[
            submitted_status, notification_obj["notification_id"], user_id
        ]
    ).fetchone()["notification_status"]

    return {
        "success": True if new_status == submitted_status else False,
        "message": new_status
    }
