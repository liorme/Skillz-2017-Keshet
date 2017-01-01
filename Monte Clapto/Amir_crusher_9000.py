"""
Bot using Monte-Carlo simulations
"""

# Imports
from Pirates import *
import random
import math
import timeit


# Class Definitions

# Class constants

PIRATE = 0
DRONE = 1
ISLAND = 2
CITY = 3

MY_TEAM = 0
ENEMY_TEAM = 1
NEUTRAL = 2  # for islands

file = open('runtimes.txt','w')
file.close()
functimes = []
def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        file = open('runtimes.txt', 'a')
        file.write('%s function took %0.3f ms\n' % (f.func_name, (time2-time1)*1000.0))
        file.close()
        return ret
    return wrap


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

    def __init__(self, aircraft, type, team, max_respawn, max_health):
        """

        :param self:
        :param aircraft:
        :type aircraft: Aircraft
        :return:
        """
        self._type = type
        self._location = clone_location(aircraft.get_location())
        self._id = aircraft.id
        self._team = team
        self._health = aircraft.current_health
        self._max_health = max_health
        self._attack_range = 0
        self._max_move = aircraft.max_speed
        self._respawn_time = 0
        self._max_respawn_time = max_respawn
        if type == PIRATE:
            self._attack_range = aircraft.attack_range
            self._respawn_time = aircraft.turns_to_revive
            self._max_respawn_time = max_respawn

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
        if self._health <= 0:  # handle deaths
            self._health = self._max_health
            self._respawn_time = self._max_respawn_time

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

    def is_alive(self):
        return self._respawn_time == 0

    def get_respawn_time(self):
        return self._respawn_time

    def set_respawn_time(self, new_respawn):
        self._respawn_time = new_respawn


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


