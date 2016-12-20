from Pirates import *
import random
import sys

game_state = "STACK"
def do_turn(game):
    """
    :type game: PirateGame
    """
    # enter your code here:
    global game_state
    if len(game.get_my_living_drones()) > 25 or game.get_max_turns() - game.get_turn() <= 20:
        game_state = "PUSH"
        game.debug("PUSH")
    elif len(game.get_my_living_drones()) < 10:
        game_state = "STACK"
        game.debug("STACK")

    handle_pirates(game, game_state)
    handle_drones(game, game_state)


def handle_pirates(game, game_state):
    pirates = game.get_my_living_pirates()
    islands = game.get_not_my_islands()
    enemy_drones = game.get_enemy_living_drones()
    enemy_pirates = game.get_enemy_living_pirates()


    for pirate in pirates[:]:
        if try_attack(pirate, game):
            pirates.remove(pirate)

    if game_state == "PUSH":
        while len(pirates) > 0:
            if len(enemy_pirates):
                min_move = best_move(pirates, enemy_pirates)
                sail_options = game.get_sail_options(min_move[0], min_move[1])
                game.set_sail(min_move[0], sail_options[len(sail_options)/2])
                pirates.remove(min_move[0])
                enemy_pirates.remove(min_move[1])
            else:
                sail_options = game.get_sail_options(pirate, game.get_my_cities()[0])
                game.set_sail(pirate, sail_options[len(sail_options)/2])
                pirates.remove(pirates[0])

    elif game_state == "STACK":

        while len(pirates) > 0:

            if len(islands) > 0:
                min_move = best_move(pirates, islands)
                sail_options = game.get_sail_options(min_move[0], min_move[1])
                game.set_sail(min_move[0], sail_options[len(sail_options)/2])
                pirates.remove(min_move[0])
                islands.remove(min_move[1])

            elif len(enemy_drones):
                min_move = best_move(pirates, enemy_drones)
                sail_options = game.get_sail_options(min_move[0], min_move[1])
                game.set_sail(min_move[0], sail_options[len(sail_options)/2])
                pirates.remove(min_move[0])
                enemy_drones.remove(min_move[1])

            elif len(enemy_pirates):
                min_move = best_move(pirates, enemy_pirates)
                sail_options = game.get_sail_options(min_move[0], min_move[1])
                game.set_sail(min_move[0], sail_options[len(sail_options)/2])
                pirates.remove(min_move[0])
                enemy_pirates.remove(min_move[1])

            else:
                destination = Location(23,23)
                sail_options = game.get_sail_options(pirates[0], destination)
                game.set_sail(pirates[0], sail_options[len(sail_options)/2])
                pirates.remove(pirates[0])

def handle_drones(game, game_state):
    if game_state == "PUSH":
        for drone in game.get_my_living_drones():
            sail_options = game.get_sail_options(drone, game.get_my_cities()[0])
            sail = drone_optimized_sail_options(drone, sail_options, game.get_my_cities()[0].location, game)
            game.set_sail(drone , sail)

    else:
        dest_row = 0
        dest_col = 0
        for pirate in game.get_my_living_pirates():
            dest_row += pirate.location.row
            dest_col += pirate.location.col
        destination = Location(dest_row/len(game.get_my_living_pirates()), dest_col/len(game.get_my_living_pirates()))
        game.debug(destination)

        for drone in game.get_my_living_drones():
            if drone.distance(game.get_my_cities()[0]) < drone.distance(destination):
                sail_options = game.get_sail_options(drone, game.get_my_cities()[0])
                sail = drone_optimized_sail_options(drone, sail_options, game.get_my_cities()[0].location, game)
                game.set_sail(drone , sail)
            else:
                sail_options = game.get_sail_options(drone, destination)
                sail = drone_optimized_sail_options(drone, sail_options, destination, game)
                game.set_sail(drone, sail)




def try_attack(pirate, game):
    in_range_pirates = []
    for enemy_pirate in game.get_enemy_living_pirates():
        if pirate.in_attack_range(enemy_pirate):
            in_range_pirates.append(enemy_pirate)
    if len(in_range_pirates) > 0:
        min_health = sys.maxint
        best_target = 0
        for enemy_pirate in in_range_pirates:
            if enemy_pirate.current_health < min_health:
                min_health = enemy_pirate.current_health
                best_target = enemy_pirate
        game.attack(pirate, best_target)
        return True
            
    for enemy_drone in game.get_enemy_living_drones():
        if pirate.in_attack_range(enemy_drone):
            game.attack(pirate, enemy_drone)
            return True
    return False


def best_move(aircrafts, locations):
    moves = []
    for aircraft in aircrafts:
        min_dist = sys.maxint
        closest_location = 0
        for location in locations:
            if aircraft.distance(location) < min_dist:
                min_dist = aircraft.distance(location)
                closest_location = location
        move = [aircraft, closest_location, min_dist]
        moves.append(move)
    min_move = [0, 0, sys.maxint]
    for move in moves:
        if move[2] < min_move[2]:
            min_move = move

    return min_move

def drone_optimized_sail_options(drone, sail_options, destination, game):
    if len(sail_options) == 1:
        return sail_options[0]

    for enemy in game.get_enemy_living_pirates():
        if drone.distance(enemy) < 7:
            if sail_options[0].distance(enemy) < sail_options[1].distance(enemy):
                return sail_options[1]
            elif sail_options[0].distance(enemy) > sail_options[1].distance(enemy):
                return sail_options[0]

    if abs(abs(sail_options[0].row - destination.row) - abs(sail_options[0].col - destination.col)) > abs(abs(sail_options[1].row - destination.row) - abs(sail_options[1].col - destination.col)):
        return sail_options[1]
    elif abs(abs(sail_options[0].row - destination.row) - abs(sail_options[0].col - destination.col)) < abs(abs(sail_options[1].row - destination.row) - abs(sail_options[1].col - destination.col)):
        return sail_options[0]
    else:
        return sail_options[random.randint(0, 1)]