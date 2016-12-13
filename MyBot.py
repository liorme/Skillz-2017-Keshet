"""
This is an example for a bot.
"""
from Pirates import *
import random


def do_turn(game):
    """
    Makes the bot run a single turn

    :param game: the current game state
    :type game: PiratesGame
    """
    # Give orders to my pirates
    handle_pirates(game)
    # Give orders to my drones
    handle_drones(game)


def handle_pirates(game):
	# Go over all of my pirates
    moves = []
    pirates = game.get_my_living_pirates()
    islands = game.get_not_my_islands()
    enemy_drones = game.get_enemy_living_drones()
    enemy_ships = game.get_enemy_living_pirates()
    for pirate in pirates:
        if try_attack(pirate, game):
            pirates.remove(pirate)
    while len(pirates) > 0:
        if len(islands) > 0:
            moves = []
            for pirate in pirates:
                min_dist = sys.maxint
                closest_island = 0
                for island in islands:
                    if pirate.distance(island) < min_dist:
                        min_dist = pirate.distance(island)
                        closest_island = island
                move = [pirate, closest_island, min_dist]
                moves.append(move)
            min_move = [0,0,sys.maxint]
            for move in moves:
                if move[2] < min_move[2]:
                    min_move = move
            sail_options = game.get_sail_options(min_move[0], min_move[1])
            game.set_sail(min_move[0], sail_options[0])
            if pirates.count(min_move[0]) == 1: pirates.remove(min_move[0])
            if islands.count(min_move[1]) == 1: islands.remove(min_move[1])


        elif len(enemy_drones) > 0:
            moves = []
            for pirate in pirates:
                min_dist = sys.maxint
                closest_drone = 0
                for drone in enemy_drones:
                    if pirate.distance(drone) < min_dist:
                        min_dist = pirate.distance(drone)
                        closest_drone = drone
                move = [pirate, closest_drone, min_dist]
                moves.append(move)
            min_move = [0,0,sys.maxint]
            for move in moves:
                if move[2] < min_move[2]:
                    min_move = move
            sail_options = game.get_sail_options(min_move[0], min_move[1])
            game.set_sail(min_move[0], sail_options[0])
            if pirates.count(min_move[0]) == 1: pirates.remove(min_move[0])
            if enemy_drones.count(min_move[1]) == 1: enemy_drones.remove(min_move[1])


        elif len(enemy_ships) > 0:
            moves = []
            for pirate in pirates:
                min_dist = sys.maxint
                closest_ship = 0
                for ship in enemy_ships:
                    if pirate.distance(ship) < min_dist:
                        min_dist = pirate.distance(ship)
                        closest_ship = ship
                move = [pirate, closest_ship, min_dist]
                moves.append(move)
            min_move = [0,0,sys.maxint]
            for move in moves:
                if move[2] < min_move[2]:
                    min_move = move
            sail_options = game.get_sail_options(min_move[0], min_move[1])
            game.set_sail(min_move[0], sail_options[0])
            if pirates.count(min_move[0]) == 1: pirates.remove(min_move[0])
            if enemy_ships.count(min_move[1]) == 1: enemy_ships.remove(min_move[1])
        

        else:
            destination = Location(23,23)
            sail_options = game.get_sail_options(pirates[0], destination)
            game.set_sail(pirates[0], sail_options[0])
            pirates.remove(pirates[0])



"""
        else:
            gathered_pirates = []
            for j in pirates:
                if j.location == pirates[0].location: gathered_pirates.append(j)
            if len(gathered_pirates)>1:
                for j in gathered_pirates:
                    min_dist = sys.maxint
                    closest_ship = 0
                    for ship in enemy_ships:
                        if pirate.distance(ship) < min_dist:
                            min_dist = pirate.distance(ship)
                            closest_ship = ship
                    move = [j, closest_ship, min_dist]
                    destination = move[1]
                    sail_options = game.get_sail_options(j, destination)
                    game.set_sail(j, sail_options[0])
                    pirates.remove(j)

            else:
                destination = Location(23,23)
                sail_options = game.get_sail_options(pirates[0], destination)
                game.set_sail(pirates[0], sail_options[0])
                pirates.remove(pirates[0])
"""







"""
	processed_islands = []
	for pirate in game.get_my_living_pirates():
        # Try to attack, if you didn't - move to an island
		if not try_attack(pirate, game):
			# Choose destination
			destinations = game.get_not_my_islands()
			if len(processed_islands) != 0:
				for i in processed_islands:
					if destinations.count(i) != 0:destinations.remove(i)
			if len(destinations)>0:destination = destinations[0]
			else:destination = Location(23,23)
			processed_islands.append(destination)
			# Get sail options
			sail_options = game.get_sail_options(pirate, destination)
			# Set sail!
			game.set_sail(pirate, sail_options[0])
			# Print a message
			#game.debug('pirate ' + str(pirate) + ' sails to ' + str(sail_options[0]))
"""

def handle_drones(game):
    """
    Gives orders to my drones

    :param game: the current game state
    :type game: PiratesGame
    """
    # Go over all of my drones
    for drone in game.get_my_living_drones():
        # Choose a destination
        destination = game.get_my_cities()[0]
        # Get sail options
        sail_options = game.get_sail_options(drone, destination)
        # Set sail!
        sail_option = random.randint(0, (len(sail_options) - 1))
        game.set_sail(drone, sail_options[sail_option])


def try_attack(pirate, game):
    """
    Makes the pirate try to attack. Returns True if it did.

    :param pirate: the attacking pirate
    :type pirate: Pirate
    :param game: the current game state
    :type game: PiratesGame
    :return: True if the pirate attacked
    :rtype: bool
    """
    # Go over all enemies
    for enemy in game.get_enemy_living_aircrafts():
        # Check if the enemy is in attack range
        if pirate.in_attack_range(enemy):
            # Fire!
            game.attack(pirate, enemy)
            # Print a message
            #game.debug('pirate ' + str(pirate) + ' attacks ' + str(enemy))
            # Did attack
            return True

    # Didn't attack
    return False

