'''
Define the choices class to hold the choices offered to the animal as
well as the its decisions. At the end of each trial, the choice history 
will be saved to file. 
'''

import pandas as pd
import numpy as np
import datetime as dt

# choices definition
class Choices:
    def __init__(self):
        # save the current time
        curr_time = dt.datetime.now()
        formatted_time = curr_time.strftime("%Y-%m-%d_%H.%M.%S")
        self.name = f'choices_{formatted_time}'

        # initialize self.data as an empty dataframe with columns for 
        # start time, choice time, starting position, chosen position, and 
        # unchosen position
        self.data = pd.DataFrame(columns=['start_time', 'choice_time', \
                            'start_pos', 'chosen_pos', 'unchosen_pos', \
                            'crop_x', 'crop_y', 'crop_width', 'crop_height'])
        
        # initialize number of choices to 0
        self.num_choices = 0

    def start_choice(self, start_pos):
        # increment number of choices
        self.num_choices += 1
        # save the start time to row 'num_choices' in column 'start_time'
        curr_time = dt.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.data.loc[self.num_choices, 'start_time'] = curr_time
        # save the start position to row 'num_choices' in column 'start_pos'
        self.data.loc[self.num_choices, 'start_pos'] = start_pos

    def register_choice(self, chosen_pos, unchosen_pos):
        # save the choice time to row 'num_choices' in column 'choice_time'
        curr_time = dt.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.data.loc[self.num_choices, 'choice_time'] = curr_time
        # save the chosen position to row 'num_choices' in column 'chosen_pos'
        self.data.loc[self.num_choices, 'chosen_pos'] = chosen_pos
        # save the unchosen position to row 'num_choices' in column 'unchosen_pos'
        self.data.loc[self.num_choices, 'unchosen_pos'] = unchosen_pos

    def save_choices(self, data_dir):
        # save the choice history to file
        self.data.to_csv(f'{data_dir}/{self.name}.csv', index=False)
        
    

