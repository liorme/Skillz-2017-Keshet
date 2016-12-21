from Pirates import *
from random import randint

def do_turn(game):

    islands = [{"i":i.id,"r":i.loction.row,"c":i.loction.col,"o":i.owner} for i in game.get_islands()]
    my_pirates = [{"i":i.id,"r":i.loction.row,"c":i.loction.col,"h":i.current_health} for i in game.get_my_pirates()]
    enemy_pirates = [{"i":i.id,"r":i.loction.row,"c":i.loction.col,"h":i.current_health} for i in game.get_enemy_pirates()]
    my_drones = [{"i":i.id,"r":i.loction.row,"c":i.loction.col} for i in game.get_my_living_drones()]
    enemy_drones = [{"i":i.id,"r":i.loction.row,"c":i.loction.col} for i in game.get_enemy_living_drones()]
    game_status = {"c":{"r":game.get_my_cities()[0].loction.row,"c":game.get_my_cities()[0].loction.col},"ec":{"r":game.get_my_cities()[0].loction.row,"c":game.get_my_cities()[0].loction.col},"i":islands,"p":my_pirates,"ep":enemy_pirates,"d":my_drones,"ed":enemy_drones}

    gen = create_first_gen(game_status)
    best = [-sys.maxint]
    while game.get_time_remaining() > 10:
        score(gen)
        best_this_gen = sorted(gen)[-1]
        if best_this_gen[0] > best[0]:
            best = best_this_gen
        gen = create_new_gen(gen)
    execute(best)

def create_first_gen(game_status):
    gen = []
    append = gen.append
    for i in range(70):
        m = {"p":[],"d":[]}
        m["p"] = map(prm, game_status["p"])
        m["d"] = map(drm, game_status["d"])
        append(m)
    return gen

def score(gen, game_status):
    pass

def create_new_gen(gen):
    pass

def execute(best):
    pass

def prm(pirate):
    r = randint(0,8)
    return {"r":pirate["r"]+r%5-2,"c":pirate["c"]+(r+2)%5-2}

def drm(drone):
    r = randint(0,4)
    return {"r":drone["r"]+r%3-1,"c":drone["c"]+(r+1)%3-1}
