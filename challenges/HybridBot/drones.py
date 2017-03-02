from utility import *
from Pirates import *
from shared import *
import math
import random

SPAWN_LOCATION_PRIORITY_FOR_STACK_LOCATION = 2
WAIT_WITH_RUSH_FOR_DRONES_IN_RANGE = 3
DANGER_COST = 5

drones_plans = []


def handle_drones(game, game_state):
	global drones_plans
	global rows, cols
	drones = game.get_my_living_drones()
	living_drones_ids = [drone.id for drone in drones]
	islands_locations = [island.location for island in game.get_my_islands()]
	enemy_pirates = game.get_enemy_living_pirates()

	# dodging enemy pirates while there are drones in danger
	checked = False
	while game_state != "RUSH":
		while not checked:
			drone_move = best_move(drones, game.get_my_cities() + game.get_neutral_cities())
			if drone_move.get_dist() < game.get_unload_range() + 5:
				sail_options = game.get_sail_options(drone_move.get_aircraft(), drone_move.get_location())
				sailing = optimize_drone_moves(sail_options, game)
				game.set_sail(drone_move.get_aircraft(), sailing)
				drones.remove(drone_move.get_aircraft())
				living_drones_ids.remove(drone_move.get_aircraft().id)
			else:
				checked = True

		escaping_info = best_move(drones, enemy_pirates)
		if escaping_info.get_dist() > 6:
			break
		x = escaping_info.get_aircraft().location.row
		y = escaping_info.get_aircraft().location.col
		options = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
		for p in options[:]:
			if p[0] < 0 or p[0] > rows or p[1] < 0 or p[1] > cols:
				options.remove(p)
				continue
			if best_move([Location(p[0], p[1])], enemy_pirates).get_dist() < escaping_info.get_dist():
				options.remove(p)
				continue
		if len(options) == 0:
			row = min(rows - 1,
					  max(2 * escaping_info.get_aircraft().location.row - escaping_info.get_location().location.row, 0))
			col = min(cols - 1,
					  max(2 * escaping_info.get_aircraft().location.col - escaping_info.get_location().location.col, 0))
			goto = (row, col)
		else:
			goto = random.choice(options)
		sail_options = game.get_sail_options(escaping_info.get_aircraft(), Location(goto[0], goto[1]))
		sailing = optimize_drone_moves(sail_options, game)
		game.set_sail(escaping_info.get_aircraft(), sailing)
		drones.remove(escaping_info.get_aircraft())
		# living_drones_ids.remove(escaping_info.get_aircraft().id)
		# debug(game, "ESCAPE: "+str(escaping_info.get_aircraft()))

	if game_state == "CONTROL":
		# making new plans
		for drone in drones:
			target = target_city(game, drone.location)
			if drone.location in islands_locations or drone.id not in map(lambda x: x['id'], drones_plans):
				new_plan = GPS(game, drone, target.location)
				drones_plans.append({"id": drone.id, "steps": new_plan})
			if game.get_time_remaining() < 10:
				break

		# plan isn't relevant (drone killed or moved away from path)
		for plan in drones_plans[:]:
			if plan["steps"] != [] and plan["id"] in living_drones_ids:
				drone = game.get_my_drone_by_id(plan["id"])
				if abs(drone.location.row - plan["steps"][0][0]) == 1 and abs(
								drone.location.col - plan["steps"][0][1]) == 0:
					continue
				elif abs(drone.location.row - plan["steps"][0][0]) == 0 and abs(
								drone.location.col - plan["steps"][0][1]) == 1:
					continue
				elif game.get_time_remaining() > -40:
					drones_plans.remove(plan)
					target = target_city(game, drone.location)
					new_plan = GPS(game, drone, target.location)
					drones_plans.append({"id": drone.id, "steps": new_plan})
				else:
					drones_plans.remove(plan)

		#debug(game, "Num of drones: "+str(len(drones))+' '+str(len(game.get_my_living_drones())))
		#debug(game, "We have plans for "+str(len(drones_plans))+' drones')
		# executing drones planes
		for plan in drones_plans:
			if plan["steps"] != [] and plan["id"] in living_drones_ids:
				drone = game.get_my_drone_by_id(plan["id"])
				next_step = Location(plan["steps"][0][0], plan["steps"][0][-1])
				if drone in drones[:]:
					drones.remove(drone)
					game.set_sail(drone, next_step)
				plan["steps"] = plan["steps"][1:]

	# Find the average position of my pirates and the left/right wall,
	# and send the drones there. If enemy pirate is close to point then move point closer to spawn point
	if game_state == "STACK":
		ave_destination = set_stack_location(game)
		city_to_rush = target_city(game,ave_destination)
		for drone in drones:
			# For each drone if the distance to the city is way smaller then the distance to stack point then go to city
			if drone.distance(city_to_rush) * 2 < drone.distance(ave_destination):
				sail_options = game.get_sail_options(drone, city_to_rush)
				sail = optimize_drone_moves(sail_options, game)
				game.set_sail(drone, sail)
			else:
				sail_options = game.get_sail_options(drone, ave_destination)
				sail = optimize_drone_moves(sail_options, game)
				game.set_sail(drone, sail)

	#Just go towards my city
	elif game_state == "EARLY":
		for drone in drones:
			destination = target_city(game, drone.location)
			sail_options = game.get_sail_options(drone, destination)
			sail = optimize_drone_moves(sail_options, game)
			game.set_sail(drone, sail)

	# Just go towards my city >?>@!@
	elif game_state == "RUSH":
		near_drones = check_near_stack_drones(game)
		if len(near_drones) > 0:
			stack = get_current_stack_location(game)
			for drone in near_drones:
				sail_options = game.get_sail_options(drone, stack)
				sail = optimize_drone_moves(sail_options, game)
				game.set_sail(drone, sail)
		else:
			for drone in drones:
				destination = target_city(game, drone.location)
				sail_options = game.get_sail_options(drone, destination)
				sail = optimize_drone_moves(sail_options, game)
				game.set_sail(drone, sail)

