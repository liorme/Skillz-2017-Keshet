from Pirates import *
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


class BestMove:
    def __init__(self, aircraft, closest_location, min_dist):
        self._aircraft = aircraft
        self._loc = closest_location
        self._dist = min_dist

    def get_aircraft(self):
        return self._aircraft

    def get_location(self):
        return self._loc

    def get_dist(self):
        return self._dist


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


# Global Variables:

range3 = [(3, 0), (2, -1), (2, 0), (2, 1), (1, -2), (1, -1), (1, 0), (1, 1), (1, 2), (0, -3), (0, -2), (0, -1), (0, 0),
          (0, 1), (0, 2), (0, 3), (-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2), (-2, -1), (-2, 0), (-2, 1), (-3, 0)]
battles = []
ave_destination = Location(0, 23)
enemy_drones_board = {}  # dictionary of all places in the board through which an enemy drone has passed.
danger_board = {}  # places in which no drone has passed aren't in the dictionary
full_tiles = []  # list of keys of enemy_drones_board
rows = 1
cols = 1
set = False
game_state = ""
drones_plans = []
stacking = 0

# Constants:
ENEMY_DRONE_REMEMBER_FACTOR = 0.99
ENEMY_PIRATE_REMEMBER_FACTOR = 0.9
MAX_TIME_TO_RUSH = 50
MIN_DRONES_ALIVE_AND_POINTS_TO_RUSH = 29
MIN_DRONES_ALIVE_TO_CONTINUE_RUSH = 10
MIN_PIRATE_CITY_DIST_TO_STACK = 7
MIN_PIRATE_CITY_DIST_TO_CONT_STACK = 9
EARLY_TURNS = 17
PIRATE = 0
DRONE = 1
NO_ATTACK = -1
DANGER_COST = 5
DRONES_TO_AGGESSION = 10
RUSH_RADIUS = 8


