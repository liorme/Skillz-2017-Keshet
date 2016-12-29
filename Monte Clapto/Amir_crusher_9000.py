"""
Bot using Monte-Carlo simulations
"""

# Imports
from Pirates import *
import random
import math


# Class Definitions

# Class constants

PIRATE = 0
DRONE = 1
ISLAND = 2
CITY = 3

MY_TEAM = 0
ENEMY_TEAM = 1
NEUTRAL = 2  # for islands


class Action:

    def __init__(self, type, who, where):
        self._type = type
        self._who = who
        self._where = where

    def get_who(self):
        return self._who

    def get_where(self):
        return self._where

    def get_type(self):
        return self._type


class MyAircraft:

    def __init__(self, type, location, id, team, max_health, max_move, attack_range):
        self._type = type
        self._location = clone_location(location)
        self._id = id
        self._team = team
        self._health = max_health
        self._attack_range = attack_range
        self._max_move = max_move

    def get_id(self):
        return self._id

    def get_location(self):
        """
        get my location
        :return: my location
        :rtype Location
        """
        return self._location

    def get_type(self):
        return self._type

    def get_team(self):
        return self._team

    def set_location(self, new_loc):
        self._location = clone_location(new_loc)

    def get_health(self):
        return self._health

    def decrease_health(self, n):
        self._health -= n

    def distance(self, other):
        """
        computes the distance between me and other
        :param other: aircraft to compute distance
        :type other: MyAircraft or MapLocation
        :return: the distance between me and other
        :rtype float
        """
        location1 = self.get_location()
        location2 = other.get_location()
        d_row = abs(location1.row - location2.row)
        d_col = abs(location1.col - location2.col)

        return d_row + d_col

    def get_max_speed(self):
        return self._max_move

    def get_attack_range(self):
        return self._attack_range


class MapLocation:

    def __init__(self, type, location, id, team):
        self._type = type
        self._location = location
        self._id = id
        self._team = team

    def get_id(self):
        return self._id

    def get_location(self):
        return self._location

    def get_type(self):
        return self._type

    def get_team(self):
        return self._team

    def set_team(self, new_team):
        self._team = new_team

    def distance(self, other_location):
        """
        computes the distance between me and location
        :param other_location: location to compute distance from
        :type other_location: Location
        :return: the distance between me and other
        :rtype float
        """
        my_location = self.get_location()
        d_row = abs(my_location.row - other_location.row)
        d_col = abs(my_location.col - other_location.col)

        return d_row + d_col