#Finds the location with the biggest stack of friendly droens
def get_current_stack_location(game):
	my_drones = game.get_my_living_drones()
	max_stack = 0
	stack_drone = Location(0,0)
	#Find where the largest stack (or stacks if a few equal size stacks) is
	for drone in my_drones:
		drones_in_location = [x for x in game.get_aircrafts_on(drone.location) if type(x).__name__ == "Drone" and x.owner.id == game.get_myself().id]
		if len(drones_in_location) > max_stack:
			max_stack = len(drones_in_location)
			stack_drone = [drone.location]
			for d in drones_in_location:
				my_drones.remove(d)
		elif len(drones_in_location) == max_stack:
			stack_drone.append(drone.location)
			for d in drones_in_location:
				my_drones.remove(d)
	return stack_drone[0]
#Sets the stack location factoring into account: friendly pirates, enemy_cities, friendly pirates spawn locations(with the added weight of SPAWN_LOCATION_PRIORITY_FOR_STACK_LOCATION)
def set_stack_location(game):
	dest_row = 0
	dest_col = 0
	ave_destination = Location(0,0)
	for pirate in game.get_my_living_pirates():
		dest_row += pirate.initial_location.row*SPAWN_LOCATION_PRIORITY_FOR_STACK_LOCATION
		dest_col += pirate.initial_location.col*SPAWN_LOCATION_PRIORITY_FOR_STACK_LOCATION
		dest_row += pirate.location.row
		dest_col += pirate.location.col
	for city in game.get_enemy_cities():
		dest_row += city.location.row
		dest_col += city.location.col
	dest_row = dest_row / (len(game.get_my_living_pirates()) + len(game.get_all_my_pirates())*SPAWN_LOCATION_PRIORITY_FOR_STACK_LOCATION + len(game.get_enemy_cities()))
	dest_col = dest_col / (len(game.get_my_living_pirates()) + len(game.get_all_my_pirates())*SPAWN_LOCATION_PRIORITY_FOR_STACK_LOCATION + len(game.get_enemy_cities()))
	ave_destination.row = dest_row
	ave_destination.col = dest_col
	return ave_destination

#finds drones near the current stack location, in a range determined by WAIT_WITH_RUSH_FOR_DRONES_IN_RANGE
def check_near_stack_drones(game):
	#For now just using the first largest stack, should usually be only one anyway in this context (stacking and rushing)
	stack = get_current_stack_location(game)
	my_drones = game.get_my_living_drones()
	near_drones = []
	for drone in my_drones:
		if drone.distance(stack) <= WAIT_WITH_RUSH_FOR_DRONES_IN_RANGE and drone.distance(stack) != 0:
			near_drones.append(drone)