def do_turn(game):
    
    global battles, enemy_drones_board, full_tiles, danger_board
    global game_state, ave_destination
    global rows, cols
    global set
    global range3
    global stacking
    
    city = game.get_my_cities()[0]
    drones_in_range = []
    drones = game.get_my_living_drones()
    for drone in drones:
        if drone.distance(city) < 11:
            drones_in_range.append(drone)
    # initialize variables for the first run:

    if not set:
        rows = game.get_row_count()
        cols = game.get_col_count()
        for row in range(rows):
            for col in range(cols):
                enemy_drones_board[(row, col)] = 0
                danger_board[(row, col)] = 0
        set = True

    # update the memory board:
    for tile in full_tiles:  # decrease effect of drone pass over time.
        enemy_drones_board[tile] *= ENEMY_DRONE_REMEMBER_FACTOR
    for tile in danger_board:  # decrease effect of pirates over time but slower.
        danger_board[tile] *= ENEMY_PIRATE_REMEMBER_FACTOR

    # add current drone states to enemy_drones_board:
    enemy_drones = game.get_enemy_living_drones()
    for drone in enemy_drones:
        tile = (drone.location.row, drone.location.col)
        enemy_drones_board[tile] += 1
        if tile not in full_tiles:
            full_tiles.append(tile)

    #add current danger tiles to danger_board:
    danger_pirates = game.get_enemy_living_pirates()
    for pirate in danger_pirates:
        row = pirate.location.row
        col = pirate.location.col
        for directions in range3:
            dirow = row+directions[0]
            dicol = col+directions[1]
            if dirow <= 45 and dirow >= 0 and dicol >= 0 and dicol <= 46:
                danger_board[(dirow,dicol)] += 1

    # choose the game state:
    if game.get_turn() < EARLY_TURNS:
        game_state = "EARLY"
    elif (len(
            game.get_my_living_drones()) > MIN_DRONES_ALIVE_AND_POINTS_TO_RUSH - game.get_my_score()
          or game.get_max_turns() - game.get_turn() < MAX_TIME_TO_RUSH) or (
                        game_state == "RUSH" and len(
                    drones_in_range) > MIN_DRONES_ALIVE_TO_CONTINUE_RUSH or game.get_max_turns() - game.get_turn() < MAX_TIME_TO_RUSH):
        game_state = "CONTROL"
    elif False and (best_move(game.get_enemy_living_pirates(),
                    game.get_my_cities()).get_dist() < MIN_PIRATE_CITY_DIST_TO_STACK) or (
                    game_state == "STACK" and best_move(game.get_enemy_living_pirates(),
                                                        game.get_my_cities()).get_dist() < MIN_PIRATE_CITY_DIST_TO_CONT_STACK):
        stacking += 1
        if stacking >= 15:
            game_state = "STACK"
        else:
            game_state = "CONTROL"
    elif game.get_enemy_islands() > game.get_my_islands() and len(game.get_enemy_living_drones()) > DRONES_TO_AGGESSION:
        game_state = "AGGRESSIVE"
        stacking = max(0, stacking -1)
    else:
        game_state = "CONTROL"
        stacking = max(0, stacking -1)

    game.debug(game_state)

    update_battles(game)
    handle_pirates(game, game_state, battles)
    handle_drones(game, game_state)

    """
    for battle in battles:
        game.debug("~~~~~~~~~~~~~")
        game.debug(battle._my_pirates)
        game.debug(battle._enemy_pirates)
        game.debug(battle._location_pirate)
        game.debug("Win: " + str(battle._win))
        game.debug("Turns remaining: " + str(battle._turns_remaining))
    """
    game.debug("Time remaining for turn: " + str(game.get_time_remaining()) + "ms")



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

    # Get a list of enemy pirates health for try_attack
    for enemy in enemy_pirates:
        enemy_health[enemy] = enemy.current_health

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

    # Try helping battles, but ignore battles when rushing
    if game_state != "RUSH":
        for battle in battles:
            for pirate in pirates:
                if math.ceil((pirate.distance(battle._location_pirate) - 2) / 2.0) <= \
                        battle._turns_remaining - 1:
                    #game.debug("Pirate: " + str(pirate.id) + " is helping with a battle!")
                    sail_options = game.get_sail_options(pirate, battle._location_pirate)
                    if not pirate in semi_used_pirates: game.set_sail(pirate, sail_options[len(sail_options) / 2])
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
    elif game_state == "STACK" or game_state == "CONTROL" or game_state == "RUSH" or game_state == "AGGRESSIVE":
        protect_drones = 0
        defend_islands = 0
        check_battles = 0
        k = 0
        defend = 0
        max_stack = 0
        drone_stack = None
        attack_pirates_relative_to_islands = 0
        find_max_stack = 0
        low_hp_pirates = []
        low_hp_check = 0
        my_pirates_next_locations = []
        while len(pirates) > 0:
            
            game.debug(my_pirates_next_locations)
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
            enemy_next_move = None
            # Defend the point where the drones stack if an enemy is near it
            if protect_drones == 0 and game_state == "STACK":
                for enemy in enemy_pirates:
                    if len(pirates) == 0:
                        break
                    if enemy.distance(ave_destination) < 10:
                        move = best_move(pirates, [enemy])
                        sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
                        if not move.get_aircraft() in semi_used_pirates:
                            game.set_sail(move.get_aircraft(), sailing)
                            my_pirates_next_locations.append(sailing)
                        else:
                            my_pirates_next_locations.append(move.get_aircraft().location)
                        pirates.remove(move.get_aircraft())
                        defend += 1
                protect_drones += 1

            # Defend an island if an enemy is close and you can intercept him
            elif defend_islands == 0 and len(my_islands) > 0:
                best_blocking_pirate_move = [None, None, 9999999, None]
                for enemy_pirate in enemy_pirates:
                    if len(pirates) == 0:
                        break
                    enemy_bm = best_move([enemy_pirate], my_islands)
                    enemy_options = game.get_sail_options(enemy_pirate, enemy_bm.get_location())
                    enemy_next_move = enemy_options[len(enemy_options) / 2]
                    if enemy_bm.get_dist() < 10:
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
                        my_pirates_next_locations.append(sailing)
                    else:
                        my_pirates_next_locations.append(best_blocking_pirate_move[0].location)
                    pirates.remove(best_blocking_pirate_move[0])
                    game.debug("ISLAND DEFENDED:")
                    game.debug("My Pirate " + str(best_blocking_pirate_move[0]))
                    game.debug("Enemy pirate: " + str(best_blocking_pirate_move[1]))
                    game.debug("Island defended: " + str(best_blocking_pirate_move[3]))
                defend_islands += 1


            elif defend == 0 and len(enemy_drones) > 6 and game_state != "AGGRESSIVE":
                drone_move = best_move(enemy_drones, game.get_enemy_cities())
                if drone_move.get_dist() <= 11:
                    move = best_move(pirates, [drone_move.get_aircraft()])
                    sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
                    if not move.get_aircraft() in semi_used_pirates:
                        game.set_sail(move.get_aircraft(), sailing)
                        my_pirates_next_locations.append(sailing)
                    else:
                        my_pirates_next_locations.append(move.get_aircraft().location)
                    pirates.remove(move.get_aircraft())
                else:
                    destination = Location(23, 10 + game.get_myself().id*26)
                    move = best_move(pirates, [destination])
                    sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location())
                    if not move.get_aircraft() in semi_used_pirates:
                        game.set_sail(move.get_aircraft(), sailing)
                        my_pirates_next_locations.append(sailing)
                    else:
                        my_pirates_next_locations.append(move.get_aircraft().location)
                    pirates.remove(move.get_aircraft())
                defend += 1

            # Chooses the pirate that is closest to an island and sends him towards the island
            elif len(islands) > 0:
                game.debug("going for islands")
                move = best_move(pirates, islands)
                sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
                if not move.get_aircraft() in semi_used_pirates:
                    game.set_sail(move.get_aircraft(), sailing)
                    my_pirates_next_locations.append(sailing)
                else:
                    my_pirates_next_locations.append(move.get_aircraft().location)
                pirates.remove(move.get_aircraft())
                islands.remove(move.get_location())

            elif len(enemy_pirates) > 0 and False:
                if low_hp_check == 0:
                    for pirate in pirates:
                        if pirate.current_health < 3 and pirate not in semi_used_pirates:
                            low_hp_pirates.append(pirate)
                    low_hp_check += 1
                while len(low_hp_pirates) > 0:
                    move = best_move(low_hp_pirates, enemy_pirates)
                    sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
                    if not move.get_aircraft() in semi_used_pirates:
                        game.set_sail(move.get_aircraft(), sailing)
                        my_pirates_next_locations.append(sailing)
                    else:
                        my_pirates_next_locations.append(move.get_aircraft().location)
                    pirates.remove(move.get_aircraft())
                    low_hp_pirates.remove(move.get_aircraft())

            # Chooses the pirate that is closest to an enemy drone and sends him towards that "drone
            elif (len(enemy_drones) > 0 or len(enemy_pirates) > 0) and game_state != "AGGRESSIVE":
                move = best_move(pirates, enemy_drones + enemy_pirates)
                sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
                if not move.get_aircraft() in semi_used_pirates:
                    game.set_sail(move.get_aircraft(), sailing)
                    my_pirates_next_locations.append(sailing)
                else:
                    my_pirates_next_locations.append(move.get_aircraft().location)
                pirates.remove(move.get_aircraft())
                if move.get_location()  in enemy_drones: enemy_drones.remove(move.get_location())
                elif move.get_location()  in enemy_pirates: enemy_pirates.remove(move.get_location())
            
            
            elif (max_stack > 0 or find_max_stack == 0) and game_state != "AGGRESSIVE":
                if find_max_stack == 0:
                    for drone in my_drones:
                        drones_in_location = [x for x in game.get_aircrafts_on(drone.location) if x.max_speed == 1 and x.owner.id == game.get_myself().id]
                        if len(drones_in_location) > max_stack:
                            max_stack = len(drones_in_location)
                            drone_stack = [drone]
                            for d in drones_in_location:
                                my_drones.remove(d)
                        elif len(drones_in_location) == max_stack:
                            drone_stack.append(drone)
                            for d in drones_in_location:
                                my_drones.remove(d)
                    find_max_stack += 1
                move = best_move(pirates, drone_stack)
                sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location().location)
                if not move.get_aircraft() in semi_used_pirates:
                    game.set_sail(move.get_aircraft(), sailing)
                    my_pirates_next_locations.append(sailing)
                else:
                    my_pirates_next_locations.append(move.get_aircraft().location)
                pirates.remove(move.get_aircraft())
            
            
            
            #send pirates to theire frineds
            elif len(my_pirates_next_locations) > 0:
                move = best_move(pirates, my_pirates_next_locations)
                sailing = optimize_pirate_moves(game, move.get_aircraft(), move.get_location())
                if not move.get_aircraft() in semi_used_pirates:
                    game.set_sail(move.get_aircraft(), sailing)
                    my_pirates_next_locations.append(sailing)
                else:
                    my_pirates_next_locations.append(move.get_aircraft().location)
                pirates.remove(move.get_aircraft())
            # If all else fails, go to the middle of the map so you dont crash
            else:
                x=1/0
                destination = Location(23, 23)
                sailing = optimize_pirate_moves(game, pirates[0], destination)
                if not pirates[0] in semi_used_pirates: game.set_sail(pirates[0], sailing)
                pirates.remove(pirates[0])

    # Rushing with the stack and pirates towards the enemies that are closest to the city
    elif game_state == "RUSH":
        max_stack = 0
        stack_location = Location(0, 0)
        for drone in game.get_my_living_drones():
            if len(game.get_aircrafts_on(drone.location)) > max_stack:
                max_stack = len(game.get_aircrafts_on(drone.location))
                stack_location = drone.location
        stack_location = Location(stack_location.row,stack_location.col+2-4*game.get_myself().id)
        scary_terry = best_move(enemy_pirates, [stack_location])
        for pirate in pirates:
            if scary_terry.get_dist() < RUSH_RADIUS:
                sailing = optimize_pirate_moves(game, pirate, scary_terry.get_aircraft().location)
                if not pirate in semi_used_pirates: game.set_sail(pirate, sailing)
            else:
                sailing = optimize_pirate_moves(game, pirate, stack_location)
                if not pirate in semi_used_pirates: game.set_sail(pirate, sailing)