class Board:

    def __init__(self, game):
        self._player0_pirate_list = []
        self._player0_drone_list = []
        self._player1_pirate_list = []
        self._player1_drone_list = []
        self._island_list = []
        self._player0_city_list = []
        self._player1_city_list = []
        self._player0_score = game.get_my_score()
        self._player1_score = game.get_enemy_score()
        self._unload_range = game.get_unload_range()
        self._control_range = game.get_control_range()

        for pirate in game.get_my_living_pirates():
            self._player0_pirate_list.append(MyAircraft(PIRATE, pirate.get_location(), pirate.id, MY_TEAM,
                                                        game.get_pirate_max_health(), pirate.max_speed,
                                                        pirate.attack_range))

        for pirate in game.get_enemy_living_pirates():
            self._player1_pirate_list.append(MyAircraft(PIRATE, pirate.get_location(), pirate.id, ENEMY_TEAM,
                                                        game.get_pirate_max_health(), pirate.max_speed,
                                                        pirate.attack_range))

        for drone in game.get_my_living_drones():
            self._player0_drone_list.append(MyAircraft(DRONE, drone.get_location(), drone.id, MY_TEAM,
                                                       game.get_drone_max_health(), drone.max_speed, 0))

        for drone in game.get_enemy_living_drones():
            self._player1_drone_list.append(MyAircraft(DRONE, drone.get_location(), drone.id, ENEMY_TEAM,
                                                       game.get_drone_max_health(), drone.max_speed, 0))

        for island in game.get_my_islands():
            self._island_list.append(MapLocation(ISLAND, island.get_location(), island.id, MY_TEAM))

        for island in game.get_enemy_islands():
            self._island_list.append(MapLocation(ISLAND, island.get_location(), island.id, ENEMY_TEAM))

        for island in game.get_not_my_islands():
            self._island_list.append(MapLocation(ISLAND, island.get_location(), island.id, NEUTRAL))

        for city in game.get_my_cities():
            self._player0_city_list.append(MapLocation(CITY, city.get_location(), city.id, MY_TEAM))

        for city in game.get_enemy_cities():
            self._player1_city_list.append(MapLocation(CITY, city.get_location(), city.id, ENEMY_TEAM))
        self._game = game
        self._rows = game.get_row_count()
        self._cols = game.get_col_count()
        self._actions = []
        # get possible stack locations for my city
        self._stack_options = self.get_stack_options(self._player0_city_list[0], stack_dist)

        self._stack_location = random.choice(self._stack_options)  # choose a random stack loaction

    def score_game(self, player):
        """
        Return the scoring for the game board given.
        Score includes:
        - 100 * dif between my score and enemy score (between -1900 to 1900)
        - 0.5 * (dif between my total HP and enemy total HP)
        - 2 * (dif between my islands and enemy islands) (between -2*num_of_cities to 2*num_of_cities)
        - 2 * (dif between my num of drones and enemy num of drones)
        - k * average distance between my drone and my city
        - (-k) * average distance between enemy drone and enemy city
        :return: score of game board
        :type: float
        """

        score = 0
        score += 100 * (self.get_my_score(player) - self.get_enemy_score(player))

        # Score takes into consideration the HP difference
        my_total_hp = sum([pirate.get_health() for pirate in self.get_my_living_pirates(player)])
        enemy_total_hp = sum([pirate.get_health() for pirate in self.get_enemy_living_pirates(player)])
        score += 0.8 * (my_total_hp - enemy_total_hp)

        # Score takes into consideration the dif between num of islands
        score += 10 * len(self.get_my_islands(player)) - 3*len(self.get_enemy_islands(player))

        # Score takes into consideration the dif between num of drones:
        score += 2 * (len(self.get_my_living_drones(player)) - len(self.get_enemy_living_drones(player)))

        if len(self.get_enemy_living_drones(player)) > 0:
            enemy_drone_to_city_distances = \
                [drone.distance(self.get_enemy_cities(player)[0]) for drone in self.get_enemy_living_drones(player)]
            score += 1.6 * (sum(enemy_drone_to_city_distances) / float(len(enemy_drone_to_city_distances)))

        # Score takes into consideration the average distance between my pirate and any other game object
        #  (not including my pirate and islands)
        if len(self.get_my_living_pirates(player)) > 0:
            distances = []
            if len(self.get_enemy_living_drones(player)) + len(self.get_not_my_islands(player)) != 0:
                for obj in self.get_enemy_living_drones(player) + self.get_not_my_islands(player):
                    distances.extend([pirate.distance(obj) for pirate in self.get_my_living_pirates(player)])
                score += -0.8 * (sum(distances) / float(len(distances)))

        return score

    def make_move(self, who, where):
        """
        Move in board. Assumes location is legal!
        :param who: Aircraft to move
        :type who: MyAircraft
        :param where: destination
        :type where: Location
        """
        who.set_location(where)
        self._actions.append(Action("MOVE", who, where))

    def make_attack(self, who, target):
        """
        do an attack
        :param who: attacker
        :type who: MyAircraft
        :param target: attack target
        :type target: MyAircraft
        """
        target.decrease_health(1)
        self._actions.append(Action("ATTACK", who, target))
        if target.get_health() == 0:
            if target.get_type() == DRONE:
                self.get_my_living_drones(target.get_team()).remove(target)
            else:
                self.get_my_living_pirates(target.get_team()).remove(target)

    def get_my_score(self, player):
        """
        gets my score
        :param player: who am I
        :type player: int
        :return: my score
        :rtype int
        """
        if player == MY_TEAM:
            return self._player0_score
        return self._player1_score

    def get_enemy_score(self, player):
        """
        get enemy score
        :param player: who am I
        :type player: int
        :return: enemy score
        :rtype int
        """
        if player == MY_TEAM:
            return self._player1_score
        return self._player0_score

    def get_my_living_pirates(self, player):
        """
        gets all my living pirates
        :param player: who am I
        :type player: int
        :return: list of all my living pirates
        :rtype list[MyAircraft]
        """
        if player == MY_TEAM:
            return self._player0_pirate_list
        return self._player1_pirate_list

    def get_enemy_living_pirates(self, player):
        """
        gets all enemy living pirates
        :param player: who am I
        :type player: int
        :return: list of all enemy living pirates
        :rtype list[MyAircraft]
        """
        if player == MY_TEAM:
            return self._player1_pirate_list
        return self._player0_pirate_list

    def get_my_living_drones(self, player):
        """
        gets all my living drones
        :param player: who am I
        :type player: int
        :return: list of all my living drones
        :rtype list[MyAircraft]
        """
        if player == MY_TEAM:
            return self._player0_drone_list
        return self._player1_drone_list

    def get_enemy_living_drones(self, player):
        """
        gets all enemy living drones
        :param player: who am I
        :type player: int
        :return: list of all enemy living drones
        :rtype list[MyAircraft]
        """
        if player == MY_TEAM:
            return self._player1_drone_list
        return self._player0_drone_list

    def get_my_islands(self, player):
        """
        gets all islands I control
        :param player: who am I
        :type player: int
        :return: list of all islands I control
        :rtype list[MapLocation]
        """
        return filter(lambda x: x.get_team() == player, self._island_list)

    def get_not_my_islands(self, player):
        """
        gets all islands I don't control
        :param player: who am I
        :type player: int
        :return: list of all islands I don't control
        :rtype list[MapLocation]
        """
        return filter(lambda x: x.get_team() != player, self._island_list)

    def get_enemy_islands(self, player):
        """
        gets all islands my enemy controls
        :param player: who am I
        :type player: int
        :return: list of all islands my enemy controls
        :rtype list[MapLocation]
        """
        return self.get_my_islands(switch_player(player))  # return all enemy's "my islands"

    def get_all_enemy_aircrafts_in_range(self, pirate, player):
        """
        finds all enemy aircrafts in attack range
        :param pirate: pirate to check attack range
        :type pirate: MyAircraft
        :param player: who am I
        :type player: int
        :return: list of all enemy aircrafts in attack range
        :rtype: list[Aircraft]
        """
        enemy_aircrafts = self.get_enemy_living_drones(player) + self.get_enemy_living_pirates(player)
        for craft in enemy_aircrafts[:]:
            if pirate.distance(craft) > pirate.get_attack_range():
                enemy_aircrafts.remove(craft)
        return enemy_aircrafts

    def get_my_cities(self, player):
        if player == MY_TEAM:
            return self._player0_city_list
        return self._player1_city_list

    def get_enemy_cities(self, player):
        return self.get_my_cities(switch_player(player))

    def clone(self):
        """
        clones this board
        :return: a lone of this board
        :rtype Board
        """
        clone = Board(self._game)
        return clone
        # clone._player0_pirate_list = self._player0_pirate_list[:]
        # clone._player1_pirate_list = self._player1_pirate_list[:]
        # clone._player0_drone_list = self._player0_drone_list[:]
        # clone._player1_drone_list = self._player1_drone_list[:]
        # clone._island_list = self._island_list[:]
        # clone._player0_city_list = self._player0_city_list[:]
        # clone._player1_city_list = self._player1_city_list[:]
        # clone._actions = self._actions[:]
        # clone._player0_score = self._player0_score
        # clone._player1_score = self._player1_score
        # clone._rows = self._rows
        # clone._cols = self._cols
        # return clone

    def _handle_pirates(self, player):
        """
        give all pirates one random legal order
        :param player: who am i
        :type player: int
        """
        for pirate in self.get_my_living_pirates(player):  # give command to each pirate
            r = random.random()  # pick a random number, r in range [0,1)
            attacked = False  # flag to check if pirate attacked or not
            if r < 0.5:  # 50% chance to attack
                can_be_attacked = self.get_all_enemy_aircrafts_in_range(pirate, player)
                if len(can_be_attacked) > 0:  # if we can attack at least one enemy
                    self.make_attack(pirate, random.choice(can_be_attacked))  # attack a random attackable target
                    attacked = True  # set flag to true - we just attacked
            if not attacked:  # move if couldn't attack or chose not to
                move_ops = self.get_move_options(pirate)
                self.make_move(pirate, random.choice(move_ops))

    def _handle_drones(self, player):
        """
        give all drones one random legal order
        :param player: who am i
        :type player: int
        """

        # handle all "stacked" drones waiting
        on_stack_location = self.get_my_drones_on(self._stack_location, player)
        if len(on_stack_location) >= min_drone_wait_num:
            self._adjust_stack(player)

        # handle all drones not yet stacked (or drones that were previously stacked but stack moved)
        for drone in filter(lambda x: x not in on_stack_location, self.get_my_living_drones(player)):
            move_ops = self.get_move_options_towards(drone,self._stack_location)
            self.make_move(drone, random.choice(move_ops))
            # handle drones scoring points
            if drone.distance(self.get_my_cities(player)[0]) < self._unload_range:
                if player == MY_TEAM:
                    self._player0_score += 1
                else:
                    self._player1_score += 1
                self.get_my_living_drones(player).remove(drone)  # drone dies after scoring a point

    def _check_island_ownership(self, player):
        for island in self.get_not_my_islands(player):
            # find all islands in  control range
            friendly_in_range = filter(lambda x: x.distance(island) <= self._control_range,
                                       self.get_my_living_pirates(player))
            enemy_in_range = filter(lambda x: x.distance(island) <= self._control_range,
                                    self.get_enemy_living_pirates(player))
            if len(friendly_in_range) < len(enemy_in_range):  # enemy has more ships then we do near this island
                island.set_team(switch_player(player))  # enemy controls this island
            elif len(friendly_in_range) > len(enemy_in_range):  # we have more ships then enemy does near this island
                island.set_team(player)  # we control this island
            elif len(friendly_in_range) == 0 and len(enemy_in_range) == 0:  # we both have no ships near this island
                return  # we original controller remains
            else:  # we both have the same non-zero number of ships
                island.set_team(NEUTRAL)  # no one controls this island

    def do_random_turn(self, player):
        """
        give all aircrafts one random legal order
        """
        self._actions = []  # get rid of last turn's actions
        if random.random() < 0.5:  # 50% chance to change stack  location
            ops = self._stack_options[:]
            ops.remove(self._stack_location)
            self._stack_location = random.choice(ops)
        self._handle_pirates(player)
        self._handle_drones(player)
        self._check_island_ownership(player)

    def run_trial(self, player):
        """
        run a game simulation of "turns" turns
        :param player: who am I
        :type player: int
        :return score of board
        :rtype: int
        """
        for i in range(2 * turns-1):  # we call this function on a board that has 1 "me" play
            self.do_random_turn(player)
            player = switch_player(player)
        return self.score_game(player)  # player will change to be me after loop ends

    def get_actions(self):
        return self._actions

    def get_move_options(self, aircraft):
        """
        returns all the locations aircraft can move to
        :param aircraft: aircraft to get move options
        :type aircraft: MyAircraft
        :return: all possible legal moves
        :rtype: list[Location]
        """
        aircraft_loc = aircraft.get_location()
        row = aircraft_loc.row
        col = aircraft_loc.col
        max_distance = aircraft.get_max_speed()
        options = []

        for i in range(max_distance+1):
            options.append(Location(row + i, col + (max_distance - i)))
            options.append(Location(row - i, col - (max_distance - i)))
            if i != 0 and i != max_distance:
                options.append(Location(row + i, col - (max_distance - i)))
                options.append(Location(row - i, col + (max_distance - i)))

        for loc in options[:]:
            if loc.row < 0 or loc.row >= self._rows:
                options.remove(loc)
                continue
            if loc.col < 0 or loc.col >= self._cols:
                options.remove(loc)

        return options

    def get_stack_options(self, city, distance):
        """
        gets all the location the drone can stack in (i.e. in distance of "stack_dist" from it"
        :param city: city to find stack options
        :type city: MapLocation
        :param distance: distance around city to stack
        :type distance: int
        :return: list of all stack options
        :rtype list[Location]
        """
        loc = city.get_location()
        row = loc.row
        col = loc.col
        options = [Location(row, col + distance), Location(row, col - distance),
                   Location(row - distance, col), Location(row + distance, col)]

        for loc in options[:]:
            if loc.row < 0 or loc.row >= self._rows:
                options.remove(loc)
                continue
            if loc.col < 0 or loc.col >= self._cols:
                options.remove(loc)

        return options

    def get_move_options_towards(self, aircraft, destination):
        """
        gets all the move options that get me closer to destination
        :param aircraft: aircraft to get move options
        :type aircraft: MyAircraft
        :param destination: where we want to go
        :type destination: MapLocation
        :return: list of all move options that get me close to destination
        :rtype list[Location]
        """
        ops = self.get_move_options(aircraft)
        current_distance = aircraft.distance(destination)
        closer_ops = filter(lambda x: destination.distance(x) < current_distance, ops)
        if len(closer_ops) == 0:
            closer_ops = [Location(aircraft.get_location().row,aircraft.get_location().col)]
        return closer_ops

    def get_my_drones_on(self, point, player):
        """
        gets all friendly drones on a certain point
        :param point: point to get all friendly drones on
        :type point: Location
        :param player: who am i
        :type player: int
        :return: list of all friendly drones on point
        :rtype: list[MyAircraft]
        """
        return filter(lambda  x: x.get_location() == point, self.get_my_living_drones(player))

    def _adjust_stack(self, player):
        city = self.get_my_cities(player)[0]
        if self._stack_location != city.get_location():
            self._stack_options = self.get_stack_options(city, self._stack_location.distance(city.get_location()) - 1)
            self._stack_location = random.choice(self._stack_options)
        else:
            self._stack_options = self.get_stack_options(city, stack_dist)
            self._stack_location = random.choice(self._stack_options)  # reset stack location
        return


