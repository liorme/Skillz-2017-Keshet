from utility import *
from battles import *
from Pirates import *
from shared import *
import math

PIRATE = 0
DRONE = 1
NO_ATTACK = -1
RUSH_RADIUS = 8

class Attack:
	def __init__(self, attacker, target, target_type):
		self._attacker = attacker
		self._target = target
		self._target_type = target_type

	def get_attacker(self):
		return self._attacker

	def get_target(self):
		return self._target

	def get_target_type(self):
		return self._target_type

def handle_pirates(game, game_state, battles):
	# Get information
	global enemy_drones_board
	my_drones = game.get_my_living_drones()
	all_islands = game.get_all_islands()
	my_islands = game.get_my_islands()
	pirates = game.get_my_living_pirates()
	islands = game.get_not_my_islands()
	enemy_pirates = game.get_enemy_living_pirates()
	enemy_drones = game.get_enemy_living_drones()
	enemy_health = {}
	semi_used_pirates = []
	decoyed = False

	# Get a list of enemy pirates health for try_attack
	for enemy in enemy_pirates[:]:
		enemy_health[enemy] = enemy.current_health
		if not_moving(enemy):
			enemy_pirates.remove(enemy)

	# make a decoy
	if game_state == "RUSH" and len(pirates) > 0:
		move = best_move(pirates, game.get_my_cities())
		to_decoy = move.get_aircraft()
		if move.get_dist() < 8 and not decoyed:
			if try_decoy(to_decoy, game):
				pirates.remove(to_decoy)
				decoyed = True

	# Try attacking, and updating battles
	for pirate in pirates[:]:
		attack = try_attack(pirate, enemy_health, enemy_drones, game)
		if attack.get_target_type() != NO_ATTACK:
			if attack.get_target_type() == DRONE:
				semi_used_pirates.append(attack.get_attacker())
				enemy_drones.remove(attack.get_target())
				pirates.remove(attack.get_attacker())
			elif attack.get_target_type() == PIRATE:
				if is_new_battle(attack):
					create_new_battle(attack, game)
				pirates.remove(attack.get_attacker())

	"""
	enemy_stack = is_stacking(game)
	if enemy_stack != (-1,-1) and False:
		move = best_move(pirates, [Location(enemy_stack[0],enemy_stack[1])])
		if move.get_aircraft() != 0:
			sail = optimize_pirate_moves(game, move.get_aircraft(), move.get_location())
			game.set_sail(move.get_aircraft(), sail)
			pirates.remove(move.get_aircraft())
	"""


	# If I don't have a city, just guard and kill drones
	if len(game.get_my_cities() + game.get_neutral_cities()) == 0:
		for pirate in pirates[:]:
			move = best_move([pirate], enemy_drones)
			if move.get_aircraft() == 0 or move.get_dist() > 6:
				sail_options = game.get_sail_options(pirate, target_city(game, pirate.location))
				game.set_sail(pirate, sail_options[0])
				pirates.remove(pirate)
				continue
			sailing = game.get_sail_options(pirate, move.get_location())
			game.set_sail(move.get_aircraft(), sailing[0])
			pirates.remove(move.get_aircraft())
			enemy_drones.remove(move.get_location())

	# Try helping battles, but ignore battles when rushing
	if game_state != "RUSH":
		for battle in battles:
			for pirate in pirates[:]:
				if math.ceil((pirate.distance(battle.get_enemy_location_pirate()) - 2) / 2.0) <= \
								battle._turns_remaining - 1 and len(battle._helping_pirates) < 2:
					if not pirate in semi_used_pirates and not decoyed:
						if try_decoy(pirate, game):
							pirates.remove(pirate)
							battle._helping_pirates.append(pirate)
							decoyed = True
					else:
						# debug(game, "Pirate: " + str(pirate.id) + " is helping with a battle!")
						sail_options = game.get_sail_options(pirate, battle.get_enemy_location_pirate())
						if not pirate in semi_used_pirates: game.set_sail(pirate, sail_options[len(sail_options) / 2])
						pirates.remove(pirate)
						battle._helping_pirates.append(pirate)


	# If early in the game rush bottom middle island with 4 pirates and upper right/left island with 1 pirate
	if game_state == "EARLY":
		if len(all_islands) > 0:
			i = 0
			for pirate in pirates[:]:
				if i == 0:
					idx = min(len(all_islands)-1, 1 + game.get_myself().id)
				else:
					idx = min(len(all_islands)-1, 3)
				sail_options = game.get_sail_options(pirate, all_islands[idx])
				game.set_sail(pirate, sail_options[len(sail_options) / 2])
				pirates.remove(pirate)
				i += 1

	# Rushing with the stack and pirates towards the enemies that are closest to the city
	elif game_state == "RUSH":
		rush_pirates = 0
		max_stack = 0
		stack_location = get_current_stack_location(game)
		stack_location = Location(stack_location.row, stack_location.col + 2 - 4 * game.get_myself().id)
		scary_terry = best_move(enemy_pirates, [stack_location])
		while rush_pirates < 2 and len(pirates) > 0:
			if scary_terry.get_dist() < RUSH_RADIUS:
				move = best_move(pirates, [scary_terry.get_aircraft()])
				sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
				if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
				pirates.remove(move.get_aircraft())
			else:
				move = best_move(pirates, [stack_location])
				sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location())
				if not pirate in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
				pirates.remove(move.get_aircraft())
			rush_pirates += 1

		"""
		for pirate in pirates:
			if scary_terry.get_dist() < RUSH_RADIUS:
				sailing = optimize_pirate_moves(game, pirate, scary_terry.get_aircraft().location)
				if not pirate in semi_used_pirates: game.set_sail(pirate, sailing)
			else:
				sailing = optimize_pirate_moves(game, pirate, stack_location)
				if not pirate in semi_used_pirates: game.set_sail(pirate, sailing)
		"""

	# Try to get islands, kill drones, kill pirates, and gain map control in general
	if len(pirates) > 0:
		protect_drones = 0
		defend_islands = 0
		check_battles = 0
		k = 0
		defend = 0
		max_stack = 0
		drone_stack = [Location(0,0)]
		attack_pirates_relative_to_islands = 0
		find_max_stack = 0
		low_hp_pirates = []
		low_hp_check = 0
		attacked_pirates = {}
		defend_pirates = 0
		for enemy in enemy_pirates:
			attacked_pirates[enemy.id] = 0
		drones_close_to_city = []
		for drone in enemy_drones:
			move = best_move([drone], game.get_enemy_cities() + game.get_neutral_cities())
			if move.get_dist() < 15:
				drones_close_to_city.append(drone)
				enemy_drones.remove(drone)
		while len(pirates) > 0:
			enemy_next_move = None
			# Defend the point where the drones stack if an enemy is near it
			if protect_drones == 0 and game_state == "STACK":
				for enemy in enemy_pirates:
					if len(pirates) == 0:
						break
					if enemy.distance(ave_destination) < 10:
						move = best_move(pirates, [enemy])
						sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
						if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
						pirates.remove(move.get_aircraft())
						defend += 1
				protect_drones += 1


			elif len(drones_close_to_city) > 0 and defend_pirates < 1:
				move = best_move(pirates, drones_close_to_city)
				drone_city = best_move([move.get_location()], game.get_enemy_cities() + game.get_neutral_cities())
				if math.ceil(move.get_aircraft().distance(drone_city.get_location())/2.0) - 3 < drone_city.get_dist():
					sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
					if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
					pirates.remove(move.get_aircraft())
					defend_pirates += 1
				drones_close_to_city.remove(move.get_location())

			# Chooses the pirate that is closest to an island and sends him towards the island
			elif len(islands) > 0:
				move = best_move(pirates, islands)
				sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
				if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
				pirates.remove(move.get_aircraft())
				islands.remove(move.get_location())

			# Defend an island if an enemy is close and you can intercept him
			elif defend_islands == 0 and len(my_islands) > 0:
				best_blocking_pirate_move = [None, None, 9999999, None]
				for enemy_pirate in enemy_pirates:
					if len(pirates) == 0:
						break
					enemy_bm = best_move([enemy_pirate], my_islands)
					enemy_options = game.get_sail_options(enemy_pirate, enemy_bm.get_location())
					enemy_next_move = enemy_options[len(enemy_options) / 2]
					if enemy_bm.get_dist() < 6:
						min_dist = 9999999
						blocking_pirate = None
						# find closest pirate
						for pirate in pirates:
							if pirate.distance(enemy_bm.get_location()) < enemy_bm.get_dist() \
									and pirate.distance(enemy_pirate) < min_dist:
								# will die while trying to kill enemy pirate
								if enemy_health[enemy_pirate] > pirate.current_health:
									continue
								min_dist = pirate.distance(enemy_pirate)
								blocking_pirate = pirate
						if blocking_pirate is not None:
							if blocking_pirate.distance(enemy_pirate) < best_blocking_pirate_move[2]:
								best_blocking_pirate_move = [blocking_pirate, enemy_pirate,
															 blocking_pirate.distance(enemy_pirate),
															 enemy_bm.get_location()]

				if best_blocking_pirate_move[0] is not None:
					sailing = optimize_pirate_moves(game, best_blocking_pirate_move[0], enemy_next_move)
					if not best_blocking_pirate_move[0] in semi_used_pirates:
						game.set_sail(best_blocking_pirate_move[0], sailing)
					pirates.remove(best_blocking_pirate_move[0])
					debug(game, "ISLAND DEFENDED:")
					debug(game, "My Pirate " + str(best_blocking_pirate_move[0]))
					debug(game, "Enemy pirate: " + str(best_blocking_pirate_move[1]))
					debug(game, "Island defended: " + str(best_blocking_pirate_move[3]))
				defend_islands += 1

			#Defend city (CURRENTLY QUITE TERRIBLE TIMING IF I DO SAY SO MYSELF)
			elif defend == 0 and len(enemy_drones) > 6 and False:
				drone_move = best_move(enemy_drones, game.get_enemy_cities() + game.get_neutral_cities())
				if drone_move.get_dist() <= 11:
					move = best_move(pirates, [drone_move.get_aircraft()])
					sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
					if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
					pirates.remove(move.get_aircraft())
				else:
					destination = Location(int(math.floor(rows / 2)), int(10 + game.get_myself().id * (cols * 0.55)))
					move = best_move(pirates, [destination])
					sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location())
					if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
					pirates.remove(move.get_aircraft())
				defend += 1

			elif len(enemy_pirates) > 0 and False:
				if low_hp_check == 0:
					for pirate in pirates:
						if pirate.current_health < 3 and pirate not in semi_used_pirates:
							low_hp_pirates.append(pirate)
					low_hp_check += 1
				while len(low_hp_pirates) > 0:
					move = best_move(low_hp_pirates, enemy_pirates)
					sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
					game.set_sail(move.get_aircraft(), sailing)
					pirates.remove(move.get_aircraft())
					low_hp_pirates.remove(move.get_aircraft())



				# Chooses the pirate that is closest to an enemy drone and sends him towards that drone



			elif len(enemy_drones) > 0 or len(enemy_pirates) > 0:
				move = best_move(pirates, enemy_drones + enemy_pirates)
				sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
				if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
				pirates.remove(move.get_aircraft())
				if move.get_location() in enemy_drones:
					enemy_drones.remove(move.get_location())
				elif move.get_location() in enemy_pirates and attacked_pirates[move.get_location().id] > 1:
					enemy_pirates.remove(move.get_location())
				else:
					attacked_pirates[move.get_location().id] += 1


			elif max_stack > 0 or find_max_stack == 0:
				if find_max_stack == 0:
					for drone in my_drones:
						drones_in_location = [x for x in game.get_aircrafts_on(drone.location) if
											  x.max_speed == 1 and x.owner.id == game.get_myself().id]
						if len(drones_in_location) > max_stack:
							max_stack = len(drones_in_location)
							drone_stack = [drone.location]
							for d in drones_in_location:
								my_drones.remove(d)
						elif len(drones_in_location) == max_stack:
							drone_stack.append(drone.location)
							for d in drones_in_location:
								my_drones.remove(d)
					find_max_stack += 1
				move = best_move(pirates, drone_stack)
				sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location())
				if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
				pirates.remove(move.get_aircraft())

				# Sends pirates after enemy pirates
			elif len(enemy_pirates) > 0:
				# If controlling islands then send the pirate that is closest to one of
				# the islands towards an enemy pirate that is also closest to the island
				# Only calculates once and passes over all pirates
				if len(my_islands) > 0 and attack_pirates_relative_to_islands == 0:
					for pirate in pirates:
						closest_island = best_move([pirate], my_islands)
						closest_enemy = best_move(game.get_enemy_living_pirates(), [closest_island.get_location()])
						if pirate.distance(closest_enemy.get_aircraft()) < 10:
							sailing = optimize_pirate_moves(game, pirate, closest_enemy.get_aircraft().location)
							if not pirate in semi_used_pirates: game.set_sail(pirate, sailing)
							pirates.remove(pirate)
					attack_pirates_relative_to_islands += 1
				# If not controlling islands then choose the pirate and enemy pirate with smallest distance between them
				# and send him there, calculates for one pirate each pass
				else:
					move = best_move(pirates, enemy_pirates)
					sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
					if not move.get_aircraft() in semi_used_pirates: game.set_sail(move.get_aircraft(), sailing)
					pirates.remove(move.get_aircraft())
					enemy_pirates.remove(move.get_location())
			# If all else fails, go to the middle of the map so you dont crash
			else:
				destination = Location(int(math.floor(rows / 2)), int(math.floor(cols / 2)))
				sailing = optimize_pirate_moves(game, pirates[0], destination)
				if not pirates[0] in semi_used_pirates: game.set_sail(pirates[0], sailing)
				pirates.remove(pirates[0])


