import sys
from Pirates import *
import random
"""
REMEMBER: Change back one STACK to CONTROL
"""
class Battle:
    def __init__(self, pirates, enemy_pirates, location):
        self._pirates = pirates
        self._enemy_pirates = enemy_pirates
        self._location = location

    def get_pirates(self):
        return self._pirates
    def get_enemy_pirates(self):
        return self._enemy_pirates
    def get_location(self):
        return self._location

    def update(self, pirates, enemy_pirates, location):
        self._pirates = pirates
        self._enemy_pirates = enemy_pirates
        self._location = location


battles = []
ave_destination = Location(0,23)
def do_turn(game):
    global battles
    global game_state
    global ave_destination
    if game.get_turn() < 17:
        game_state = "EARLY"
    elif (len(game.get_my_living_drones()) > 29 - game.get_my_score() or game.get_max_turns() - game.get_turn() < 50) or (game_state == "RUSH" and len(game.get_my_living_drones()) > 5 or game.get_max_turns() - game.get_turn() < 50):
        game_state = "RUSH"
    elif (best_move(game.get_enemy_living_pirates(), game.get_my_cities())[2] < 7) or (game_state == "STACK" and best_move(game.get_enemy_living_pirates(), game.get_my_cities())[2] < 9):
        game_state = "STACK"
    else:
        game_state = "STACK"
    game.debug(game_state)
    
    update_battles()
    handle_pirates(game, game_state)
    handle_drones(game, game_state)

    game.debug(game.get_time_remaining())


def handle_pirates(game, game_state):
    #Get information
    all_islands = game.get_all_islands()
    my_islands = game.get_my_islands()
    pirates = game.get_my_living_pirates()
    islands = game.get_not_my_islands()
    enemy_pirates = game.get_enemy_living_pirates()
    enemy_drones = game.get_enemy_living_drones()
    enemy_health = {}

    #Get a list of enemy pirates health for try_attack
    for enemy in enemy_pirates:
        enemy_health[enemy] = enemy.current_health


    #Try attacking, and updating battles
    for pirate in pirates[:]:
        attack = try_attack(pirate, enemy_health, game)
        if attack == True:
            pirates.remove(pirate)
        elif False:
            if new_battle(attack):
                pass
            else:
                add_to_battle(attack)

    
    #If early in the game rush bottom middle island with 4 pirates and upper right/left island with 1 pirate
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
    
    #Try to get islands, kill drones, kill pirates, and gain map control in general
    elif game_state == "STACK" or game_state == "CONTROL":
        i = 0
        j = 0
        k = 0
        l = 0
        while len(pirates) > 0:

            #Defend the point where the drones stack if an enemy is near it
            if i == 0:
                for enemy in enemy_pirates:
                    if enemy.distance(ave_destination) < 10:
                        move = best_move(pirates, [enemy])
                        sail_options = game.get_sail_options(move[0], move[1])
                        game.set_sail(move[0], sail_options[len(sail_options)/2])
                        pirates.remove(move[0])
                i += 1

            #Defend an island if an enemy is close and you can intercept him
            elif j == 0 and len(my_islands) > 0:
                best_blocking_pirate_move = [None, None, sys.maxint]
                for enemy_pirate in enemy_pirates:
                        enemy_bm = best_move([enemy_pirate], my_islands)
                        if enemy_bm[2] < 10:
                            min_dist = sys.maxint
                            blocking_pirate = None
                            for pirate in pirates:
                                if pirate.distance(enemy_bm[1]) < enemy_bm[2] and pirate.distance(enemy_pirate) < min_dist:
                                        min_dist = pirate.distance(enemy_pirate)
                                        blocking_pirate = pirate
                            if blocking_pirate != None:
                                if blocking_pirate.distance(enemy_pirate) < best_blocking_pirate_move[2]:
                                    best_blocking_pirate_move = [blocking_pirate, enemy_pirate, blocking_pirate.distance(enemy_pirate)]

                if best_blocking_pirate_move[0] != None:  
                    sail_options = game.get_sail_options(best_blocking_pirate_move[0], best_blocking_pirate_move[1])
                    game.set_sail(best_blocking_pirate_move[0], sail_options[(len(sail_options) / 2)])
                    pirates.remove(best_blocking_pirate_move[0])
                j += 1
                
            
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

            #Chooses the pirate that is closest to an island and sends him towards the island
            elif len(islands) > 0:
                move = best_move(pirates, islands)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options)/2])
                pirates.remove(move[0])
                islands.remove(move[1])

            #Chooses the pirate that is closest to an enemy drone and sends him towards that drone
            elif len(enemy_drones) > 0:
                move = best_move(pirates, enemy_drones)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options)/2])
                pirates.remove(move[0])
                enemy_drones.remove(move[1])
            
            #Sends pirates after enemy pirates
            elif len(enemy_pirates) > 0 or l == -1:
                #If controlling islands then send the pirate that is closest to one of
                #the islands towards an enemy pirate that is also closest to the island
                #Only calculates once and passes over all pirates
                if len(my_islands) > 0:
                    for pirate in pirates:
                        closest_island = best_move([pirate], my_islands)
                        closest_enemy = best_move(game.get_enemy_living_pirates(), [closest_island[1]])
                        if pirate.distance(closest_enemy[0]) < 10 or True:
                            sail_options = game.get_sail_options(pirate, closest_enemy[0])
                            game.set_sail(pirate, sail_options[len(sail_options)/2])
                            pirates.remove(pirate)
                            #my_islands.remove(closest_island[1])
                    l += 1
                #If not controlling islands then choose the pirate and enemy pirate with the least distance between them
                #and send him there, calculates for one pirate each pass
                else:
                    move = best_move(pirates, enemy_pirates)
                    sail_options = game.get_sail_options(move[0], move[1])
                    game.set_sail(move[0], sail_options[len(sail_options)/2])
                    pirates.remove(move[0])
                    enemy_pirates.remove(move[1])                 


                """
                move = best_move(pirates, enemy_pirates)
                sail_options = game.get_sail_options(move[0], move[1])
                game.set_sail(move[0], sail_options[len(sail_options)/2])
                pirates.remove(move[0])
                enemy_pirates.remove(move[1])
                """
                
            #If all else fails, go to the middle of the map so you dont crash
            else:
                destination = Location(23,23)
                sail_options = game.get_sail_options(pirates[0], destination)
                game.set_sail(pirates[0], sail_options[len(sail_options)/2])
                pirates.remove(pirates[0])
                
    #Rushing with the stack and pirates towards the enemies that are closest to the city           
    elif game_state == "RUSH":

        move = best_move(enemy_pirates, game.get_my_cities())
        for pirate in pirates:
            sail_options = game.get_sail_options(pirate, move[0])
            game.set_sail(pirate, sail_options[len(sail_options)/2])
                
    