# Constants and global variables
num_of_one_turn_trials = 25  # number of trials
num_of_mult_turn_trials = 12
num_of_best_boards = 5
turns = 2  # number of turns per trial
min_drone_wait_num = 15
stack_dist = 7


# Function Definitions

def clone_location(loc):
    return Location(loc.row, loc.col)


def switch_player(player):
    """
    switches the player
    :param player: player to switch
    :type player: int
    :return: the other player
    :rtype: int
    """
    if player == MY_TEAM:
        return ENEMY_TEAM
    else:
        return MY_TEAM


def choose_best_board(scores, boards):
    """
    finds the best score in scores and returns the corresponding board
    :param scores: list of averge scores of all boards tried
    :type scores: list[int]
    :param boards: list of all boards
    :type boards: list[Board]
    :return: the best board
    :rtype: Board
    """
    maxs = max(scores)  # find the best score
    idx = scores.index(maxs)  # find the index of the score
    return boards[idx]  # return the set of actions in the same index
    # (score[n] corresponds to boards[n] board)


def execute_turn(best, game):
    """
    do the turn, i.e. the game calls
    :param best: the board with the highest potential, only one turn is played on it
    :type best: Board
    :param game: the game to play on
    :type game: PirateGame
    """
    acts = best.get_actions()
    # game.debug(len(acts))
    for act in acts:
        if act.get_type() == "MOVE":
            destination = act.get_where()
            type = act.get_who().get_type()
            if type == DRONE:
                game.set_sail(game.get_my_drone_by_id(act.get_who().get_id()), destination)
            else:
                game.set_sail(game.get_my_pirate_by_id(act.get_who().get_id()), destination)
        else:
            type = act.get_where().get_type()
            if type == DRONE:
                target = game.get_enemy_drone_by_id(act.get_where().get_id())
            else:
                target = game.get_enemy_pirate_by_id(act.get_where().get_id())
            game.attack(game.get_my_pirate_by_id(act.get_who().get_id()), target)


