"""
player.py

Exposes a blueprint that handles requests made to `/user/*` endpoint

"""

from flask import Blueprint
from . import db

database = db.Database()
bp = Blueprint("user", __name__, url_prefix="/user")

def getUser(netid):
    """
    @returns `dict` representing a user in the database. If the user doesn't 
    exist, returns `None`.
    """
    cursor = database.execute(
        'SELECT UserId FROM Player_Accounts WHERE NetId = %s', values=(netid,)
    )
    userid = cursor.fetchone()

    return userid

def createProfile(playerinfo):
    cursor = database.execute('SELECT max(UserId) FROM Player_Accounts')
    userid = int(cursor.fetchone()[0]) + 1

    accountinfo = [
        userid, playerinfo["Name"], playerinfo["NetId"], playerinfo["Email"], 
        playerinfo["PhoneNum"], playerinfo["Room"]
    ]

    # playerinfo should be a tuple that contains the player's name, netid, console situation, room, and league status
    stmtstr2 = 'INSERT INTO Player_Accounts (UserId, Name, NetId, Email, PhoneNum, Room) ' +\
            'VALUES (%s, %s, %s, %s, %s, %s)'

    database.execute(stmtstr2, values=accountinfo)