def handle_drones(game, game_state):
    #Find the average position of my pirates and the left/right wall,
    #and send the drones there. If enemy pirate is close to point then move point closer to spawn point
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
            if ave_destination.col - (1-game.get_myself().id*2)*6 >=0 and ave_destination.col - (1-game.get_myself().id*2)*6 <= 46:
                ave_destination.col = ave_destination.col - (1-game.get_myself().id*2)*6
            elif game.get_myself().id == 0:
                ave_destination.col = 0
            else:
                ave_destination.col = 46
        game.debug(ave_destination)

        #For each drone if the distance to the city is way smaller then the distance to stack point then go to city
        for drone in game.get_my_living_drones():
            if drone.distance(game.get_my_cities()[0])*2 < drone.distance(ave_destination):
                sail_options = game.get_sail_options(drone, game.get_my_cities()[0])
                sail = optimize_drone_moves(drone, sail_options, game.get_my_cities()[0].location, game)
                game.set_sail(drone, sail)
            else:
                sail_options = game.get_sail_options(drone, ave_destination)
                sail = optimize_drone_moves(drone, sail_options, ave_destination, game)
                game.set_sail(drone, sail)
        
    #Just go towards my city
    elif game_state == "RUSH" or game_state == "CONTROL":
        for drone in game.get_my_living_drones():
            destination = game.get_my_cities()[0]
            sail_options = game.get_sail_options(drone, destination)
            sail = optimize_drone_moves(drone, sail_options, destination.location, game)
            game.set_sail(drone, sail)


def try_attack(pirate, enemy_health, game):
    #Find which pirates are in my range
    in_range_pirates = []
    for enemy_pirate in game.get_enemy_living_pirates():
        if pirate.in_attack_range(enemy_pirate) and enemy_health[enemy_pirate] > 0:
            in_range_pirates.append(enemy_pirate)
    #If pirates are in range then attack the one with the lowest health
    if len(in_range_pirates) > 0:
        min_health = sys.maxint
        best_target = 0
        for enemy_pirate in in_range_pirates:
            if enemy_pirate.current_health < min_health:
                min_health = enemy_pirate.current_health
                best_target = enemy_pirate
        enemy_health[best_target] -= 1
        game.attack(pirate, best_target)
        return True
            
    for enemy_drone in game.get_enemy_living_drones():
        if pirate.in_attack_range(enemy_drone):
            game.attack(pirate, enemy_drone)
            return True
    return False


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

    if abs(abs(sail_options[0].row - destination.row) - abs(sail_options[0].col - destination.col)) > abs(abs(sail_options[1].row - destination.row) - abs(sail_options[1].col - destination.col)):
        return sail_options[1]
    elif abs(abs(sail_options[0].row - destination.row) - abs(sail_options[0].col - destination.col)) < abs(abs(sail_options[1].row - destination.row) - abs(sail_options[1].col - destination.col)):
        return sail_options[0]
    else:
        return sail_options[random.randint(0, 1)]


def is_new_battle(attack):
    for battle in battles:
        if battle.location == attack[1].location:
            return False
        else:
            new_battle = create_new_battle(attack)
            battles.append(new_battle)
            return True

def create_new_battle():
    pass
def update_battles():
    pass
def add_to_battle():
    pass