#Chooses the best sailing option, by checking proximity to enemy pirates, and if irrelevant, the path needed to take to travel diagonally to destination(I THINK!!)
def optimize_drone_moves(sail_options, game):
	if len(sail_options) == 1:
		return sail_options[0]

	move1 = best_move([sail_options[0]], game.get_enemy_living_pirates())
	move2 = best_move([sail_options[1]], game.get_enemy_living_pirates())

	if move1.get_dist() > move2.get_dist() and move2.get_dist() < 10:
		return sail_options[0]
	elif move1.get_dist() < move2.get_dist() and move1.get_dist() < 10:
		return sail_options[1]

	if (sail_options[0].row - math.floor(rows / 2)) ** 2 + (sail_options[0].col - math.floor(cols / 2)) ** 2 > \
							(sail_options[1].row - math.floor(rows / 2)) ** 2 + (
				sail_options[1].col - math.floor(cols / 2)) ** 2:
		return sail_options[0]
	else:
		return sail_options[1]


# takes a drone and a destination, return the safes and shortest path
def GPS(game, drone, destination):
	# danger_board is a memory of all the places enem pirates have threatend
	global danger_board
	destination = (destination.row, destination.col)
	# creates a board by (row,col) that for each spot contains a dictionary its
	# 'index', the 'cost' to get there(infinity at the beginning),
	# the 'value' of beein there ('cost' plus min cost to get from there to destination)
	# and the shortest road to this point that is currently known(empty in the beginning)
	board = {}
	for row in xrange(rows):
		for col in xrange(cols):
			board[(row, col)] = {'index': (row, col), 'cost': 10 ** 99, 'value': 10 ** 99, 'road': []}
	# sets the drones location to be 'cost' 0 and 'value' 0

	board[(drone.location.row, drone.location.col)]['cost'] = 0
	board[(drone.location.row, drone.location.col)]['value'] = \
		0 + abs(drone.location.row - destination[0]) + abs(drone.location.col - destination[-1])
	# creates a list of points we know how to get to and that are not yet checked,
	# this list will be sorted by the points values
	needs_checking = [board[(drone.location.row, drone.location.col)]]
	# next_to is a list of the 4 directions, in an efficient order according to your team
	if game.get_myself().id == 0:
		next_to = [(0, -1), (1, 0), (0, 1), (-1, 0)]
	else:
		next_to = [(0, 1), (1, 0), (0, -1), (-1, 0)]
	while True:
		tile = needs_checking[0]  # setting the tile with the best value to be the one we are checking
		if tile['index'] == destination:  # if this tile is the destination we return the road we found to this tile
			return board[destination]['road']
		needs_checking = needs_checking[1:]  # taking the tile we are checking out of needs_checking
		# we are checking all the tiles that next to the tile we are checking and
		# adding the road and the cost for this next_to_tile if its efficient to go the new tile
		for i in next_to:
			row = tile['index'][0] + i[0]
			col = tile['index'][-1] + i[-1]
			if 0 <= row < rows and 0 <= col < cols:  # checking that the next_to_tile is on the board
				# potential_cost is the cost to get to tile + the danger level times DANGER_COST plus
				# the turns it will take to get to this next tile (1)
				potential_cost = tile['cost'] + danger_board[(row, col)] * DANGER_COST + 1
				# checks if the potential_cost is lower then the cost that the tile hes
				if potential_cost < board[(row, col)]['cost']:
					b = 0  # checks it updates the new tile only once
					board[(row, col)]['cost'] = potential_cost  # setting the new cost
					board[(row, col)]['value'] = \
						potential_cost + abs(row - destination[0]) + abs(col - destination[-1])  # setting the new value
					board[(row, col)]['road'] = tile['road'] + [(row, col)]  # setting the new road
					for itsplace, unchecked in enumerate(
							needs_checking[:]):  # looping threw the needs_checking list and the indexes of it
						# if we looped and got to a place in list that the new tile hes less value(better):
						if b == 0 and unchecked['value'] >= board[(row, col)]['value']:
							needs_checking.insert(itsplace, board[
								(row, col)])  # we insert the the new_tile into the needs_checking list
							b = 1  # we make shor we wont add or insert it again
						if unchecked['index'] == (row, col) and unchecked['value'] != board[(row, col)][
							'value']:  # if the unchecked tile is a older version of the new_tile
							needs_checking.remove(unchecked)  # we remove it
					if b == 0:  # if we didnt inserted the new_tile yet (it hes the worst value)
						needs_checking.append(board[(row, col)])  # we append it ate the end of the needs_checking list

	return near_drones         