import sys
import math
import random

def main():
    random.seed()
    rows = random.randint(20,100)
    half_cols = random.randint(10,50)
    cols = 2*half_cols
    islands_per_side = random.randint(3,6)
    city_0_loc = [random.randint(5,rows-5), random.randint(5, half_cols-5)]
    island_locations =[]
    for island in range(islands_per_side):
        island_locations.append([random.randint(5,rows-5), random.randint(5, half_cols-5)])
    for island in island_locations[:]:
        island_locations.append([island[0], cols-island[1]])
    city_1_loc = [city_0_loc[0], cols-city_0_loc[1]]
    pirates_per_side = random.randint(3,8)
    spawn_locations = []
    for pirate in range(pirates_per_side):
        spawn_locations.append([0,random.randint(2,rows-2) ,random.randint(2,half_cols-2)])
    for pirate in spawn_locations[:]:
        spawn_locations.append([1,pirate[1],cols-pirate[2]])

    ###PRINT
    print "rows " + str(rows)
    print "cols " + str(cols)
    print "players 2"
    print "city 0 1"
    print "city 1 0"
    print ""
    for x in range(rows):
        line = "m "
        for y in range(cols):
            is_done = False
            if [x,y] in [city_0_loc,city_1_loc]:
                line += "C"
                is_done = True
            elif [x,y] in island_locations:
                line += "I"
                is_done = True
            for spawn in spawn_locations:
                if [x,y] == [spawn[1],spawn[2]]:
                    if spawn[0] == 0:
                        line += "a"
                    elif spawn[0] == 1:
                        line += "b"
                    is_done = True
            if not is_done:
                line += "."
        print line




main()