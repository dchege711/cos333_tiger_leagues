"""
db2.py

This file acts as the central access to the database.

"""

# add a helper function that catchs database errors

from psycopg2 import connect, ProgrammingError
from . import config

import click
import json
from flask import current_app, g
from flask.cli import with_appcontext

class Database:

	def __init__(self):
		DATABASE_URL = config.DATABASE_URL
		self._connection = connect(DATABASE_URL)

	def disconnect(self):
		self._connection.close()

	def launch(self):
		stmtstr1 = 'CREATE TABLE IF NOT EXISTS Player_Accounts (UserId int, Name varchar(255), NetId varchar(255), Email varchar(255), ' + \
					'PhoneNum varchar(255), Room varchar(255), LeagueId varchar(255) PRIMARY KEY (UserId))' 

		stmtstr2 = 'CREATE TABLE IF NOT EXISTS Match_Info (LeagueId int, MatchId int, User1 int, User2 int, Score1 int, ' + \
					'Score2 int, Deadline date PRIMARY KEY (MatchId))'

		stmtstr3 = 'CREATE TABLE IF NOT EXISTS League_Info ( LeagueId int, LeagueName varchar(255), Descrip varchar(255), WinPoints int, ' + \
					'DrawPoints int, LossPoints int, AdditionalQuestions text) PRIMARY KEY (LeagueId)'

		cursor = self._connection.cursor()
		cursor.execute(stmtstr1)
		cursor.execute(stmtstr2)

	def _executeHelper(self, stmtstr, option = None):
		cursor = self._connection.cursor()
		try:
			if option is not None:
				cursor.execute(stmtstr, option)
			else:
				cursor.execute(stmtstr)
			self._connection.commit()
		except ProgrammingError as error:
			print(error)
			self._connection.rollback()

	# leagueinfo must be a list, dict or tuple that contains info from a form
	# knowing the particularily order of the elements in the tuple is VERY IMPORTANT

	def isMember(self, netid):
		stmtstr1 = 'SELECT UserId FROM Player_Accounts WHERE NetId = netid'
		cursor = self._connection.cursor()
		self._executeHelper(stmtstr1)
		userid = cursor.fetchone()

		if userid == None:
			return 0
		else:
			return 1

	def createProfile(self, playerinfo):
		stmtstr1 = 'SELECT max(UserId) FROM Player_Accounts'
		cursor = self._connection.cursor()
		try:
			cursor.execute(stmtstr1)
			userid = int(cursor.fetchone()[0]) + 1
		except ProgrammingError:
			print("Error")
			userid = 0

		accountinfo = [userid, playerinfo["Name"], playerinfo["NetId"], playerinfo["Email"], playerinfo["PhoneNum"], playerinfo["Room"]]

		# playerinfo should be a tuple that contains the player's name, netid, console situation, room, and league status
		stmtstr2 = 'INSERT INTO Player_Accounts (UserId, Name, NetId, Email, PhoneNum, Room) ' +\
					'VALUES (%s, %s, %s, %s, %s, %s)'

		self._executeHelper(stmtstr2, accountinfo)


	def createLeague(self, leagueinfo):
		stmtstr1 = 'SELECT max(LeagueId) FROM League_Info2'
		cursor = self._connection.cursor()
		self._executeHelper(stmtstr1)
		results = cursor.fetchone()
		if results and results[0] is not None: leagueid = results[0] + 1
		else: leagueid = 1

		userid = leagueinfo["UserId"]
		sanitizedAdditionalQuestions = {}
		for idx, question in enumerate(leagueinfo["AdditionalQuestions"].values()):
			try:
				sanitizedAdditionalQuestions["question{}".format(idx)] = {
					"question": question["question"], "options": question["options"]
				}
			except KeyError:
				return {
					"success": False, "status": 200, 
					"message": "Malformed input detected!"
				}

		leaguebasics = (
			leagueid, leagueinfo["LeagueName"], leagueinfo["Descrip"], 
			leagueinfo["WinPoints"], leagueinfo["DrawPoints"], 
			leagueinfo["LossPoints"], json.dumps(sanitizedAdditionalQuestions)
		)
		stmtstr2 = 'INSERT INTO League_Info2 (LeagueId, LeagueName, Descrip, WinPoints, DrawPoints, LossPoints, AdditionalQuestions) ' + \
					'Values (%s, %s, %s, %s, %s, %s, %s)'

		self._executeHelper(stmtstr2, leaguebasics)

		# questions provided by the creator of league, given as the keys in leagueinfo

		stmtstr3 = 'CREATE TABLE LeagueResponses{} (UserId int, Status VARCHAR(255), {})'.format(
			leagueid, ", ".join([
				"{} VARCHAR(255)".format(x) for x in sanitizedAdditionalQuestions.keys()
			])
		)

		print("Statement 3:", stmtstr3)

		self._executeHelper(stmtstr3)
		self._connection.commit()

		return None

	# def joinLeague(self, playerinfo):


	# def getRequests(self, leagueid):
	# 	stmtstr = "SELECT * FROM INFORMATION_SCHEMA.COLUMNS"

	# def leaveLeague(self):


	# def submitScore(self):


	# def confirmScore(self):


	# def confirmPlayer(self):


	# def removePlayer(self):


	# def changeScore(self):

if __name__ == "__main__":
	db = Database()
	db.launch()