def handle_drones(game, game_state):
    global drones_plans
    global rows, cols
    drones = game.get_my_living_drones()
    living_drones_ids = [drone.id for drone in drones]
    islands_locations = [island.location for island in game.get_my_islands()]
    enemy_pirates = game.get_enemy_living_pirates()
    
    #dodging enemy pirates while there are drones in danger
    checked = False
    while game_state != "RUSH":
        while not checked:
            drone_move = best_move(drones, game.get_my_cities())
            if drone_move.get_dist() < 8:
                sail_options = game.get_sail_options(drone_move.get_aircraft(), drone_move.get_location())
                sailing = optimize_drone_moves(sail_options, game)
                game.set_sail(drone_move.get_aircraft(), sailing)
                drones.remove(drone_move.get_aircraft())
                living_drones_ids.remove(drone_move.get_aircraft().id)
            else:
                checked = True

        escaping_info = best_move(drones, enemy_pirates)
        if escaping_info.get_dist() > 6:
            break
        row = min(rows-1,max(2*escaping_info.get_aircraft().location.row - escaping_info.get_location().location.row,0))
        col = min(cols-1,max(2*escaping_info.get_aircraft().location.col - escaping_info.get_location().location.col,0))
        sail_options = game.get_sail_options(escaping_info.get_aircraft(), Location(row,col))
        sailing = optimize_drone_moves(sail_options, game)
        game.set_sail(escaping_info.get_aircraft(), sailing)
        drones.remove(escaping_info.get_aircraft())
        living_drones_ids.remove(escaping_info.get_aircraft().id)
        #game.debug("ESCAPE")
    
    if game_state == "CONTROL" or game_state == "AGGRESSIVE":
        # making new plans
        for drone in drones:
            if drone.location in islands_locations:
                new_plan = GPS(game, drone, game.get_my_cities()[0].location)
                drones_plans.append({"id":drone.id,"steps":new_plan})
            if game.get_time_remaining() < 10:
                break

        # plan isn't relevant (drone killed or moved away from path)
        for plan in drones_plans[:]:
            if plan["steps"] != [] and plan["id"] in living_drones_ids:
                drone = game.get_my_drone_by_id(plan["id"])
                if abs(drone.location.row - plan["steps"][0][0]) == 1 and abs(drone.location.col - plan["steps"][0][1]) == 0:
                    continue
                elif abs(drone.location.row - plan["steps"][0][0]) == 0 and abs(drone.location.col - plan["steps"][0][1]) == 1:
                    continue
                elif game.get_time_remaining() > -40:
                    drones_plans.remove(plan)
                    new_plan = GPS(game, drone, game.get_my_cities()[0].location)
                    drones_plans.append({"id": drone.id, "steps": new_plan})
                else:
                    drones_plans.remove(plan)



        # executing drones planes
        for plan in drones_plans:
            if plan["steps"] != [] and plan["id"] in living_drones_ids:
                drone = game.get_my_drone_by_id(plan["id"])
                next_step = Location(plan["steps"][0][0],plan["steps"][0][-1])
                if drone in drones:
                    drones.remove(drone)
                    game.set_sail(drone, next_step)
                plan["steps"] = plan["steps"][1:]
    
    # Find the average position of my pirates and the left/right wall,
    # and send the drones there. If enemy pirate is close to point then move point closer to spawn point
    if game_state == "STACK" and False:
        dest_row = 0
        dest_col = 0
        for pirate in game.get_my_living_pirates():
            dest_row += pirate.location.row
            dest_col += pirate.location.col
        dest_row = dest_row / len(game.get_my_living_pirates())
        dest_col = dest_col / len(game.get_my_living_pirates())
        if game.get_myself().id == 0:
            ave_destination = Location(dest_row, min(13, dest_col))
        else:
            ave_destination = Location(dest_row, max(33, dest_col))
        drone_move = best_move(game.get_enemy_living_pirates(), [ave_destination])
        if drone_move.get_dist() < 7:
            if ave_destination.row + 6 <= 46:
                ave_destination.row = ave_destination.row + 6
            else:
                ave_destination.row = 46
            if ave_destination.col - 1 - game.get_myself().id * 2 >= 0 \
                    and ave_destination.col - (1 - game.get_myself().id * 2) * 6 <= 46:
                ave_destination.col = ave_destination.col - (1 - game.get_myself().id * 2) * 6
            elif game.get_myself().id == 0:
                ave_destination.col = 0
            else:
                ave_destination.col = 46
        game.debug(ave_destination)

        # For each drone if the distance to the city is way smaller then the distance to stack point then go to city
        for drone in drones:
            if drone.distance(game.get_my_cities()[0]) * 2 < drone.distance(ave_destination):
                sail_options = game.get_sail_options(drone, game.get_my_cities()[0])
                sail = optimize_drone_moves(sail_options, game)
                game.set_sail(drone, sail)
            else:
                sail_options = game.get_sail_options(drone, ave_destination)
                sail = optimize_drone_moves(sail_options, game)
                game.set_sail(drone, sail)

    # Just go towards my city
    elif game_state == "RUSH" or game_state == "CONTROL" or game_state == "AGGRESSIVE":
        for drone in drones:
            destination = game.get_my_cities()[0]
            sail_options = game.get_sail_options(drone, destination)
            sail = optimize_drone_moves(sail_options, game)
            game.set_sail(drone, sail)


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