def handle_decoy(game, game_state):
	decoy = game.get_myself().decoy
	if decoy and game_state == "RUSH":
		max_stack = 0
		stack_location = Location(0, 0)
		for drone in game.get_my_living_drones():
			if len(game.get_aircrafts_on(drone.location)) > max_stack:
				max_stack = len(game.get_aircrafts_on(drone.location))
				stack_location = drone.location
		stack_location = Location(stack_location.row, stack_location.col + 2 - 4 * game.get_myself().id)
		scary_terry = best_move(game.get_enemy_living_pirates(), [stack_location])
		if scary_terry.get_dist() < RUSH_RADIUS:
			sailing = optimize_pirate_moves(game, decoy, scary_terry.get_aircraft().location)
			game.set_sail(decoy, sailing)
		else:
			sailing = optimize_pirate_moves(game, decoy, stack_location)
			game.set_sail(decoy, sailing)
	elif decoy:
		for battle in battles:
			if math.ceil((decoy.distance(battle.get_enemy_location_pirate()) - 2) / 2.0) <= battle._turns_remaining - 1:
				# debug(game, "Pirate: " + str(pirate.id) + " is helping with a battle!")
				sail_options = game.get_sail_options(decoy, battle.get_enemy_location_pirate())
				game.set_sail(decoy, sail_options[len(sail_options) / 2])
				decoy = None
				break
		if decoy:
			move = best_move([decoy], game.get_enemy_living_pirates())
			sail_options = game.get_sail_options(move.get_aircraft(), move.get_location())
			game.set_sail(move.get_aircraft(), sail_options[len(sail_options)/2])

