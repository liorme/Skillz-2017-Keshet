import sys
import math
import random

SIZE_MIN = 20 #Must be even and at least 6
SIZE_MAX = 100 #must be even
ISLANDS_MIN = 3
ISLANDS_MAX = 6
PIRATES_MIN = 3
PIRATES_MAX = 8
CITIES_MIN = 1
CITIES_MAX = 2
IS_SQUARE = True

def main():
    random.seed()
    rows = random.randint(SIZE_MIN,SIZE_MAX)
    half_cols = random.randint(SIZE_MIN/2,SIZE_MAX/2)
    if IS_SQUARE:
        half_cols = int(rows/2)
    cols = 2*half_cols
    islands_per_side = random.randint(ISLANDS_MIN,ISLANDS_MAX)
    cities_per_side = random.randint(CITIES_MIN,CITIES_MAX)
    island_locations =[]
    for island in range(islands_per_side):
        island_locations.append([random.randint(5,rows-5), random.randint(5, half_cols-5)])
    for island in island_locations[:]:
        island_locations.append([island[0], cols-island[1]])
    pirates_per_side = random.randint(PIRATES_MIN,PIRATES_MAX)
    spawn_locations = []
    for pirate in range(pirates_per_side):
        spawn_locations.append([0,random.randint(2,rows-2) ,random.randint(2,half_cols-2)])
    for pirate in spawn_locations[:]:
        spawn_locations.append([1,pirate[1],cols-pirate[2]])
    cities0 = []
    for city in range(cities_per_side):
        cities0.append([random.randint(5,rows-5), random.randint(5, half_cols-5)])
    cities1 = []
    for city in cities0:
        cities1.append([city[0], cols - city[1]])

    ###PRINT
    print "rows " + str(rows)
    print "cols " + str(cols)
    print "players 2"
    city_id = 0
    for city in range(cities_per_side):
        print "city " + str(city_id) + " 0"
        print "city " + str(city_id + 1) + " 1"
        city_id += 2
    print ""
    for x in range(rows):
        line = "m "
        for y in range(cols):
            is_done = False
            if [x,y] in cities0+cities1:
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
