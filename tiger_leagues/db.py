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
	stmtstr = 'CREATE TABLE Player_Accounts (UserId int, Name varchar(255), NetId varchar(255), Email varchar(255) ' + \
				'PhoneNum varchar(255), Room varchar(255), LeagueId varchar(255)' 


	stmtstr2 = 'CREATE TABLE Match_Info (LeagueId int, MatchId int, User1 int, User2 int, Score1 int, ' + \
				'Score2 int, Deadline date)'

	stmtstr3 = 'CREATE TABLE League_Info (LeagueName varchar(255), Descrip varchar(255), WinPoints int, ' + \
				'DrawPoints int, LossPoints int, LeagueId int,'

	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	cursor.execute(stmtstr2)

# leagueinfo must be a list, dict or tuple that contains info from a form
# knowing the particularily order of the elements in the tuple is VERY IMPORTANT

def isMember(self, netid)
	stmtstr1 = 'SELECT UserId FROM Player_Accounts WHERE NetId = netid'
	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	userid = cursor.fetchone()

	if userid == None:
		return 0
	else:
		return 1

def createProfile(self, playerinfo):
	stmtstr1 = 'SELECT max(UserId) FROM Player_Accounts'
	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	userid = cursor.fetchone()

	userid = userid + 1

	accountinfo = [userid, playerinfo["Name"], playerinfo["NetId"], playerinfo["Email"], playerinfo["PhoneNum"], playerinfo["Room"]]

	# playerinfo should be a tuple that contains the player's name, netid, console situation, room, and league status
	stmtstr2 = 'INSERT INTO Player_Accounts (UserId, Name, NetId, Email, PhoneNum, Room) ' +\
				'VALUES (?, ?, ?, ?, ?, ?)'

	cursor.execute(stmtstr2, accountinfo)


def createLeague(self, leagueinfo):
	stmtstr1 = 'SELECT max(LeagueId) FROM League_Info'
	cursor = self._connection.cursor()
	cursor.execute(stmtstr1)
	leagueid = cursor.fetchone()

	if (leagueid == None):
		leagueid = 0

	leaguid = leagueid + 1

	userid = leagueinfo("UserId")

	leaguebasics = [leagueid, leagueinfo["LeagueName"], leagueinfo["Descrip"], leagueinfo["WinPoints"], leagueinfo["DrawPoints"], leagueinfo["LossPoints"]]

	stmtstr2 = 'INSERT INTO League_Info (LeagueId, LeagueName, Descrip, WinPoints, DrawPoints, LossPoints) ' + \
				'Values (?, ?, ?, ?, ?, ?)'

	cursor.execute(stmtstr2, leaguebasics)

	# questions provided by the creator of league, given as the keys in leagueinfo
	temp = leagueinfo.keys()

	requests = []

	stmtstr3 = 'CREATE TABLE '

	stmtstr3 = stmtstr3 + leagueid + " (UserId, Status"

	for i in range(6, len(leagueinfo)):
		requests.append(leagueinfo[temp[i]])
		stmtstr3 = stmtstr3 + ", " + temp[i]

	stmtstr3 = ") Values (" + userid + ", Admin"

	for i in range(2, len(requests)):
			stmtstr3 = stmtstr3 + ", " + requests[i]

	stmtstr3 = stmtstr3 + ")"

	cursor.execute(stmtstr3)

def joinLeague(self, playerinfo):


def getRequests(self, leagueid):
	stmtstr = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"

def leaveLeague(self):


def submitScore(self):


def confirmScore(self):


def confirmPlayer(self):


def removePlayer(self):


def changeScore(self):
