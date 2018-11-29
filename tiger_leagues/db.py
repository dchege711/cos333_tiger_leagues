"""
db2.py

This file acts as the central access to the database.

"""

# add a helper function that catchs database errors

import sys
from psycopg2 import connect, ProgrammingError, extras
from . import config

import click
import json
from flask import current_app, g, url_for
from flask.cli import with_appcontext

class Database:

	def __init__(self):
		DATABASE_URL = config.DATABASE_URL
		self._connection = connect(DATABASE_URL)
		self.launch()

	def disconnect(self):
		self._connection.close()

	def launch(self):
		stmtstr1 = 'CREATE TABLE IF NOT EXISTS Player_Accounts (UserId int, Name varchar(255), NetId varchar(255), Email varchar(255), ' + \
				'PhoneNum varchar(255), Room varchar(255), LeagueId varchar(255), PRIMARY KEY (UserId))' 

		stmtstr2 = 'CREATE TABLE IF NOT EXISTS Match_Info (LeagueId int, MatchId int, User1 int, User2 int, Score1 int, ' + \
				'Score2 int, Deadline date, PRIMARY KEY (MatchId))'

		stmtstr3 = 'CREATE TABLE IF NOT EXISTS League_Info ( LeagueId int, LeagueName varchar(255), Descrip varchar(255), WinPoints int, ' + \
				'DrawPoints int, LossPoints int, AdditionalQuestions text, PRIMARY KEY (LeagueId))'

		print("Ensuring that the tables exist...")

		self.execute(stmtstr1)
		self.execute(stmtstr2)
		self.execute(stmtstr3)

	def execute(self, stmtstr, values=None):
		"""
		@returns `Cursor` after executing the SQL statement in `stmtstr` with 
		placeholders substituted by the `values` tuple.
		"""
		cursor = self._connection.cursor(
			cursor_factory=extras.DictCursor
		)
		try:
			if values is not None:
				cursor.execute(stmtstr, values)
			else:
				cursor.execute(stmtstr)
			self._connection.commit()
		except ProgrammingError as error:
			print(error)
			self._connection.rollback()

		return cursor

	# leagueinfo must be a list, dict or tuple that contains info from a form
	# knowing the particularily order of the elements in the tuple is VERY IMPORTANT

	def createLeague(self, leagueinfo):
		stmtstr1 = 'SELECT max(Leagueid) FROM League_Info'
		cursor = self.execute(stmtstr1)
		results = cursor.fetchone()
		if results[0] is not None: leagueid = results[0] + 1
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
		stmtstr2 = 'INSERT INTO League_Info (LeagueId, LeagueName, Descrip, WinPoints, DrawPoints, LossPoints, AdditionalQuestions) ' + \
				'Values (%s, %s, %s, %s, %s, %s, %s)'

		self.execute(stmtstr2, leaguebasics)

		# questions provided by the creator of league, given as the keys in leagueinfo
		if sanitizedAdditionalQuestions:
			stmtstr3 = 'CREATE TABLE LeagueResponses{} (UserId int PRIMARY KEY, Status VARCHAR(255), {})'.format(
				leagueid, ", ".join([
					"{} VARCHAR(255)".format(x) for x in sanitizedAdditionalQuestions.keys()
				])
			)
		else:
			stmtstr3 = "CREATE TABLE LeagueResponses{} (UserId int PRIMARY KEY, Status VARCHAR(255))".format(leagueid)

		self.execute(stmtstr3)

		return {
			"success": True, "status": 200, 
			"message": {
				"inviteURL": url_for("league.join_league", leagueID=leagueid, _external=True),
				"leagueID": leagueid
			}
		}

	def getLeagueInfoList(self, userID=None):
		"""
		@returns `List[dict]` each dict has the keys `status`, `LeagueName` and 
		`LeagueId`.
		"""

		cursor = self.execute("SELECT LeagueName, LeagueId FROM League_Info;")
		leagueInfoList = []
		try:
			matchingRow = cursor.fetchone()
			while matchingRow is not None:
				leagueInfoList.append({
					"status": "", "LeagueName": matchingRow[0], "LeagueId": matchingRow[1]
				})
				matchingRow = cursor.fetchone()
		except ProgrammingError as err:
			print(err, file=sys.stderr)

		return leagueInfoList

	def getJoinLeagueInfo(self, leagueID):
		"""
		@returns `dict`: keys are `success`, `message` and `status`. The 
		`message` field if successful is another dict having the keys 
		`LeagueName`, `Descrip`, `WinPoints`, `DrawPoints`, `LossPoints` 
		`LeagueId`, `AdditionalQuestions`.
		"""
		cursor = self.execute(
			"SELECT LeagueId, LeagueName, Descrip, WinPoints, \
			DrawPoints, LossPoints, AdditionalQuestions FROM League_Info \
			WHERE LeagueId = %s", values=(leagueID,)
		)
		matchingRow = cursor.fetchone()
		if matchingRow is not None:
			return {
				"success": True, "status": 200,
				"message": {
					"LeagueId": matchingRow[0], "LeagueName": matchingRow[1],
					"Descrip": matchingRow[2], "WinPoints": matchingRow[3],
					"DrawPoints": matchingRow[4], "LossPoints": matchingRow[5],
					"AdditionalQuestions": json.loads(matchingRow[6])
				}
			}
		else:
			return {
				"success": False, "status": 200, "message": "League not found"
			}

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
	print(DATABASE_URL)

