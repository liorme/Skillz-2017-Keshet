import sys
from Pirates import *
import random
import math

"""
REMEMBER: Change back one STACK to CONTROL
"""


class Battle:
    def __init__(self, my_pirates, enemy_pirates, location_pirate):
        self._my_pirates = my_pirates
        self._enemy_pirates = enemy_pirates
        self._location_pirate = location_pirate
        self._turns_remaining = 0
        self._win = False

    def get_my_pirates(self):
        return self._my_pirates

    def get_enemy_pirates(self):
        return self._enemy_pirates

    def get_location_pirate(self):
        return self._location_pirate

    def update(self, my_pirates, enemy_pirates, location_pirate):
        self._my_pirates = my_pirates
        self._enemy_pirates = enemy_pirates
        self._location_pirate = location_pirate


battles = []
ave_destination = Location(0, 23)
enemy_drones_board = {}
empty_tiles = {}
for row in xrange(1, 47):
    for col in xrange(1, 47):
        enemy_drones_board[row,col] = 0
        empty_tiles[row,col] = True

def do_turn(game):
    global battles
    global game_state
    global ave_destination
    global enemy_drones_board
    global empty_tiles

    #updating the memory board
    for tile in empty_tiles:
        enemy_drones_board[tile] *= 0.99
    enemy_drones = game.get_enemy_living_drones()
    for drone in enemy_drones:
        enemy_drones_board[drone.location.row,drone.location.col] += 1
        tile = (drone.location.row,drone.location.col)
        if empty_tiles[tile]:
            empty_tiles[tile] = False

    #chosing the game state
    if game.get_turn() < 17:
        game_state = "EARLY"
    elif (len(
            game.get_my_living_drones()) > 29 - game.get_my_score() or game.get_max_turns() - game.get_turn() < 50) or (
                game_state == "RUSH" and len(
                game.get_my_living_drones()) > 5 or game.get_max_turns() - game.get_turn() < 50):
        game_state = "RUSH"
    elif (best_move(game.get_enemy_living_pirates(), game.get_my_cities())[2] < 7) or (
            game_state == "STACK" and best_move(game.get_enemy_living_pirates(), game.get_my_cities())[2] < 9):
        game_state = "STACK"
    else:
        game_state = "STACK"
    game.debug(game_state)

    update_battles(game)
    handle_pirates(game, game_state, battles)
    handle_drones(game, game_state)

    for battle in battles:
        game.debug("~~~~~~~~~~~~~")
        game.debug(battle._my_pirates)
        game.debug(battle._enemy_pirates)
        game.debug(battle._location_pirate)
        game.debug("Win: " + str(battle._win))
        game.debug("Turns remaining: " + str(battle._turns_remaining))
    game.debug("Time remaining for turn: " + str(game.get_time_remaining()) + "ms")


