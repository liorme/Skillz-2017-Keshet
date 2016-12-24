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
    processed_islands = []
    for pirate in game.get_my_living_pirates():
        # Try to attack, if you didn't - move to an island
        if not try_attack(pirate, game):
            if pirate.id == 4:
                destination = Location(23,23)
                sail_options = game.get_sail_options(pirate, destination)
                game.set_sail(pirate, sail_options[0])
            else:
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
            game.debug('pirate ' + str(pirate) + ' attacks ' + str(enemy))
            # Did attack
            return True

    # Didn't attack
    return False