def best_move(aircrafts, locations):
    moves = []
    for aircraft in aircrafts[:]:
        min_dist = 9999999
        closest_location = 0
        for location in locations[:]:
            if aircraft.distance(location) < min_dist:
                min_dist = aircraft.distance(location)
                closest_location = location
        move = BestMove(aircraft, closest_location, min_dist)
        moves.append(move)
    min_move = BestMove(0, 0, 9999999)
    for move in moves:  # type: BestMove
        if move.get_dist() < min_move.get_dist():
            min_move = move
    return min_move


def optimize_drone_moves(sail_options, game):
    if len(sail_options) == 1:
        return sail_options[0]

    move1 = best_move([sail_options[0]], game.get_enemy_living_pirates())
    move2 = best_move([sail_options[1]], game.get_enemy_living_pirates())

    if move1.get_dist() > move2.get_dist() and move2.get_dist() < 10:
        return sail_options[0]
    elif move1.get_dist() < move2.get_dist() and move1.get_dist() < 10:
        return sail_options[1]

    if (sail_options[0].row-24)**2+(sail_options[0].col-23)**2 > (sail_options[1].row-24)**2+(sail_options[1].col-23)**2:
        return sail_options[0]
    else:
        return sail_options[1]



def is_new_battle(attack):
    for battle in battles:
        if battle._location_pirate.location == attack.get_target().location:
            return False
    return True


