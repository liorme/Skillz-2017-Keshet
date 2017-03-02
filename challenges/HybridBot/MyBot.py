from Pirates import *

import random
from my_pirates import *
from drones import *
from utility import *
from shared import *



# Global Variables:
set = False

# Constants:
ENEMY_DRONE_REMEMBER_FACTOR = 0.99
ENEMY_PIRATE_REMEMBER_FACTOR = 0.9



#MAIN
def do_turn(game):
	global battles, enemy_drones_board, full_tiles, danger_board
	global ave_destination
	global rows, cols
	global set
	global range3

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

	# add current danger tiles to danger_board:
	danger_pirates = game.get_enemy_living_pirates()
	for pirate in danger_pirates:
		row = pirate.location.row
		col = pirate.location.col
		for directions in range3:
			dirow = row + directions[0]
			dicol = col + directions[1]
			if 0 <= dirow < rows and 0 <= dicol < cols:
				danger_board[(dirow, dicol)] += 1
				
	choose_state(game)

	update_battles(game)
	handle_pirates(game, game_state, battles)
	handle_drones(game, game_state)
	handle_decoy(game, game_state)

	debug(game, "Time remaining for turn: " + str(game.get_time_remaining()) + "ms")

