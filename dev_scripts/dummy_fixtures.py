"""
dummy fixtures
"""

import sys
from math import ceil
sys.path.insert(0, "..")

def fixture_generator(users):
    # we need a more effective of finding all the users in the league. 
    # as of right now we need to iterate through every user and the league_ids they pertain to
    length = len(users)
    odd = 0

    if length % 2 is not 0:
        odd = 1

    half = ceil(length/2)

    tempList1 = [None] * half
    tempList2 = [None] * half

    for i in range(0, half):
    	tempList1[i] = users[i]

    j = 0
    for i in range(length-1, half-1, -1):
    	tempList2[j] = users[i]
    	j += 1

    fixtures_list = []
    rounds_list = []
    pairs_list = []

    for j in range(0,length-1):
        for i in range(0, half):
            pairs_list = [tempList1[i], tempList2[i]]
            rounds_list.append(pairs_list)
            pairs_list = []
        tempList1.insert(1, tempList2[0])
        del tempList2[0]
        tempList2.append(tempList1[half])
        del tempList1[-1]
        fixtures_list.append(rounds_list)
        rounds_list = []

    return fixtures_list
       




if __name__ == "__main__":
	users = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
	fixture_generator(users)