def create_new_battle(attack, game):
    battle = Battle([], [], attack.get_target())
    all_pirates = game.get_my_living_pirates() + game.get_enemy_living_pirates()
    for pirate in all_pirates:
        if attack.get_target().in_attack_range(pirate):
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
                if col >= 0 and col < cols and row >= 0 and row < rows:
                    option_value += enemy_drones_board[(row, col)]
        option_value -= math.hypot(option.row - 23, option.col - 23)
        if option_value > max_value:
            max_value = option_value
            best_option = option
    return best_option

#takes a drone and a destination, return the safes and shortest path
def GPS(game, drone, destination):
    #danger_board is a memory of all the places enem pirates have threatend
    global danger_board
    destination = (destination.row,destination.col)
    #creates a board by (row,col) that for each spot contains a dicrenry its 'index', the 'cost' to get there(infinty at the begining),
    #the 'value' of beein there ('cost' plus min cost to get from there to destenation) and the shortest road to this point that is corently known(empty in the begining)
    board = {}
    for row in xrange(46):
        for col in xrange(47):

            board[(row,col)] = {'index':(row,col),'cost':10**99,'value':10**99,'road':[]}
    #sets the drones location to be 'cost' 0 and 'value' 0

    board[(drone.location.row,drone.location.col)]['cost'] = 0
    board[(drone.location.row,drone.location.col)]['value'] = 0+abs(drone.location.row-destination[0])+abs(drone.location.col-destination[-1])
    #creates a list of points we know how to get to and that are not yet checked, this list will be sorted by the points values
    needs_checking = [board[(drone.location.row,drone.location.col)]]
    #next_to is a list of the 4 dirctions, in an efficnt order acourding to your team
    if game.get_myself().id == 0:
        next_to =[(0,-1),(1,0),(0,1),(-1,0)]
    else:
        next_to =[(0,1),(1,0),(0,-1),(-1,0)]
    while True:
        tile = needs_checking[0] #seting the tile with the best value to be the one we are checking
        if tile['index'] == destination: #if this tile is the destination we return the road we found to this tile
            return board[destination]['road']
        needs_checking = needs_checking[1:] #taking the tile we are checking out of needs_checking
        # we are checking all the tiles that next to the tile we are checking and adding the road and the cost for this next_to_tile if its efficnt to go therew tile
        for i in next_to:
            row = tile['index'][0]+i[0]
            col = tile['index'][-1]+i[-1]
            if row >= 0 and row <= 45 and col >= 0 and col <= 46: #checking that the next_to_tile is on the board
                potential_cost = tile['cost']+danger_board[(row,col)]*DANGER_COST+1 #potential_cost is the cost to get to tile + the danger level times DANGER_COST + the turns it will take to get to this next tile (1)
                if potential_cost < board[(row ,col)]['cost']: #checkes if the potential_cost is lower then the cost that the tile hes
                    b=0 #checkes it updates the new tile onl once
                    board[(row,col)]['cost'] = potential_cost #setting the new cost
                    board[(row,col)]['value'] = potential_cost+abs(row-destination[0])+abs(col-destination[-1]) #setting the new value
                    board[(row,col)]['road'] = tile['road']+[(row,col)] #setting the new road
                    for itsplace,unchecked in enumerate(needs_checking[:]): #looping threw the needs_checking list and the indexes of it
                        if b==0 and unchecked['value'] >= board[(row,col)]['value']: #if we looped and got to a place in list that the new tile hes less value(better):
                            needs_checking.insert(itsplace,board[(row,col)]) #we insert the the new_tile into the needs_checking list
                            b=1 #we make shor we wont add or insert it again
                        if unchecked['index'] == (row,col) and unchecked['value']!=board[(row,col)]['value']: #if the unchecked tile is a older version of the new_tile
                            needs_checking.remove(unchecked) #we remove it
                    if b==0: #if we didnt inserted the new_tile yet (it hes the worst value)
                        needs_checking.append(board[(row,col)]) #we append it ate the end of the needs_checking list
