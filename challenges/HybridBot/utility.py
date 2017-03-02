from Pirates import *
from shared import *
import math

EARLY_TURNS = 17
MIN_STACK_MULT = 1.7
DEBUG = False

class BestMove:
	def __init__(self, aircraft, closest_location, min_dist):
		self._aircraft = aircraft
		self._loc = closest_location
		self._dist = min_dist

	def get_aircraft(self):
		return self._aircraft

	def get_location(self):
		return self._loc

	def get_dist(self):
		return self._dist

#Important utility function, takes 2 lists of locations and finds the closest one between them
def best_move(aircrafts, locations):
	moves = []
	for aircraft in aircrafts[:]:
		min_dist = 9999999
		closest_location = 0
		for location in locations[:]:
			if aircraft.distance(location) < min_dist:
				min_dist = aircraft.distance(location)
				closest_location = location
		move = BestMove(aircraft, closest_location, min_dist)
		moves.append(move)
	min_move = BestMove(0, 0, 9999999)
	for move in moves:  # type: BestMove
		if move.get_dist() < min_move.get_dist():
			min_move = move
	return min_move

#Checks if the enemy bot is playing defensively around our city or neutral city
def is_defensive(game):
	highest = filter(lambda x: danger_board[x] > 4, danger_board)
	for city in game.get_my_cities() + game.get_neutral_cities():
		for loc in highest[:]:
			if Location(loc[0], loc[1]).distance(city) > 3:
				highest.remove(loc)
	return len(highest) > 0
#Checks if the enemy bot is stack drones
def is_stacking(game):
	drones = game.get_my_living_drones()
	grid = {}
	for x in xrange(rows):
		for y in xrange(cols):
			grid[(x,y)] = 0
	for drone in drones:
		loc = drone.location
		grid[(loc.row,loc.col)] += 1

	# get all spaces that have a 0.8 or above drone occurrence
	highest = filter(lambda x: enemy_drones_board[x] > 4, enemy_drones_board.keys())
	area = {}   # calculate drone passing density in area
	for loc in highest[:]:
		near = [(loc[0]+x[0], loc[1]+x[1]) for x in range3]
		near_in_range = filter(lambda x: 0 <= x[0] < rows and 0 <= x[1] < cols, near)
		area[loc] = sum(map(lambda x: enemy_drones_board[x], near_in_range))
	# find place with biggest area density
	max = -1
	max_loc = (-1, -1)
	for loc in area:
		if area[loc] > max:
			max = area[loc]
			max_loc = loc
		# if two spaces have the same drone area density, pick the one with highest drone density on it
		if abs(area[loc] - max) < 0.2 and grid[(loc[0],loc[1])] > grid[(max_loc[0],max_loc[1])]:
			max_loc = loc
	if max_loc != (-1,-1):
		debug(game, "Enemy is stacking at "+str(max_loc))
	return max_loc
#Checks if pirate hanst move from spawn location, used specificlly against a challenge bot in week 2
def not_moving(pirate):
	highest = filter(lambda x: danger_board[x] > 15, danger_board)
	for loc in highest[:]:
		if Location(loc[0], loc[1]).distance(pirate) > 1:
			highest.remove(loc)
	return len(highest) > 0
#Finds best city to rush
def target_city(game, stack_location):
	best_score = 9999999
	best_city = None
	for city in game.get_my_cities() + game.get_neutral_cities():
		score = city.distance(stack_location)/city.value_multiplier
		if score < best_score:
			best_city = city
			best_score = score
	return best_city
#For turning on and off printing to console easily (done with the constanst DEBUG which appears in the beginning of the file)
def debug(game, message):
	if DEBUG:
		game.debug(message)

def choose_state(game):
	global game_state
	global EARLY_TURNS

	if len(game.get_my_cities()+game.get_neutral_cities()) == 0:
		game_state = "CONTROL"
		return

	drones = game.get_my_living_drones()
	if game.get_max_drones_count() == 1:
		game_state = "CONTROL"
		return

	if game.get_turn() == 1:
		EARLY_TURNS = math.ceil(game.get_my_living_pirates()[-1].distance(game.get_not_my_islands()[min(len(game.get_not_my_islands())-1, 3)])/2.0) + 3
	score_to_win = game.get_max_points()
	my_score = game.get_my_score()
	diff = score_to_win - my_score
	if len(game.get_neutral_cities()) != 0:
		diff /= 2

	if game.get_turn() < EARLY_TURNS and len(game.get_my_islands()) == 0:
		game_state = "EARLY"
	# line 1 of if - states to rush drom
	# line 2 - 
	elif (game_state == "STACK" or game_state == "RUSH") and \
			((len(drones) >= diff*MIN_STACK_MULT or len(drones)==game.get_max_drones_count()) or \
			(game_state == "RUSH" and len(drones) > 5)) : 
		if game.get_myself().decoy is None:
			if game_state == "RUSH" or game.get_myself().turns_to_decoy_reload <= 2:
				game_state = "RUSH"
		else:
			game_state = "RUSH"
	elif is_defensive(game) or game_state == "STACK":
		game_state = "STACK"
	else:
		game_state = "CONTROL"

	debug(game, game_state)