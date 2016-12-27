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
        self._location = location
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
        self._location = new_loc

    def get_health(self):
        return self._health

    def decrease_health(self, n):
        self._health -= n

    def distance(self, other):
        """
        computes the distance between me and other
        :param other: aircraft to compute distance
        :type other: MyAircraft
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
        score += 3 * (len(self.get_my_islands(player)) - len(self.get_enemy_islands(player)))

        # Score takes into cosideration the dif between num of drones:
        score += 2 * (len(self.get_my_living_drones(player)) - len(self.get_enemy_living_drones(player)))

        # Score takes into consideration the average distance between my drone and my city
        if len(self.get_my_living_drones(player)) > 0:
            my_drone_to_city_distances = [drone.distance(self.get_my_cities(player)[0]) for drone in
                                          self.get_my_living_drones(player)]
            score += -0.8 * (sum(my_drone_to_city_distances) / float(len(my_drone_to_city_distances)))
        if len(self.get_enemy_living_drones(player)) > 0:
            enemy_drone_to_city_distances = \
                [drone.distance(self.get_enemy_cities(player)[0]) for drone in self.get_enemy_living_drones(player)]
            score += 1.6 * (sum(enemy_drone_to_city_distances) / float(len(enemy_drone_to_city_distances)))

        # Score takes into consideration the average distance between my pirate and any other game object
        #  (not including my pirate and islands)
        if len(self.get_my_living_pirates(player)) > 0:
            distances = []
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
        :rtype List[MyAircraft]
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
        :rtype List[MyAircraft]
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
        :rtype List[MyAircraft]
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
        :rtype List[MyAircraft]
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
        :rtype List[MapLocation]
        """
        return filter(lambda x: x.get_team() == player, self._island_list)

    def get_not_my_islands(self, player):
        """
        gets all islands I don't control
        :param player: who am I
        :type player: int
        :return: list of all islands I don't control
        :rtype List[MapLocation]
        """
        return filter(lambda x: x.get_team() != player, self._island_list)

    def get_enemy_islands(self, player):
        """
        gets all islands my enemy controls
        :param player: who am I
        :type player: int
        :return: list of all islands my enemy controls
        :rtype List[MapLocation]
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
        :rtype: List[Aircraft]
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
        clone._player0_pirate_list = self._player0_pirate_list[:]
        clone._player1_pirate_list = self._player1_pirate_list[:]
        clone._player0_drone_list = self._player0_drone_list[:]
        clone._player1_drone_list = self._player1_drone_list[:]
        clone._island_list = self._island_list[:]
        clone._player0_city_list = self._player0_city_list[:]
        clone._player1_city_list = self._player1_city_list[:]
        clone._actions = self._actions[:]
        clone._player0_score = self._player0_score
        clone._player1_score = self._player1_score
        clone._rows = self._rows
        clone._cols = self._cols
        return clone

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
                move_ops = self.get_move_options(pirate, pirate.get_max_speed())
                self.make_move(pirate, random.choice(move_ops))

    def _handle_drones(self, player):
        """
        give all drones one random legal order
        :param player: who am i
        :type player: int
        """
        for drone in self.get_my_living_drones(player):
            poss_moves = self.get_move_options(drone, drone.get_max_speed())
            move = random.choice(poss_moves)
            self.make_move(drone, move)

    def do_random_turn(self, player):
        """
        give all aircrafts one random legal order
        """
        self._actions = []  # get rid of last turn's actions
        self._handle_pirates(player)
        self._handle_drones(player)

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

    def get_move_options(self, aircraft, max_distance):
        """
        returns all the location pirate can move to
        :param aircraft: aircraft to get move options
        :type aircraft: MyAircraft
        :param max_distance: the max distance the aircraft can move
        :return: all possible legal moves
        :rtype: List[Location]
        """
        aircraft_loc = aircraft.get_location()
        row = aircraft_loc.row
        col = aircraft_loc.col
        options = []
        if max_distance == 1:
            options = [Location(row - 1, col), Location(row + 1, col), Location(row, col - 1), Location(row, col + 1), Location(row, col)]  # distance of 1
        if max_distance == 2:
            options.extend(
                [Location(row - 2, col), Location(row + 2, col), Location(row, col + 2), Location(row, col - 2)])  # within straight distance of 2
            options.extend([Location(row - 1, col - 1), Location(row + 1, col - 1), Location(row - 1, col + 1), Location(row - 1, col - 1)])

        for loc in options[:]:
            if loc.row < 0 or loc.row >= self._rows:
                options.remove(loc)
                continue
            if loc.col < 0 or loc.col >= self._cols:
                options.remove(loc)
        return options

# Constants and global variables
num_of_one_turn_trials = 60  # number of trials
num_of_mult_turn_trials = 35
num_of_best_boards = 5
turns = 3  # number of turns per trial
min_drone_wait_num = 15


# Function Definitions


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
    :type scores: List[int]
    :param boards: list of all boards
    :type boards: List[Board]
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
    game.debug(len(acts))
    for act in acts:
        if act.get_type() == "MOVE":
            destination = act.get_where()
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
    :type boards: List[Board]
    :param n: number of boards to choose
    :type n: int
    :return: the n best boards
    :rtype: List[Board]
    """
    i = n
    scores = map(lambda x: x.score_game(MY_TEAM), boards)
    best_boards = []
    while i > 0:
        best_boards.append(choose_best_board(scores, boards))
        i -= 1
    return best_boards


def average(lst):
    """
    computes the average of the list lst
    :param lst: list to compute average
    :type lst: List[]
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
    scores = []
    for b in best_one_turn:
        b_scores = [b.clone().run_trial(ENEMY_TEAM) for i in range(num_of_mult_turn_trials)]
        scores.append(average(b_scores))
    best = choose_best_board(scores, best_one_turn)
    execute_turn(best, game)