#Tries to attack the pirate with lowerst health, then drones
def try_attack(pirate, enemy_health, enemy_drones, game):
	# Find which pirates are in my range
	in_range_pirates = []
	for enemy_pirate in game.get_enemy_living_pirates():
		if pirate.in_attack_range(enemy_pirate) and enemy_health[enemy_pirate] > 0:
			in_range_pirates.append(enemy_pirate)
	# If pirates are in range then attack the one with the lowest health
	if len(in_range_pirates) > 0:
		min_health = 9999999
		best_target = 0
		for enemy_pirate in in_range_pirates:
			if enemy_pirate.current_health < min_health:
				min_health = enemy_pirate.current_health
				best_target = enemy_pirate
		enemy_health[best_target] -= 1
		game.attack(pirate, best_target)
		return Attack(pirate, best_target, PIRATE)

	for enemy_drone in enemy_drones:
		if pirate.in_attack_range(enemy_drone):
			game.attack(pirate, enemy_drone)
			return Attack(pirate, enemy_drone, DRONE)
	return Attack(None, None, NO_ATTACK)

#Checks if decoy is off cooldown
def try_decoy(pirate, game):
	if pirate.owner.turns_to_decoy_reload == 0:
		game.decoy(pirate)
		return True
	return False

def optimize_pirate_moves(game, pirate, destination):
	"""
	Returns the move currently needed to move pirate toward destination, while going through
	the area most likely to contain drones (according to past drone behaivor).
	This function is used to make a move toward a destination (island, enemy pirate,..) more likely
	to bring the pirate close to drones, while not straying out of the path.

	:param game: pirate game
	:param pirate: pirate that wants to move
	:param destination: target of pirate
	:return: best_option - sailing option (one of the options returned by get_sail_options)
	"""


	global enemy_drones_board
	global rows, cols
	sail_options = game.get_sail_options(pirate, destination)
	max_value = -100
	best_option = None
	for option in sail_options:
		option_value = 0
		for row in xrange(min(option.row, destination.row) - 1, max(option.row, destination.row) + 2):
			for col in xrange(min(option.col, destination.col) - 1, max(option.col, destination.col) + 2):
				if 0 <= row < rows and 0 <= col < cols:
					option_value += enemy_drones_board[(row, col)]
		option_value -= int(math.hypot(option.row - math.floor(rows / 2), option.col - math.floor(cols / 2)))
		if option_value > max_value:
			max_value = option_value
			best_option = option
	return best_option