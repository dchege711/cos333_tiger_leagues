"""
db2.py

This file acts as the central access to the database.

"""

import psycopg2
import config.py

import click
from flask import current_app, g
from flask.cli import with_appcontext

def __init__(self):
    self._connection = None

def connect(self):
	DATABASE_URL = config.DATABASE_URL
	self._connection = psycopg2.connect(DATABASE_URL)

def disconnect(self):
    self._connection.close()

def launch(self):
	stmtstr1 = 'CREATE TABLE League_Info (LeagueId int, LeagueName varchar(255), Deadline date)'

	stmtstr2 = 'CREATE TABLE Player_Info (UserId int, LeagueId int, Name varchar(255), ' + \
				'NetId varchar(255), Console int, Room varchar(255), Status varchar(255)' 


	stmtstr3 = 'CREATE TABLE Match_Info (LeagueId int, MatchId int, User1 int, User2 int, Score1 int, ' + \
				'Score2 int, Deadline date)'

	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	cursor.execute(stmtstr2)
	cursor.execute(stmtstr3)

# leagueinfo must be a list, dict or tuple that contains info from a form
# knowing the particularily order of the elements in the tuple is VERY IMPORTANT

def isMember(self, netid)
	stmtstr1 = 'SELECT UserId FROM Player_Info WHERE NetId = netid'
	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	userid = cursor.fetchone()

	if userid == None:
		return 0
	else:
		return 1

def createProfile(self, playerinfo):
	stmtstr1 = 'SELECT max(UserId) FROM Player_Info'
	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	userid = cursor.fetchone()

	userid = userid + 1

	# playerinfo should be a tuple that contains the player's name, netid, console situation, room, and league status
	stmtstr2 = 'INSERT INTO Player_Info (UserId, Name, NetId, Console, Room, Status) ' +\
				'VALUES (userid, playerinfo[0], playerinfo[1], playerinfo[2], playerinfo[3], Leagueless'

	cursor.execute(stmtstr2)


def createLeague(self, leagueinfo):
	stmtstr1 = 'SELECT max(LeagueId) FROM League_Info'
	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	leagueid = cursor.fetchone()

	if (leagueid == None):
		leagueid = 0

	leaguid = leagueid + 1

	stmtstr2




def joinLeague(self, leagueid):
	



def leaveLeague(self):


def submitScore(self):


def confirmScore(self):


def confirmPlayer(self):


def removePlayer(self):


def changeScore(self):
