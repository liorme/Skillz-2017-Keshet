from Pirates import *
range3 = [(3, 0), (2, -1), (2, 0), (2, 1), (1, -2), (1, -1), (1, 0), (1, 1), (1, 2), (0, -3), (0, -2), (0, -1), (0, 0),
          (0, 1), (0, 2), (0, 3), (-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2), (-2, -1), (-2, 0), (-2, 1), (-3, 0)]
battles = []
ave_destination = Location(0, 23)
enemy_drones_board = {}  # dictionary of all places in the board through which an enemy drone has passed.
danger_board = {}  # places in which no drone has passed aren't in the dictionary
full_tiles = []  # list of keys of enemy_drones_board
rows = 1
cols = 1
game_state = ""