def handle_pirates(game, game_state, battles):
    # Get information
    all_islands = game.get_all_islands()
    my_islands = game.get_my_islands()
    pirates = game.get_my_living_pirates()
    islands = game.get_not_my_islands()
    enemy_pirates = game.get_enemy_living_pirates()
    enemy_drones = game.get_enemy_living_drones()
    enemy_health = {}

    # Get a list of enemy pirates health for try_attack
    for enemy in enemy_pirates:
        enemy_health[enemy] = enemy.current_health

    # Try attacking, and updating battles
    for pirate in pirates[:]:
        attack = try_attack(pirate, enemy_health, enemy_drones, game)
        if len(attack) > 1: 
            if not attack[2]:
                pirates.remove(attack[0])
                enemy_drones.remove(attack[1])
            elif attack[2]:
                if is_new_battle(attack):
                    create_new_battle(attack, game)
                pirates.remove(attack[0])

    # Try helping battles
    for battle in battles:
        for pirate in pirates:
            if math.ceil((pirate.distance(
                    battle._location_pirate) - 2) / 2.0) <= battle._turns_remaining and battle._win == False:
                game.debug("Pirate: " + str(pirate.id) + " is helping with a battle!")
                sail_options = game.get_sail_options(pirate, battle._location_pirate)
                game.set_sail(pirate, sail_options[len(sail_options) / 2])
                pirates.remove(pirate)

    # If early in the game rush bottom middle island with 4 pirates and upper right/left island with 1 pirate
    if game_state == "EARLY":
        i = 0
        for pirate in pirates:
            if i == 0:
                sail_options = game.get_sail_options(pirate, all_islands[1 + game.get_myself().id])
                game.set_sail(pirate, sail_options[len(sail_options) / 2])
            else:
                sail_options = game.get_sail_options(pirate, all_islands[3])
                game.set_sail(pirate, sail_options[len(sail_options) / 2])
            i += 1

    # Try to get islands, kill drones, kill pirates, and gain map control in general
    elif game_state == "STACK" or game_state == "CONTROL":
        protect_drones = 0
        defend_islands = 0
        check_battles = 0
        k = 0
        attack_pirates_relative_to_islands = 0
        while len(pirates) > 0:

            # If you can make it in time go help with a lost/tied battle
            """
            if check_battles == 0:
                for battle in battles:
                    for pirate in pirates:
                        if math.ceil((pirate.distance(battle._location_pirate)-2)/2.0) <= battle._turns_remaining:
                            game.debug("Pirate: " + str(pirate.id) + " is helping with a battle!")
                            sail_options = game.get_sail_options(pirate, battle._location_pirate)
                            game.set_sail(pirate, sail_options[len(sail_options)/2])
                            pirates.remove(pirate)
                check_battles += 1
            """

            # Defend the point where the drones stack if an enemy is near it
            if protect_drones == 0:
                for enemy in enemy_pirates:
                    if enemy.distance(ave_destination) < 10:
                        move = best_move(pirates, [enemy])
                        sail_options = game.get_sail_options(move[0], move[1])
                        game.set_sail(move[0], sail_options[len(sail_options) / 2])
                        pirates.remove(move[0])
                protect_drones += 1

            # Defend an island if an enemy is close and you can intercept him
            elif defend_islands == 0 and len(my_islands) > 0:
                best_blocking_pirate_move = [None, None, sys.maxint, None]
                for enemy_pirate in enemy_pirates:
                    enemy_bm = best_move([enemy_pirate], my_islands)
                    enemy_next_turn = game.get_sail_options(enemy_pirate, enemy_bm[1])[0]
                    if enemy_bm[2] < 10:
                        min_dist = sys.maxint
                        blocking_pirate = None
                        # find closest pirate
                        for pirate in pirates:
                            if pirate.distance(enemy_bm[1]) < enemy_bm[2] and pirate.distance(enemy_pirate) < min_dist:
                                # will die while trying to kill enemy pirate
                                if enemy_health[enemy_pirate] > pirate.current_health:
                                    continue
                                min_dist = pirate.distance(enemy_pirate)
                                blocking_pirate = pirate
                        if blocking_pirate != None:
                            if blocking_pirate.distance(enemy_pirate) < best_blocking_pirate_move[2]:
                                best_blocking_pirate_move = [blocking_pirate, enemy_pirate,
                                                             blocking_pirate.distance(enemy_pirate),
                                                             enemy_bm[1]]

                if best_blocking_pirate_move[0] != None:
                    sail_options = game.get_sail_options(best_blocking_pirate_move[0], best_blocking_pirate_move[1])
                    game.set_sail(best_blocking_pirate_move[0], sail_options[(len(sail_options) / 2)])
                    pirates.remove(best_blocking_pirate_move[0])
                    game.debug("ISLAND DEFENDED:")
                    game.debug("My Pirate "+str(best_blocking_pirate_move[0]))
                    game.debug("Enemy pirate: "+str(best_blocking_pirate_move[1]))
                    game.debug("Island defended: "+str(best_blocking_pirate_move[3]))
                defend_islands += 1

                """
                elif j == 0 and len(game.get_enemy_islands()) > 2:
                    drone_move = best_move(enemy_drones, game.get_enemy_cities())
                    if drone_move[2] <= 10:
                        d_list = []
                        d_list.append(drone_move[0])
                        move = best_move(pirates, d_list)
                        sail_options = game.get_sail_options(move[0], move[1])
                        game.set_sail(move[0], sail_options[len(sail_options)/2])
                    else:
                        destination = Location(23, 10 + game.get_myself().id*26)
                        d_list = []
                        d_list.append(destination)
                        move = best_move(pirates, d_list)
                        sail_options = game.get_sail_options(move[0], destination)
                        game.set_sail(move[0], sail_options[len(sail_options)/2])
                    pirates.remove(move[0])
                    j += 1
                """

            # Chooses the pirate that is closest to an island and sends him towards the island
            elif len(islands) > 0:
                move = best_move(pirates, islands)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options) / 2])
                pirates.remove(move[0])
                islands.remove(move[1])

            # Chooses the pirate that is closest to an enemy drone and sends him towards that drone
            elif len(enemy_drones) > 0:
                move = best_move(pirates, enemy_drones)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options) / 2])
                pirates.remove(move[0])
                enemy_drones.remove(move[1])

            # Sends pirates after enemy pirates
            elif len(enemy_pirates) > 0:
                # If controlling islands then send the pirate that is closest to one of
                # the islands towards an enemy pirate that is also closest to the island
                # Only calculates once and passes over all pirates
                if len(my_islands) > 0 and attack_pirates_relative_to_islands == 0:
                    for pirate in pirates:
                        closest_island = best_move([pirate], my_islands)
                        closest_enemy = best_move(game.get_enemy_living_pirates(), [closest_island[1]])
                        if pirate.distance(closest_enemy[0]) < 10:
                            sail_options = game.get_sail_options(pirate, closest_enemy[0])
                            game.set_sail(pirate, sail_options[len(sail_options) / 2])
                            pirates.remove(pirate)
                            # my_islands.remove(closest_island[1])
                    attack_pirates_relative_to_islands += 1
                # If not controlling islands then choose the pirate and enemy pirate with the least distance between them
                # and send him there, calculates for one pirate each pass
                else:
                    move = best_move(pirates, enemy_pirates)
                    sail_options = game.get_sail_options(move[0], move[1])
                    game.set_sail(move[0], sail_options[len(sail_options) / 2])
                    pirates.remove(move[0])
                    enemy_pirates.remove(move[1])

                """
                move = best_move(pirates, enemy_pirates)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options)/2])
                pirates.remove(move[0])
                enemy_pirates.remove(move[1])
                """

            # If all else fails, go to the middle of the map so you dont crash
            else:
                destination = Location(23, 23)
                sail_options = game.get_sail_options(pirates[0], destination)
                game.set_sail(pirates[0], sail_options[len(sail_options) / 2])
                pirates.remove(pirates[0])

    # Rushing with the stack and pirates towards the enemies that are closest to the city
    elif game_state == "RUSH":

        move = best_move(enemy_pirates, game.get_my_cities())
        for pirate in pirates:
            sail_options = game.get_sail_options(pirate, move[0])
            game.set_sail(pirate, sail_options[len(sail_options) / 2])


