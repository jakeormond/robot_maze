'''
testing choices_class.py
'''

import choices_class as cc
import time

# initialize choices object
choices = cc.Choices()

# save a series of choices using a loop with a 1 sec pause between each choice
# first, create a list of start platforms
start_platforms = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# then a list of chosen platforms by adding 10 to each start platform
chosen_platforms = [x + 10 for x in start_platforms]
# then a list of unchosen platforms
unchosen_platforms = [x + 20 for x in start_platforms]

for i in range(10):
    # start a choice
    choices.start_choice(start_platforms[i])
    time.sleep(0.5)
    choices.register_choice(chosen_platforms[i], unchosen_platforms[i])
    time.sleep(0.5)
    
# save the choices to file
choices.save_choices('/media/jake/LaCie/robot_maze_workspace')