def make_board(game):
    """
    makes a board instance from the game object provided
    :param game: the current game state
    :type game: PirateGame
    :return: the current game state as an instance of Board
    :rtype Board
    """
    board = Board(game)
    return board


def choose_n_best_boards(boards, n):
    """
    returns the best n moves
    :param boards: a list of all moves we made
    :type boards: list[Board]
    :param n: number of boards to choose
    :type n: int
    :return: the n best boards
    :rtype: list[Board]
    """
    i = n
    scores = map(lambda x: x.score_game(MY_TEAM), boards)
    best_boards = []
    while i > 0:
        best_board = choose_best_board(scores, boards)
        best_boards.append(best_board)
        boards.remove(best_board)
        scores.remove(best_board.score_game(MY_TEAM))
        i -= 1
    return best_boards


def average(lst):
    """
    computes the average of the list lst
    :param lst: list to compute average
    :type lst: list[]
    :return: the average of the list
    :rtype int
    """
    return sum(lst)/float(len(lst))


def do_turn(game):
    """
    Makes the bot run a single turn
    :param game: the current game state
    :type game: PirateGame
    """
    board = make_board(game)
    boards = []
    for i in range(num_of_one_turn_trials):
        clone = board.clone()
        clone.do_random_turn(MY_TEAM)
        boards.append(clone)
    best_one_turn = choose_n_best_boards(boards, num_of_best_boards)
    # scores = [board.score_game(MY_TEAM) for board in best_one_turn]
    scores = []
    for b in best_one_turn:
        b_scores = [b.clone().run_trial(ENEMY_TEAM) for i in range(num_of_mult_turn_trials)]
        scores.append(average(b_scores))
    best = choose_best_board(scores, best_one_turn)
    execute_turn(best, game)
