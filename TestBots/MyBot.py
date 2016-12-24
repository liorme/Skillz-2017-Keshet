import sys
from Pirates import *
import random

def do_turn(game):
    global game_state
    if game.get_turn() < 15:
        game_state = "EARLY"
    elif (len(game.get_my_living_drones()) > 29 - game.get_my_score() or game.get_max_turns() - game.get_turn() < 50) or (game_state == "RUSH" and len(game.get_my_living_drones()) > 5 or game.get_max_turns() - game.get_turn() < 50):
        game_state = "RUSH"
    elif (best_move(game.get_enemy_living_pirates(), game.get_my_cities())[2] < 7) or (game_state == "STACK" and best_move(game.get_enemy_living_pirates(), game.get_my_cities())[2] < 9):
        game_state = "STACK"
    else:
        game_state = "CONTROL"
    game.debug(game_state)
    
    handle_pirates(game, game_state)
    handle_drones(game, game_state)

def handle_pirates(game, game_state):
    all_islands = game.get_all_islands()
    pirates = game.get_my_living_pirates()
    islands = game.get_not_my_islands()
    enemy_pirates = game.get_enemy_living_pirates()
    enemy_drones = game.get_enemy_living_drones()
    
    for pirate in pirates[:]:
        if try_attack(pirate, game):
            pirates.remove(pirate)
    
    
    if game_state == "EARLY":
        i = 0
        for pirate in pirates:
            if i == 0:
                sail_options = game.get_sail_options(pirate, all_islands[1+game.get_myself().id])
                game.set_sail(pirate, sail_options[len(sail_options)/2])
            else:
                sail_options = game.get_sail_options(pirate, all_islands[3])
                game.set_sail(pirate, sail_options[len(sail_options)/2])
            i += 1
    
    elif game_state == "STACK" or game_state == "CONTROL":
        i = 0
        while len(pirates) > 0:
            """
            if i == 0:
                pirates_in_zone = []
                for enemy in enemy_pirates:
                    if enemy.location.row >= 21:
                        if (game.get_myself().id == 0 and enemy.location.col <= 23) or (game.get_myself().id == 1 and enemy.location.col >= 23):
                            pirates_in_zone.append(enemy)
                if len(pirates_in_zone) > 0:
                    move = best_move(pirates, pirates_in_zone)
                    sail_options = game.get_sail_options(move[0], move[1])
                    game.set_sail(move[0], sail_options[len(sail_options)/2])
                    pirates.remove(move[0])
                    enemy_pirates.remove(move[1])
                    i += 1
            """
        
            """
            if i == 0 and len(game.get_enemy_islands()) >= 2:
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
                i += 1
            """
            
            if len(islands) > 0:
                move = best_move(pirates, islands)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options)/2])
                pirates.remove(move[0])
                islands.remove(move[1])
            
            elif len(enemy_drones) > 0:
                move = best_move(pirates, enemy_drones)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options)/2])
                pirates.remove(move[0])
                enemy_drones.remove(move[1])
                
            elif len(enemy_pirates) > 0:
                move = best_move(pirates, enemy_pirates)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options)/2])
                pirates.remove(move[0])
                enemy_pirates.remove(move[1])
                
            else:
                destination = Location(23,(12 + 22*game.get_myself().id))
                sail_options = game.get_sail_options(pirates[0], destination)
                game.set_sail(pirates[0], sail_options[len(sail_options)/2])
                pirates.remove(pirates[0])
                
                
    elif game_state == "RUSH":
        
        move = best_move(enemy_pirates, game.get_my_cities())
        for pirate in pirates:
            sail_options = game.get_sail_options(pirate, move[0])
            game.set_sail(pirate, sail_options[len(sail_options)/2])
                
    
def handle_drones(game, game_state):
    if game_state == "STACK":
        dest_row = 0
        dest_col = 0
        for pirate in game.get_my_living_pirates():
            dest_row += pirate.location.row
            dest_col += pirate.location.col
        dest_row = dest_row / len(game.get_my_living_pirates())
        dest_col = dest_col / len(game.get_my_living_pirates())
        destination = Location(dest_row, dest_col)
        d_list = []
        d_list.append(destination)
        drone_move = best_move(game.get_enemy_living_pirates(), d_list)
        if drone_move[2] < 7:
            if destination.row + 6 <= 46:
                destination.row = destination.row + 6
            if destination.col - (1-game.get_myself().id*2)*6 >=0 and destination.col - (1-game.get_myself().id*2)*6 <= 46:
                destination.col = destination.col - (1-game.get_myself().id*2)*6
        
        for drone in game.get_my_living_drones():
            if drone.distance(game.get_my_cities()[0])*2 < drone.distance(destination):
                sail_options = game.get_sail_options(drone, game.get_my_cities()[0])
                sail = optimize_drone_moves(drone, sail_options, game.get_my_cities()[0].location, game)
                game.set_sail(drone, sail)
            else:
                sail_options = game.get_sail_options(drone, destination)
                sail = optimize_drone_moves(drone, sail_options, destination, game)
                game.set_sail(drone, sail)
        
    elif game_state == "RUSH" or game_state == "CONTROL":
        for drone in game.get_my_living_drones():
            destination = game.get_my_cities()[0]
            sail_options = game.get_sail_options(drone, destination)
            sail = optimize_drone_moves(drone, sail_options, destination.location, game)
            game.set_sail(drone, sail)

    
def try_attack(pirate, game):
    in_range_pirates = []
    for enemy_pirate in game.get_enemy_living_pirates():
        if pirate.distance(enemy_pirate) <= 3:
            in_range_pirates.append(enemy_pirate)
    #game.debug(in_range_pirates)
    if len(in_range_pirates) > 0:
        min_health = sys.maxint
        best_target = 0
        for enemy_pirate in in_range_pirates:
            if enemy_pirate.current_health < min_health:
                min_health = enemy_pirate.current_health
                best_target = enemy_pirate
        game.attack(pirate, best_target)
        game.debug(best_target)
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
    
    
def optimize_drone_moves(drone, sail_options, destination, game):
    if len(sail_options) == 1:
        return sail_options[0]

    d_list = []
    d_list.append(drone)
    closest_enemy = best_move(game.get_enemy_living_pirates(), d_list)
    if closest_enemy[2] < 7:
        if sail_options[0].distance(closest_enemy[0]) < sail_options[1].distance(closest_enemy[0]):
            return sail_options[1]
        elif sail_options[0].distance(closest_enemy[0]) > sail_options[1].distance(closest_enemy[0]):
            return sail_options[0]
    
    if abs(abs(destination.row - sail_options[0].row) - abs(destination.col - sail_options[0].col)) < abs(abs(destination.row - sail_options[1].row) - abs(destination.col - sail_options[1].col)):
        return sail_options[0]
    elif abs(abs(destination.row - sail_options[0].row) - abs(destination.col - sail_options[0].col)) > abs(abs(destination.row - sail_options[1].row) - abs(destination.col - sail_options[1].col)):
        return sail_options[1]
    else:
        return sail_options[random.randint(0, 1)]
    