class Board:

    def __init__(self, game):
        """

        :param game:
         :type game: PirateGame
        """
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

        for pirate in game.get_all_my_pirates():
            self._player0_pirate_list.append(MyAircraft(pirate, PIRATE, MY_TEAM, game.get_spawn_turns(), game.get_pirate_max_health()))

        for pirate in game.get_all_enemy_pirates():
            self._player1_pirate_list.append(MyAircraft(pirate, PIRATE, ENEMY_TEAM, game.get_spawn_turns(), game.get_pirate_max_health()))

        for drone in game.get_my_living_drones():
            self._player0_drone_list.append(MyAircraft(drone, DRONE, MY_TEAM, 0, game.get_drone_max_health()))

        for drone in game.get_enemy_living_drones():
            self._player1_drone_list.append(MyAircraft(drone, DRONE, ENEMY_TEAM, 0, game.get_drone_max_health()))

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
        city_loc = self._player0_city_list[0].get_location()
        self._stack = Location(city_loc.row - 5, city_loc.col + 2)

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
        score += 1000 * (self.get_my_score(player) - self.get_enemy_score(player))

        # Score takes into consideration the HP difference
        my_total_hp = sum([pirate.get_health() for pirate in self.get_my_living_pirates(player)])
        enemy_total_hp = sum([pirate.get_health() for pirate in self.get_enemy_living_pirates(player)])
        score += 0.8 * (my_total_hp - enemy_total_hp)

        # Score takes into consideration the dif between num of islands
        score += 500 * len(self.get_my_islands(player)) - 3*len(self.get_enemy_islands(player))

        # Score takes into consideration the dif between num of drones:
        score += 2 * (len(self.get_my_living_drones(player)) - len(self.get_enemy_living_drones(player)))

        if len(self.get_enemy_living_drones(player)) > 0:
            enemy_drone_to_city_distances = \
                [drone.distance(self.get_enemy_cities(player)[0]) for drone in self.get_enemy_living_drones(player)]
            score += 1.6 * average(enemy_drone_to_city_distances)

        # Score takes into consideration the average distance between my pirate and any other game object
        #  (not including my pirate and islands)
        if len(self.get_my_living_pirates(player)) > 0:
            distances = []
            if len(self.get_enemy_living_drones(player)) + len(self.get_not_my_islands(player)) != 0:
                for obj in self.get_enemy_living_drones(player) + self.get_not_my_islands(player):
                    distances.extend([pirate.distance(obj) for pirate in self.get_my_living_pirates(player)])
                score += -0.8 * average(distances)

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
        return self.get_my_score(switch_player(player))

    def get_all_my_pirates(self, player):
        """
        gets all my pirates
        :param player: who am I
        :type player: int
        :return: list of all my pirates
        :rtype list[MyAircraft]
        """
        if player == MY_TEAM:
            return self._player0_pirate_list
        return self._player1_pirate_list

    def get_all_enemy_pirates(self, player):
        """
        gets all enemy pirates
        :param player: who am I
        :type player: int
        :return: list of all enemy pirates
        :rtype list[MyAircraft]
        """
        return self.get_all_my_pirates(switch_player(player))

    def get_my_living_pirates(self, player):
        """
        gets all my living pirates
        :param player: who am I
        :type player: int
        :return: list of all my living pirates
        :rtype list[MyAircraft]
        """
        return filter(lambda x: x.is_alive(), self.get_all_my_pirates(player))

    def get_enemy_living_pirates(self, player):
        """
        gets all enemy living pirates
        :param player: who am I
        :type player: int
        :return: list of all enemy living pirates
        :rtype list[MyAircraft]
        """
        return self.get_my_living_pirates(switch_player(player))

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
        return self.get_my_living_drones(switch_player(player))

    def get_my_living_aircrafts(self, player):
        """
        gets all my living aircrafts
        :param player: who am I
        :type player: int
        :return: list of all my living aircrafts
        :rtype list[MyAircraft]
        """
        return self.get_my_living_drones(player) + self.get_y_living_pirates(player)

    def get_enemy_living_aircrafts(self, player):
        """
        gets all enemy living aircrafts
        :param player: who am I
        :type player: int
        :return: list of all enemy living aircrafts
        :rtype list[MyAircraft]
        """
        return self.get_my_living_aircrafts(player)

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
        return filter(lambda x: pirate.distance(x) <= pirate.get_attack_range(),
                      self.get_enemy_living_drones(player) + self.get_enemy_living_pirates(player))

    def get_my_cities(self, player):
        if player == MY_TEAM:
            return self._player0_city_list
        return self._player1_city_list

    def get_enemy_cities(self, player):
        return self.get_my_cities(switch_player(player))

    def get_my_drone_by_id(self, team, id):
        return filter(lambda x: x.get_id() == id, self.get_my_living_drones(team))[0]  # only one drone with this ID

    def get_my_pirate_by_id(self, team, id):
        return filter(lambda x: x.get_id() == id, self.get_all_my_pirates(team))[0]  # only one drone with this ID

    def apply_actions(self, actions):
        """
        apply all the actions in "actions" to this board
        :param actions:  list of actions to apply
        :type actions: list[Action]
        :return:
        """
        for act in actions:
            if act.get_type() == "MOVE":  # it's a move
                who = act.get_who()
                destination = act.get_where()
                type = who.get_type()
                if type == DRONE:
                    mover = self.get_my_drone_by_id(who.get_team(), who.get_id())
                else:
                    mover = self.get_my_pirate_by_id(who.get_team(), who.get_id())
                self.make_move(mover, destination)
            else:  # it's an attack
                where = act.get_where()
                who = act.get_who()
                type = where.get_type()
                if type == DRONE:
                    target = self.get_my_drone_by_id(where.get_team(), where.get_id())
                else:
                    target = self.get_my_pirate_by_id(where.get_team(), where.get_id())
                self.make_attack(self.get_my_pirate_by_id(who.get_team(), who.get_id()), target)

    def clone(self):
        """
        clones this board
        :return: a lone of this board
        :rtype Board
        """
        clone = Board(self._game)
        clone.apply_actions(self._actions)
        return clone

    def is_my_city_clear(self, player):
        """
        check if an enemy pirate is near my city
        :param player: who am I
        :type player: int
        :return: whether my city is clear or not
        :rtype bool
        """
        city = self.get_my_cities(player)[0]
        for pirate in self.get_enemy_living_pirates(player): # type: MyAircraft
            if pirate.distance(city) <= clear_range:
                return False
        return True

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
                    self.make_attack(pirate, random.choice(can_be_attacked))  # attack a random attack able target
                    attacked = True  # set flag to true - we just attacked
            if not attacked:  # move if couldn't attack or chose not to.
                move_ops = self.get_move_options(pirate)
                self.make_move(pirate, random.choice(move_ops))

    def _handle_drones(self, player):
        """
        give all drones one random legal order
        :param player: who am i
        :type player: int
        """
        if self.is_my_city_clear(player) or len(self.get_my_drones_on(player, self._stack)) >= min_stack_wait:
            # send drones to city
            destination = self.get_my_cities(player)[0]
        else:
            # send drones to stack location
            destination = self._stack

        for drone in self.get_my_living_drones(player):
            poss_moves = self.get_move_options_towards(drone, destination)
            move = random.choice(poss_moves)
            self.make_move(drone, move)
            # handle drones scoring points
            if drone.get_type() == DRONE and drone.distance(self.get_my_cities(player)[0]) < self._unload_range:
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
        # handle respawn
        for pirate in self.get_all_my_pirates(player):  # type: MyAircraft
            if not pirate.is_alive():
                pirate.set_respawn_time(pirate.get_respawn_time())
            # if re-spawn time is 0 it it automatically set as alive
        if player == MY_TEAM:
            self._player0_drone_list = filter(lambda x: x.is_alive(), self._player0_drone_list)
        else:
            self._player1_drone_list = filter(lambda x: x.is_alive(), self._player1_drone_list)
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
        i = 2*turns-1
        while i > 0:  # we call this function on a board that has 1 "me" play
            self.do_random_turn(player)
            player = switch_player(player)
            i -= 1
        return self.score_game(player)  # player will change to be me after loop ends

    def get_actions(self):
        return self._actions

    def get_move_options(self, aircraft):
        """
        returns all the location pirate can move to
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
        if max_distance == 1:
            options = [Location(row - 1, col), Location(row + 1, col), Location(row, col - 1),
                       Location(row, col + 1)]  # distance of 1
        if max_distance == 2:
            options.extend(
                [Location(row - 2, col), Location(row + 2, col), Location(row, col + 2),
                 Location(row, col - 2)])  # within straight distance of 2
            options.extend([Location(row - 1, col - 1), Location(row + 1, col - 1),
                            Location(row - 1, col + 1), Location(row - 1, col - 1)])

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
        closer_ops = filter(lambda x: destination.get_location().distance(x) < current_distance, ops)
        if len(closer_ops) == 0:
            closer_ops = [Location(aircraft.get_location().row, aircraft.get_location().col)]
        return closer_ops

    def get_my_drones_on(self, player, point):
        return filter(lambda x: x.get_location() == point, self.get_my_living_drones(player))

# Constants and global variables
num_of_one_turn_trials = 60  # number of trials
num_of_mult_turn_trials = 25
num_of_best_boards = 5
turns = 2  # number of turns per trial
clear_range = 4
min_stack_wait = 15


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
    for act in acts:
        if act.get_type() == "MOVE":  # type: Action
            destination = act.get_where()
            who = act.get_who()
            type = act.get_who().get_type()
            if type == DRONE:
                mover = game.get_my_drone_by_id(who.get_id())
            else:
                mover = game.get_my_pirate_by_id(who.get_id())
            game.set_sail(mover, destination)
        else:
            type = act.get_where().get_type()
            who = act.get_who()
            where = act.get_where()
            if type == DRONE:
                target = game.get_enemy_drone_by_id(where.get_id())
            else:
                target = game.get_enemy_pirate_by_id(where.get_id())
            attacker = game.get_my_pirate_by_id(who.get_id())
            game.attack(attacker, target)


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

@timing
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
    before = game.get_time_remaining()
    num_of_mult_trials = (before+100) / (3 * len(best_one_turn))
    game.debug(num_of_mult_trials)
    for b in best_one_turn:
        b_scores = [b.clone().run_trial(ENEMY_TEAM) for i in range(num_of_mult_trials)]
        scores.append(average(b_scores))
    best = choose_best_board(scores, best_one_turn)
    execute_turn(best, game)