def handle_drones(game, game_state):
    # Find the average position of my pirates and the left/right wall,
    # and send the drones there. If enemy pirate is close to point then move point closer to spawn point
    if game_state == "STACK":
        dest_row = 0
        dest_col = 0
        for pirate in game.get_my_living_pirates():
            dest_row += pirate.location.row
            dest_col += pirate.location.col
        dest_row = dest_row / len(game.get_my_living_pirates())
        dest_col = dest_col / len(game.get_my_living_pirates())
        ave_destination = Location(dest_row, dest_col)
        drone_move = best_move(game.get_enemy_living_pirates(), [ave_destination])
        if drone_move[2] < 7:
            if ave_destination.row + 6 <= 46:
                ave_destination.row = ave_destination.row + 6
            else:
                ave_destination.row = 46
            if ave_destination.col - (1 - game.get_myself().id * 2) * 6 >= 0 and ave_destination.col - (
                1 - game.get_myself().id * 2) * 6 <= 46:
                ave_destination.col = ave_destination.col - (1 - game.get_myself().id * 2) * 6
            elif game.get_myself().id == 0:
                ave_destination.col = 0
            else:
                ave_destination.col = 46
        game.debug(ave_destination)

        # For each drone if the distance to the city is way smaller then the distance to stack point then go to city
        for drone in game.get_my_living_drones():
            if drone.distance(game.get_my_cities()[0]) * 2 < drone.distance(ave_destination):
                sail_options = game.get_sail_options(drone, game.get_my_cities()[0])
                sail = optimize_drone_moves(drone, sail_options, game.get_my_cities()[0].location, game)
                game.set_sail(drone, sail)
            else:
                sail_options = game.get_sail_options(drone, ave_destination)
                sail = optimize_drone_moves(drone, sail_options, ave_destination, game)
                game.set_sail(drone, sail)

    # Just go towards my city
    elif game_state == "RUSH" or game_state == "CONTROL":
        for drone in game.get_my_living_drones():
            destination = game.get_my_cities()[0]
            sail_options = game.get_sail_options(drone, destination)
            sail = optimize_drone_moves(drone, sail_options, destination.location, game)
            game.set_sail(drone, sail)


