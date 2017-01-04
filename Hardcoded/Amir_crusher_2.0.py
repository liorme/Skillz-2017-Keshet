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
    stack_point = Location(my_city_loc.row + 5, my_city_loc.col - 2)
    handle_pirates(game)
    # Give orders to my drones
    handle_drones(game)


def handle_pirates(game):
    """
    Gives orders to my pirates

    :param game: the current game state
    :type game: PirateGame
    """
    # Go over all of my pirate
    enemy_city = game.get_enemy_cities()[0]
    islands_to_take = game.get_not_my_islands()
    for pirate in game.get_my_living_pirates():
        if not try_attack(pirate, game):
            destination = find_closest_island(pirate, islands_to_take)
            if destination is None:  # TODO find better option
                destination = enemy_city
            move_ops = get_move_options_towards(pirate, destination.location, game.get_pirate_max_speed(), game)
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


def get_move_options_towards(aircraft, destination, max_speed, game):
    """
    gets all move options that get aircraft closer to destination
    :param aircraft: aircraft to move
    :type aircraft: Aircraft
    :param destination: where we want to go
    :type destination: MapObject
    :param max_speed: how far can aircraft go
    :type max_speed: int
    :param game: current game state
    :type game: PirateGame
    :return: list of all moves that get me closer to destination
    :rtype list[Location]
    """
    aircraft_loc = aircraft.location
    row = aircraft_loc.row
    col = aircraft_loc.col
    options = []
    for i in range(max_speed + 1):
        options.append(Location(row + i, col + (max_speed - i)))
        options.append(Location(row - i, col - (max_speed - i)))
        if i != 0 and i != max_speed:
            options.append(Location(row + i, col - (max_speed - i)))
            options.append(Location(row - i, col + (max_speed - i)))

    options = filter(lambda x: 0 <= x.row < game.get_row_count() and 0 <= x.col < game.get_col_count(), options)
    current_distance = aircraft.distance(destination)
    closer_ops = filter(lambda x: destination.distance(x) < current_distance, options)
    if len(closer_ops) == 0:
        closer_ops = [aircraft_loc]  # if can't get closer stay in place
    return closer_ops


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
        poss_moves = get_move_options_towards(drone, destination, game.get_drone_max_speed(), game)
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
