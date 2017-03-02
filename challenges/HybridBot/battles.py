from utility import *
from Pirates import *
import math
from shared import *

class Battle:
	def __init__(self, my_pirates, enemy_pirates, my_location_pirate, enemy_location_pirate):
		self._my_pirates = my_pirates
		self._enemy_pirates = enemy_pirates
		self._my_location_pirate = my_location_pirate
		self._enemy_location_pirate = enemy_location_pirate
		self._turns_remaining = 0
		self._helping_pirates = []
		self._win = False

	def get_my_pirates(self):
		return self._my_pirates

	def get_enemy_pirates(self):
		return self._enemy_pirates

	def get_my_location_pirate(self):
		return self._my_location_pirate

	def get_enemy_location_pirate(self):
		return self._enemy_location_pirate

#Checks if an attack is part of a battle or a new battle
def is_new_battle(attack):
	for battle in battles:
		if battle.get_my_location_pirate().location == attack.get_attacker().location or battle.get_enemy_location_pirate() == attack.get_target():
			return False
	return True
#Creates a new battle
def create_new_battle(attack, game):
	battle = Battle([], [], attack.get_attacker(), attack.get_target())
	enemy_pirates = game.get_enemy_living_pirates()
	my_pirates = game.get_my_living_pirates()
	for pirate in my_pirates:
		if attack.get_target().in_attack_range(pirate):
			battle._my_pirates.append(pirate)
	for pirate in enemy_pirates:
		if attack.get_attacker().in_attack_range(pirate):
			battle._enemy_pirates.append(pirate)
	battle = turns_remaining_to_battle(battle)
	battles.append(battle)
#Updates all battles in the beginning of a new turn
def update_battles(game):
	enemy_pirates = game.get_enemy_living_pirates()
	my_pirates = game.get_my_living_pirates()
	for battle in battles:
		# update_location_pirate(battle, all_pirates, game)
		if battle.get_my_location_pirate() in my_pirates:
			battle._my_pirates = []
			battle._enemy_pirates = []
			for pirate in my_pirates:
				if battle.get_enemy_location_pirate().in_attack_range(pirate):
					battle._my_pirates.append(pirate)
			for pirate in enemy_pirates:
				if battle.get_my_location_pirate().in_attack_range(pirate):
					battle._enemy_pirates.append(pirate)
			if not (len(battle.get_my_pirates()) > 0 and len(battle.get_enemy_pirates()) > 0):
				battles.remove(battle)
			else:
				turns_remaining_to_battle(battle)
		else:
			battles.remove(battle)
#ROUGHLY calculates the turns remaining to battle by check hp of pirates vs amount of enemy pirates and vice versa
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