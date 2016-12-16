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
            min_move = best_move(pirates, islands)
            sail_options = game.get_sail_options(min_move[0], min_move[1])
            game.set_sail(min_move[0], sail_options[(len(sail_options) / 2)])
            if pirates.count(min_move[0]) == 1: pirates.remove(min_move[0])
            if islands.count(min_move[1]) == 1: islands.remove(min_move[1])


        elif len(enemy_drones) > 0:
            min_move = best_move(pirates, enemy_drones)
            sail_options = game.get_sail_options(min_move[0], min_move[1])
            game.set_sail(min_move[0], sail_options[(len(sail_options) / 2)])
            if pirates.count(min_move[0]) == 1: pirates.remove(min_move[0])
            if enemy_drones.count(min_move[1]) == 1: enemy_drones.remove(min_move[1])


        elif len(enemy_ships) > 0:
            min_move = best_move(pirates, enemy_ships)
            sail_options = game.get_sail_options(min_move[0], min_move[1])
            game.set_sail(min_move[0], sail_options[(len(sail_options) / 2)])
            if pirates.count(min_move[0]) == 1: pirates.remove(min_move[0])
            if enemy_ships.count(min_move[1]) == 1: enemy_ships.remove(min_move[1])


        else:
            destination = Location(23, 23)
            sail_options = game.get_sail_options(pirates[0], destination)
            game.set_sail(pirates[0], sail_options[(len(sail_options) / 2)])
            pirates.remove(pirates[0])

		
def handle_drones(game):
    global drones_state
    living_drones = game.get_my_living_drones()
    if len(living_drones) < 30 and game.get_max_turns()- game.get_turn() > 10 and drones_state != 1:
        for drone in living_drones:
            # Choose a destination
            destination = Location(24,17)
            # Get sail options
            sail_options = game.get_sail_options(drone, destination)
            # Set sail!
            sail_option = random.randint(0, (len(sail_options) - 1))
            game.set_sail(drone, sail_options[sail_option])
    else:
        drones_state = 1
        for drone in living_drones:
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
            # game.debug('pirate ' + str(pirate) + ' attacks ' + str(enemy))
            # Did attack
            return True

    # Didn't attack
    return False

def best_move(pirates, list):
    moves = []
    for pirate in pirates:
        min_dist = sys.maxint
        closest_aircraft = 0
        for aircraft in list:
            if pirate.distance(aircraft) < min_dist:
                min_dist = pirate.distance(aircraft)
                closest_aircraft = aircraft
        move = [pirate, closest_aircraft, min_dist]
        moves.append(move)
    min_move = [0, 0, sys.maxint]
    for move in moves:
        if move[2] < min_move[2]:
            min_move = move
    return min_move
