"""
This is an example for a bot.
"""
from Pirates import *
import random
import copy
import math

# Class defenitions
class Action:
    def __init__(self,type,org,target):
        self._type = type
        self._org = org
        self._target = target

    def get_type(self):
        """
        returns the type of the Action
        :return: type of this Action
        :rtype String
        """
        return self._type

    def get_target(self):
        """
        returns the target of the Action
        :return: target of this Action
        :rtype Location or Aircraft
        """
        return self._target

    def get_org(self):
        """
        returns the origin of the Action
        :return: origin of this Action
        :rtype Pirate
        """
        return self._org

# Constants and global variables
N = 10 # number of trials
turns = 4 # number of turns per trial


def switch_player(game):
    """
    switches "myself" to enemy and vice-versa
    :param game:
    :return:
    """
    me = game.get_myself()
    if me.id == me_id:
        me.id = enemy_id
    else:
        me.id = me_id

def play_rand_turn(game):
    """
    plays one random turn
    :param game: the game to play on
    :type game: PiratesGame
    """
    turn = []
    for pirate in game.get_my_living_pirates():
        r = random.random()
        attacked = False
        if r < 0.5:  # 50% chance to attack
            can_be_attacked = []
            for enemy in game.get_enemy_living_aircrafts():
                if pirate.in_attack_range(enemy):
                    can_be_attacked.append(enemy)
            if len(can_be_attacked) > 0:
                turn.append(Action("ATTACK", pirate, random.choice(can_be_attacked)))
                attacked = True
        elif r > 0.5 or (not attacked):  # 50% chance to make a move
            islands = game.get_all_islands()
            rand_island = random.choice(islands)
            sails_ops = game.get_sail_options(pirate, rand_island)
            if len(sails_ops) > 0:
                turn.append(Action("MOVE", pirate, random.choice(sails_ops)))
    rad = abs(game.get_my_cities()[0].location.col -game.get_enemy_cities()[0].location.col) / 2
    for drone in game.get_my_living_drones():
        angle = random.randrange(0,359)
        loc = Location(rad*math.sin(angle),rad*math.cos(angle))
        game.set_sail(drone,loc)
    return turn

def score_game(game):
    return 0

def run_trial(game):
    set = False
    my_action = None
    for dummy_i in range(2*turns):
        act = play_rand_turn(game)
        if not set:
            my_action = act
        switch_player(game)
    score = score_game(game)
    return [score,my_action]

def choose_best_acts(scores,actions):
    maxs = max(scores)
    idx = scores.index(maxs)
    return actions[idx]

def execute_turn(best,game):
    for act in best:
        if act.get_type() == "MOVE":
            game.set_sail(act.get_org(),act.get_target())
        else:
            game.attack(act.get_org(),act.get_target())

def do_turn(game):
    """
    Makes the bot run a single turn
    :param game: the current game state
    :type game: PiratesGame
    """
    me_id = game.get_myself().id
    enemy_id = game.get_enemy().id
    global me_id # ID of my player
    global enemy_id #ID of enemy player
    scores = []
    actions = []
    for dummy_i in range(N):
        cp = copy.deepcopy(game)
        ret = run_trial(cp)
        scores.append(ret[0])
        actions.append(ret[1])
    best = choose_best_acts(scores,actions)
    execute_turn(best,game)

"""    # Give orders to my pirates
    handle_pirates(game)
    # Give orders to my drones
    handle_drones(game)

def handle_pirates(game):
    """"""
    Gives orders to my pirates

    :param game: the current game state
    :type game: PiratesGame
""""""
    N = 10 #number of simulations
    scores = []
    turns = []
    for dummy_i in range(N):
        turn = []
        for pirate in game.get_my_living_pirates():
            r = random.random()
            attacked = False
            if r < 0.5:  # 50% chance to attack
                can_be_attacked = []
                for enemy in game.get_enemy_living_aircrafts():
                    if pirate.in_attack_range(enemy):
                        can_be_attacked.append(enemy)
                if len(can_be_attacked) > 0:
                    turn.append(Action("ATTACK",pirate,random.choice(can_be_attacked)))
                    attacked = True
            elif r > 0.5 or not attacked :  # 50% chance to make a move
                islands = game.get_all_islands()
                rand_island = random.choice(islands)
                sails_ops = game.get_sail_options(pirate,rand_island)
                if len(sails_ops) > 0:
                    turn.append(Action("MOVE",pirate,random.choice(sails_ops)))
        scores.append(score_game(turn,game))
        turns.append(turn)
    best = turns[scores.index(max(scores))]
    for act in best:
        if act.get_type() == 'MOVE':
            game.set_sail(act.get_org(),act.get_target())
        elif act.get_type() == 'ATTACK':
            game.attack(act.get_org(),act.get_target())


def score_game(turn,g):
    game = copy.deepcopy(g)
    for act in turn:
        if act.get_type() == 'MOVE':
            game.set_sail(act.get_org(),act.get_target())
        elif act.get_type() == 'ATTACK':
            game.attack(act.get_org(),act.get_target())
    score = 0
    # pirate health - more is good
    score += sum([pirate.current_health for pirate in game.get_my_living_pirates()])
    # enemy health - more is bad
    score -= sum([enemy.current_health for enemy in game.get_enemy_living_aircrafts()])
    # islands I control - good
    score += len(game.get_my_islands())
    # island enemy control - bad
    score -= len(game.get_not_my_islands())
    # my living pirates - good
    score += len(game.get_my_living_pirates())
    # enemy living pirates - bad
    score -= len(game.get_enemy_living_pirates())
    # enemy living drones - very bad
    score -= 5*len(game.get_enemy_living_drones())
    return score


def handle_drones(game):
    pass
"""