def try_attack(pirate, enemy_health, enemy_drones, game):
    # Find which pirates are in my range
    in_range_pirates = []
    for enemy_pirate in game.get_enemy_living_pirates():
        if pirate.in_attack_range(enemy_pirate) and enemy_health[enemy_pirate] > 0:
            in_range_pirates.append(enemy_pirate)
    # If pirates are in range then attack the one with the lowest health
    if len(in_range_pirates) > 0:
        min_health = sys.maxint
        best_target = 0
        for enemy_pirate in in_range_pirates:
            if enemy_pirate.current_health < min_health:
                min_health = enemy_pirate.current_health
                best_target = enemy_pirate
        enemy_health[best_target] -= 1
        game.attack(pirate, best_target)
        return [pirate, best_target, True]

    for enemy_drone in enemy_drones:
        if pirate.in_attack_range(enemy_drone):
            game.attack(pirate, enemy_drone)
            return [pirate, enemy_drone, False]
    return []


def best_move(aircrafts, locations):
    moves = []
    for aircraft in aircrafts[:]:
        min_dist = sys.maxint
        closest_location = 0
        for location in locations[:]:
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


def optimize_drone_moves(drone, sail_options, destination, game):
    if len(sail_options) == 1:
        return sail_options[0]

    for enemy in game.get_enemy_living_pirates():
        if drone.distance(enemy) < 7:
            if sail_options[0].distance(enemy) < sail_options[1].distance(enemy):
                return sail_options[1]
            elif sail_options[0].distance(enemy) > sail_options[1].distance(enemy):
                return sail_options[0]

    if abs(abs(sail_options[0].row - destination.row) - abs(sail_options[0].col - destination.col)) > abs(
                    abs(sail_options[1].row - destination.row) - abs(sail_options[1].col - destination.col)):
        return sail_options[1]
    elif abs(abs(sail_options[0].row - destination.row) - abs(sail_options[0].col - destination.col)) < abs(
                    abs(sail_options[1].row - destination.row) - abs(sail_options[1].col - destination.col)):
        return sail_options[0]
    else:
        return sail_options[random.randint(0, 1)]


def is_new_battle(attack):
    for battle in battles:
        if battle._location_pirate.location == attack[1].location:
            return False
    return True


def create_new_battle(attack, game):
    battle = Battle([], [], attack[1])
    all_pirates = game.get_my_living_pirates() + game.get_enemy_living_pirates()
    for pirate in all_pirates:
        if attack[1].in_attack_range(pirate):
            if pirate.owner.id == game.get_myself().id:
                battle._my_pirates.append(pirate)
            else:
                battle._enemy_pirates.append(pirate)
    battle = turns_remaining_to_battle(battle)
    battles.append(battle)


def update_battles(game):
    all_pirates = game.get_my_living_pirates() + game.get_enemy_living_pirates()
    for battle in battles:
        # update_location_pirate(battle, all_pirates, game)
        if battle.get_location_pirate() in all_pirates:
            battle._my_pirates = []
            battle._enemy_pirates = []
            for pirate in all_pirates:
                if battle.get_location_pirate().in_attack_range(pirate):
                    if pirate.owner.id == game.get_myself().id:
                        battle._my_pirates.append(pirate)
                    else:
                        battle._enemy_pirates.append(pirate)
            if not (len(battle.get_my_pirates()) > 0 and len(battle.get_enemy_pirates()) > 0):
                battles.remove(battle)
            else:
                turns_remaining_to_battle(battle)
        else:
            battles.remove(battle)


def turns_remaining_to_battle(battle):
    # for battle in battles:
    enemy_hp = 0
    my_hp = 0
    turns_remaning = 0
    for enemy in battle.get_enemy_pirates():
        enemy_hp += enemy.current_health
    for friendly in battle.get_my_pirates():
        my_hp += friendly.current_health
    my_turns_remaining = math.ceil(my_hp / float(len(battle.get_enemy_pirates())))
    enemy_turns_remaining = math.ceil(enemy_hp / float(len(battle.get_my_pirates())))
    if my_turns_remaining < enemy_turns_remaining:
        battle._win = False
        battle._turns_remaining = my_turns_remaining
    elif my_turns_remaining > enemy_turns_remaining:
        battle._win = True
        battle._turns_remaining = enemy_turns_remaining
    else:
        battle._win = False
        battle._turns_remaining = my_turns_remaining
    return battle


def optimize_pirate_moves(game, pirate, enemy_drones_board, destination):
    sail_options = game.get_sail_options(pirate, destination)
    max_value = -1
    best_option = None
    for option in sail_options:
        option_value = 0
        for row in xrange(min(option.row, destination.row), max(option.row, destination.row) + 1):
            for col in xrange(min(option.col, destination.col), max(option.col, destination.col) + 1):
                option_value += enemy_drones_board[row,col]
        option_value -= math.hypot(option.row-23,option.col-23)
        if option_value > max_value:
            max_value = option_value
            best_option = option
    return best_option
