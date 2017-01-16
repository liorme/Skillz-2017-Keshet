"""
New Hardcoded Bot - Lior and Elool
"""

from Pirates import *
import random

# Constants
min_drone_stack = 15
stack_point = Location(0, 0)
CITY_CLEAR_RANGE = 4


def do_turn(game):
    """
    Makes the bot run a single turn

    :param game: the current game state
    :type game: PirateGame
    """
    # Give orders to my pirates
    my_city_loc = game.get_my_cities()[0].location
    global stack_point
    if game.get_turn_count() < 20:
        state = "EARLY"
    else:
        state = "MID"
    stack_point = Location(my_city_loc.row + 5, my_city_loc.col - 2)
    handle_pirates(game, state)
    # Give orders to my drones
    handle_drones(game, state)


def handle_pirates(game, state):
    """
    Gives orders to my pirates

    :param game: the current game state
    :type game: PirateGame
    """
    # Go over all of my pirate
    enemy_city = game.get_enemy_cities()[0]
    island = game.get_not_my_islands()
	drones = game.get_enemy_living_drones()
    for pirate in game.get_my_living_pirates():
        if state == "EARLY":
            if not try_attack(pirate, game):
                destination = find_closest_island(pirate, islands_to_take)
                if destination is None:  # TODO find better option
                    destination = Location(game.get_row_count()/2,game.get_col_count()/2)
			else:
				destination = find_closest_island(pirate, drones)
				if destination is None:
					destination = Location(game.get_row_count()/2,game.get_col_count()/2)
            move_ops = game.get_sail_options(pirate, destination)
            game.set_sail(pirate, random.choice(move_ops))


def find_closest_island(pirate, islands):
    """
    finds the closest island to this pirate
    :param pirate: pirate to find closest island
    :type pirate: Pirate
    :param islands: islands to choose closest from
    :type islands: list[Island]
    :return: the closest island to pirate
    :rtype: Island
    """
    if len(islands) == 0:
        return None
    dists = map(lambda x: x.distance(pirate), islands)
    smallest_dist = min(dists)
    idx = dists.index(smallest_dist)
    chosen = islands[idx]
    islands.remove(chosen)  # "mark" this island so other pirates won't go there
    return chosen


def is_my_city_clear(game):
    """
    checks whether an enemy pirate is near my city
    :param game: current game state
    :type game: PirateGame
    :return: whether an enemy pirate is near my city
    :rtype: bool
    """
    my_city = game.get_my_cities()[0]
    for pirate in game.get_enemy_living_pirates():
        if pirate.distance(my_city) <= CITY_CLEAR_RANGE:
            return False
    return True


def handle_drones(game):
    """
    Gives orders to my drones

    :param game: the current game state
    :type game: PiratesGame
    """
    drones_stacked = filter(lambda x: x.type == "drone" and x.owner == game.get_myself(),
                            game.get_aircrafts_on(stack_point))
    
    if is_my_city_clear(game) or len(drones_stacked) >= min_drone_stack:
        # send drones to city
        destination = game.get_my_cities()[0].location
    else:
        # send drones to stack location
        destination = stack_point

    for drone in game.get_my_living_drones():
        poss_moves = game.get_sail_options(drone, destination)
        move = random.choice(poss_moves)
        game.set_sail(drone, move)


def try_attack(pirate, game):
    """
    Makes the pirate try to attack. Returns True if it did.

    :param pirate: the attacking pirate
    :type pirate: Pirate
    :param game: the current game state
    :type game: PirateGame
    :return: True if the pirate attacked
    :rtype: bool
    """
    in_range = filter(lambda x: pirate.in_attack_range(x), game.get_enemy_living_aircrafts())
    if len(in_range) == 0:  # can't attack anyone:
        return False  # mark i din't attack
    in_range.sort(key=lambda x: x.current_health)
    target = min(in_range)
    game.attack(pirate, target)
    return True
