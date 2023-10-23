'''
Define the choices class to hold the choices offered to the animal as
well as the its decisions. At the end of each trial, the choice history 
will be saved to file. 
'''

import pandas as pd
import datetime as dt
import os

# choices definition
class Choices:
    def __init__(self, directory=None, goal=None):
        # save the current time
        curr_time = dt.datetime.now()
        formatted_time = curr_time.strftime("%Y-%m-%d_%H.%M.%S")
        self.name = formatted_time

        # initialize self.data as an empty dataframe with columns for 
        # start time, choice time, starting position, chosen position, and 
        # unchosen position
        self.data = None

        # if directory is not None, load the previous choices
        if directory is not None:
            self.data = Choices.load_previous_choices(directory, goal)

        if self.data is None:
             self.data = pd.DataFrame(columns=['start_time', 'choice_time', \
                            'start_pos', 'chosen_pos', 'unchosen_pos', \
                            'crop_x', 'crop_y', 'crop_width', 'crop_height'])
        
        # initialize number of choices to 0
        self.num_choices = 0

        self.initial_crop_params = {}

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

    def save_crop_params(self, crop_params):
        self.data.loc[self.num_choices, 'crop_x'] = crop_params[0]
        self.data.loc[self.num_choices, 'crop_y'] = crop_params[1]
        self.data.loc[self.num_choices, 'crop_width'] = crop_params[2]
        self.data.loc[self.num_choices, 'crop_height'] = crop_params[3]

    def save_initial_crop_params(self, crop_params):
        self.initial_crop_params['crop_x'] = crop_params[0]
        self.initial_crop_params['crop_y'] = crop_params[1]
        self.initial_crop_params['crop_width'] = crop_params[2]
        self.initial_crop_params['crop_height'] = crop_params[3]

    @staticmethod
    def load_previous_choices(data_dir, goal):
        # create a list of all csv files in the data directory
        csv_files = [f for f in os.listdir(data_dir) if f.startswith('20') and f.endswith('.csv')]

        

        # if there are no csv files, return None
        if len(csv_files) == 0:
            return None
        
        # read each csv file to determine if it was towards the same goal
        csv_dfs = []
        for csv_file in csv_files:
            df = pd.read_csv(f'{data_dir}/{csv_file}')
            if df['chosen_pos'].iloc[-1] == goal:
                csv_dfs.append(df)
        
        if len(csv_dfs) == 0:
            return None

        return pd.concat(csv_dfs, ignore_index=True)                
            
        # otherwise, load the csv files into a list of dataframes and concatenate them
        # else:
        #    csv_dfs = [pd.read_csv(f'{data_dir}/{csv_file}') for csv_file in csv_files]
        #    return pd.concat(csv_dfs, ignore_index=True)
        
    
if __name__ == '__main__':
    # TESTING    
    from time import sleep
    choices = Choices()
    sleep(1)

    choices.start_choice(91)
    sleep(1)
    choices.register_choice(81, 101)

    sleep(1)   
    choices.start_choice(101)
    choices.register_choice(111, 110)

    sleep(1)   
    choices.start_choice(110)
    choices.register_choice(101, 119)

    sleep(1)   
    choices.start_choice(101)
    choices.register_choice(91, 92)

    sleep(1)   
    choices.start_choice(91)
    choices.register_choice(101, 82)

    sleep(1)   
    choices.start_choice(101)
    choices.register_choice(111, 110)

    sleep(1)
