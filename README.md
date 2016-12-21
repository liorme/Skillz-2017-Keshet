[my_city(row,col),enemy_city(row,col),islands[(id,row,col,owner)],my_pirates[(id,row,col,health)],enemy_pirates[(id,row,col,health)] 
my_drones[(id,row,col)],enemy_drones[(id,row,col)]]
gen = generation, a list of of moves
move = a dictionary of pirates and drones moves ("p" and "d")
"p" and "d" = a list of dictionaries each containing row and col ("r" and "c" )
create_first_gen:
    m = move that is now created
prm:
    creating a random pirate move
drm:
    creating a random drone move
