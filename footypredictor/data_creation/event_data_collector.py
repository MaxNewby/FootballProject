import ast
import time
from uvicorn.config import is_dir
import config
from GetFootballData.scraper_utilities.year_maps import season_to_starting_year, starting_year_to_season
from config import ROOT_DIR
import soccerdata as sd
import ScraperFC as sfc
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os
from ws_abbreviation_to_name_map.abbreviation_map import get_ws_abbreviation_to_name_map
from footypredictor.data_creation.event_data_collector_utilities.event_data_processing import EventDataProcessing
from match_event_datasets import qualifier_dictionary
from match_event_datasets.pitch_dimensions import get_pitch_dimensions
from match_event_datasets.qualifier_dictionary import get_qualifier, get_qualifier_dict_columns
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


class EventDataCollector:

    def __init__(self):

        self.event_data_processing = EventDataProcessing()

    def get_all_stat_columns(self, unique=True) -> list:
        """Flatten the value lists from all three mapping dicts into one list."""
        all_columns = self.event_data_processing.get_all_stat_columns()

        if unique:
            # dict.fromkeys drops duplicates but keeps first-seen order
            return list(dict.fromkeys(all_columns))
        return all_columns



    def save_who_scored_event_data(self, league_list:list, year_list: list):

        '''
        :param league_list: list of leagues that match event data will be scraped from.
        :param season_list: list of starting years of the seasons that match event data will be scraped from. (ex: [2024, 2025])
        '''

        for year in year_list:

            season = str(starting_year_to_season[year])

            count = 0

            if not is_dir(Path(f'{ROOT_DIR}/match_event_datasets')):
                os.mkdir(Path(f'{ROOT_DIR}/match_event_datasets'))

            for league in league_list:

                if not is_dir(Path(f'{ROOT_DIR}/match_event_datasets/{season}')):
                    os.mkdir(Path(f'{ROOT_DIR}/match_event_datasets/{season}'))

                if not is_dir(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}')):
                    os.mkdir(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}'))

                ws = sd.WhoScored(leagues=league, seasons=season)
                ws_schedule = ws.read_schedule()

                if not is_dir(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/fixtures')):
                    os.mkdir(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/fixtures'))

                if not is_dir(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/data')):
                    os.mkdir(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/data'))

                if not os.path.isfile(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/fixtures/schedule.parquet')):
                    schedule_data = pd.DataFrame(ws_schedule)
                    table = pa.Table.from_pandas(schedule_data)
                    pq.write_table(table, Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/fixtures/schedule.parquet'))

                #print(ws_schedule['game_id'])
                #print(ws_schedule.columns)

                print(ws_schedule['game_id'])

                for game in ws_schedule.itertuples():

                    game_id = game.game_id
                    print(game_id)

                    match_stats_df = ws.read_events(match_id=game_id)
                    count += 1
                    table = pa.Table.from_pandas(match_stats_df)
                    pq.write_table(table, f'{ROOT_DIR}/match_event_datasets/{season}/{league}/data/{game_id}.parquet')
                    print(f'{count}/380')

                    time.sleep(0.5)



    def load_who_scored_event_data(self, year: int, league: str, home_team: str, away_team: str, iteration=1) -> pd.DataFrame:

        '''

        :param year: the starting year of the season to find the game in (ex. 2025)
        :param league: the league to find the game in (ex. 'ENG-Premier League')
        :param home_team: the home team name
        :param away_team: the away team name
        :param iteration: Used if an identical home-away fixture appears more than once in the league.
         The iteration parameter can be used to pick between the nth iteration of the fixture in the given league/season.
         1 for the first meeting, 2 for the second meeting etc.
        :return: a pd.Dataframe object containing the event data for the chosen game. If a game can't be found, None is returned.
        '''

        #1. Get schedule.
        #2. Use the schedule's home and away teams to fetch the game_id. If multiple games are present in the df, use the iteration parameter.
        #3. Return game from data file using the found game_id

        season = starting_year_to_season[year]

        if not Path.is_dir(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}')):
            raise Exception('No match_event_datasets directory under ROOT_DIR')

        schedule_table = pq.read_table(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/fixtures/schedule.parquet'))
        schedule_dataframe = schedule_table.to_pandas()

        matches = schedule_dataframe.loc[(schedule_dataframe['home_team'] == home_team) & (schedule_dataframe['away_team'] == away_team)]
        if matches.empty:
            raise Exception('No matches found for the given home team against the away team in this league and season in the schedule')

        try:
            game_id = matches['game_id'].iloc[iteration-1] #Correct the user input to make it access the first element in the list
        except:
            raise Exception(f'No game_id found for iteration {iteration} of this fixture for this given league and season in the schedule')

        if not Path.is_file(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/data/{game_id}.parquet')):
            raise Exception(f'No dataframe .parquet file for this game in the data file for the given league and season. The game_id you were looking for is {game_id}')

        match_event_table = pq.read_table(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/data/{game_id}.parquet'))
        match_event_dataframe = match_event_table.to_pandas()

        return match_event_dataframe



    def get_formation_and_sub_change_data(self, season, league, game_id):

        formation_id_name_mappings = {
            '2': "4-4-2", '3': "4-1-2-1-2", '4': "4-3-3",
            '5': "4-5-1", '6': "4-4-1-1", '7': "4-1-4-1",
            '8': "4-2-3-1", '9': "4-3-2-1", '10': "5-3-2",
            '11': "5-4-1", '12': "3-5-2", '13': "3-4-3",
            '14': "3-1-3-1-2", '15': "4-2-2-2", '16': "3-5-1-1",
            '17': "3-4-2-1", '18': "3-4-1-2", '19': "3-1-4-2",
            '20': "3-4-1-2", '21': "4-1-3-2", '22': "4-2-4",
            '23': "4-3-1-2", '24': "3-2-4-1", '25': "3-3-3-1",
        }

        match_event_table = pq.read_table(Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/data/{game_id}.parquet'))
        match_event_dataframe = match_event_table.to_pandas()

        home_team = match_event_dataframe['team'].iloc[0]
        away_team = match_event_dataframe['team'].iloc[1]

        formation_and_sub_event_dataframe = match_event_dataframe[(match_event_dataframe['type'] == 'FormationSet') | (match_event_dataframe['type'] == 'FormationChange') | (match_event_dataframe['type'] == 'SubstitutionOn') | (match_event_dataframe['type'] == 'SubstitutionOff')]
        formation_event_dataframe = formation_and_sub_event_dataframe[(formation_and_sub_event_dataframe['type'] == 'FormationSet') | (formation_and_sub_event_dataframe['type'] == 'FormationChange')]
        sub_event_dataframe = formation_and_sub_event_dataframe[(formation_and_sub_event_dataframe['type'] == 'SubstitutionOn') | (formation_and_sub_event_dataframe['type'] == 'SubstitutionOff')]

        player_dict = (match_event_dataframe[['player_id', 'player']].dropna(subset=['player_id']).drop_duplicates('player_id').set_index('player_id')['player'].to_dict())  # player_id:player

        home_formation_change_list = {}
        away_formation_change_list = {}

        home_sub_change_list = {} #{'minute:second': (sub_off, sub_on)}
        away_sub_change_list = {}

        for row in formation_event_dataframe.itertuples():

            qualifiers = row.qualifiers
            minute = row.minute
            second = row.second

            qualifier_dict = {qualifier['type']['displayName']: qualifier['value'] for qualifier in qualifiers}

            formation_string = formation_id_name_mappings[qualifier_dict['TeamFormation']]
            player_list = [player_dict.get(float(player_id), None) for player_id in qualifier_dict['InvolvedPlayers'].split(',')]

            player_positions = self.get_positions_mappings_for_formations(player_list, formation_string)

            if row.team == home_team:
                home_formation_change_list.update({f'{int(minute)}:{int(second)}': player_positions})
            elif row.team == away_team:
                away_formation_change_list.update({f'{int(minute)}:{int(second)}': player_positions})

        unique_pairs_df = sub_event_dataframe[['minute', 'second']].dropna().drop_duplicates()
        sub_minutes = [(int(row.minute), int(row.second)) for row in unique_pairs_df.itertuples(index=False)]

        for min_sec_pair in sub_minutes:
            substitution_df = sub_event_dataframe.loc[(sub_event_dataframe['minute'] == min_sec_pair[0]) & (sub_event_dataframe['second'] == min_sec_pair[1])]
            player_off = substitution_df.loc[substitution_df['type'] == 'SubstitutionOff', 'player'].iloc[0]
            player_on = substitution_df.loc[substitution_df['type'] == 'SubstitutionOn', 'player'].iloc[0]
            team = substitution_df['team'].iloc[0]

            if team == home_team:
                home_sub_change_list.update({f'{min_sec_pair[0]}:{min_sec_pair[1]}': (player_off, player_on)})
            else:
                away_sub_change_list.update({f'{min_sec_pair[0]}:{min_sec_pair[1]}': (player_off, player_on)})


        return home_formation_change_list, home_sub_change_list, away_formation_change_list, away_sub_change_list




    def get_positions_mappings_for_formations(self, player_list, formation):

        formation_position_map = {
            "4-4-2": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'RCM', 5: 'RCB', 6: 'LCB', 7: 'RM', 8: 'LCM', 9: 'LST', 10: 'RST', 11: 'LM'},
            "4-1-2-1-2": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'CDM', 5: 'RCB', 6: 'LCB', 7: 'RCM', 8: 'CAM', 9: 'LST', 10: 'RST', 11: 'LCM'},
            "4-3-3": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'CM', 5: 'RCB', 6: 'LCB', 7: 'RCM', 8: 'LCM', 9: 'ST', 10: 'RW', 11: 'LW'},
            "4-5-1": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'RCM', 5: 'RCB', 6: 'LCB', 7: 'RM', 8: 'LCM', 9: 'ST', 10: 'CM', 11: 'LM'},
            "4-4-1-1": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'RCM', 5: 'RCB', 6: 'LCB', 7: 'RM', 8: 'LCM', 9: 'ST', 10: 'CAM', 11: 'LM'},
            "4-1-4-1": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'CDM', 5: 'RCB', 6: 'LCB', 7: 'RM', 8: 'CM', 9: 'ST', 10: 'CM', 11: 'LM'},
            "4-2-3-1": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'LDM', 5: 'RCB', 6: 'LCB', 7: 'RW', 8: 'RDM', 9: 'ST', 10: 'CAM', 11: 'LW'},
            "4-3-2-1": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'CM', 5: 'RCB', 6: 'LCB', 7: 'LCM', 8: 'RCM', 9: 'ST', 10: 'RAM', 11: 'LAM'},
            "5-3-2": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'RCM', 8: 'CM', 9: 'LST', 10: 'LCM', 11: 'RST'},
            "5-4-1": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'RM', 8: 'RCM', 9: 'ST', 10: 'LCM', 11: 'LM'},
            "3-5-2": {1: 'GK', 2: 'RWB', 3: 'LWB', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'RCM', 8: 'LCM', 9: 'RST', 10: 'LST', 11: 'CM'},
            "3-4-3": {1: 'GK', 2: 'RWB', 3: 'LWB', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'RCM', 8: 'LCM', 9: 'ST', 10: 'RW', 11: 'LW'},
            "3-1-3-1-2": {1: 'GK', 2: 'RCM', 3: 'LCM', 4: 'CDM', 5: 'LCB', 6: 'CCB', 7: 'RCB', 8: 'CM', 9: 'LST', 10: 'RST', 11: 'CAM'},  # estimated formation so likely inaccurate
            "4-2-2-2": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'RDM', 5: 'RCB', 6: 'LCB', 7: 'RAM', 8: 'LDM', 9: 'LST', 10: 'RST', 11: 'LAM'},
            "3-5-1-1": {1: 'GK', 2: 'RWB', 3: 'LWB', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'RCM', 8: 'LCM', 9: 'ST', 10: 'SS', 11: 'CM'},
            "3-4-2-1": {1: 'GK', 2: 'RWB', 3: 'LWB', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'LCM', 8: 'RCM', 9: 'ST', 10: 'LAM', 11: 'RAM'},
            "3-4-1-2": {1: 'GK', 2: 'RWB', 3: 'LWB', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'RCM', 8: 'LCM', 9: 'CAM', 10: 'RST', 11: 'LST'},
            "3-1-4-2": {1: 'GK', 2: 'RWB', 3: 'LWB', 4: 'CCB', 5: 'RCB', 6: 'LCB', 7: 'RCM', 8: 'CDM', 9: 'RST', 10: 'LST', 11: 'LCM'},
            "4-1-3-2": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'CDM', 5: 'RCB', 6: 'LCB', 7: 'RCM', 8: 'CM', 9: 'ST', 10: 'ST', 11: 'LCM'},
            "4-2-4": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'RCM', 5: 'RCB', 6: 'LCB', 7: 'RW', 8: 'LCM', 9: 'LST', 10: 'RST', 11: 'LW'},
            "4-3-1-2": {1: 'GK', 2: 'RB', 3: 'LB', 4: 'CM', 5: 'RCB', 6: 'LCB', 7: 'RCM', 8: 'CAM', 9: 'RST', 10: 'LST', 11: 'LCM'},
            "3-2-4-1": {1: 'GK', 2: 'RCM', 3: 'LCM', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'LAM', 8: 'RAM', 9: 'ST', 10: 'LW', 11: 'RW'},
            "3-3-3-1": {1: 'GK', 2: 'RCM', 3: 'LCM', 4: 'LCB', 5: 'CCB', 6: 'RCB', 7: 'CAM', 8: 'CM', 9: 'ST', 10: 'RW', 11: 'LW'},
        }

        lineup_dict = {}

        lineup_position_list = formation_position_map[formation]
        for index, player in enumerate(player_list[:11]):
            lineup_dict[player] = lineup_position_list[index+1]

        return lineup_dict


    def update_players_in_dataframe(self, dataframe, player_position_dict, minute, second, expanded_minute)->pd.DataFrame:

        for player, position in player_position_dict.items():
            new_row = {'player': player, 'position': position, 'start_minute': minute, 'start_second': second, 'expanded_start_minute': expanded_minute}

            if not ((dataframe['player'] == player) & (dataframe['position'] == position)).any():
                dataframe = pd.concat([dataframe, pd.DataFrame([new_row])], ignore_index=True)

        return dataframe


    def update_player_end_times(self, dataframe, player_dict, end_minute, end_second, expanded_end_minute)->pd.DataFrame:
        for player, position in player_dict.items():
            if player is None:
                player_mask = dataframe['player'].isna()
            else:
                player_mask = dataframe['player'] == player

            mask = (player_mask & (dataframe['position'] == position) & (dataframe['end_minute'].isna()))
            dataframe.loc[mask, 'end_minute'] = end_minute
            dataframe.loc[mask, 'end_second'] = end_second
            dataframe.loc[mask, 'expanded_end_minute'] = expanded_end_minute

        return dataframe

    def update_players_in_dataframe_from_pending_subs(self, dataframe, pending_subs, current_home_formation_dict, current_away_formation_dict, home_team) -> pd.DataFrame:

        for player, data_array in pending_subs.items():
            stale_position, minute, second, expanded_minute, team = data_array

            current_dict = current_home_formation_dict if team == home_team else current_away_formation_dict
            position = current_dict.get(player, stale_position)

            new_row = {'player': player, 'position': position, 'start_minute': minute, 'start_second': second, 'expanded_start_minute': expanded_minute}

            if not ((dataframe['player'] == player) & (dataframe['position'] == position)).any():
                dataframe = pd.concat([dataframe, pd.DataFrame([new_row])], ignore_index=True)

        return dataframe


    def is_formation_change_after_substitution(self, dataframe, sub_minute, team)->bool:

        mask = (
                (dataframe['type'] == 'FormationChange') &
                (dataframe['minute'] >= sub_minute) &
                (dataframe['minute'] <= sub_minute + 1)
        )
        if team is not None:
            mask &= (dataframe['team'] == team)

        return mask.any()


    def build_player_row_lookup(self, total_stat_df):

        player_intervals = {}

        for index, stat_row in total_stat_df.iterrows():
            player = stat_row['player']

            player_intervals.setdefault(player, []).append(
                (
                    stat_row['expanded_start_minute'] * 60 + stat_row['start_second'],
                    stat_row['expanded_end_minute'] * 60 + stat_row['end_second'],
                    index
                )
            )

        return player_intervals


    def append_match_event_pitch_regions(self, match_data_dataframe, league: str, home_team: str,) -> pd.DataFrame:
        '''
        :param match_data_dataframe: the dataframe containing all match events for the game.
        :param league: the league that the game takes place in.
        :param home_team: the home team in the game.
        :return: the match_data_dataframe with appended columns including new columns:
            'fifth' - returns the fifths that each event occurred in.
        '''

        x_pitch_length, y_pitch_width = get_pitch_dimensions(league, home_team)

        match_data_dataframe['vertical_fifth'] = pd.cut(match_data_dataframe['x'], bins=5, labels=['right_wing', 'inside_right', 'centre', 'inside_left', 'left_wing'])
        match_data_dataframe['horizontal_thirds'] = pd.cut(match_data_dataframe['y'], bins=3, labels=['defensive_third', 'midfield', 'final_third'])
        match_data_dataframe['is_in_six_yard_box'] = ((match_data_dataframe['x'] / 100) * x_pitch_length) <= 6 and (((match_data_dataframe['y'] / 100) * y_pitch_width) >= ((y_pitch_width / 2) + 10) or (((match_data_dataframe['y'] / 100) * y_pitch_width) >= ((y_pitch_width / 2) - 10)))
        match_data_dataframe['is_in_penalty_area'] = ((match_data_dataframe['x'] / 100) * x_pitch_length) <= 18 and (((match_data_dataframe['y'] / 100) * y_pitch_width) >= ((y_pitch_width / 2) + 22) or (((match_data_dataframe['y'] / 100) * y_pitch_width) >= ((y_pitch_width / 2) - 22))) and not match_data_dataframe['is_in_six_yard_box']
        #Is in six yard box does not count for being in the penalty area in here.

        return match_data_dataframe


    def append_match_event_distances(self, match_data_dataframe, league: str, home_team: str) -> pd.DataFrame:
        """
        :param match_data_dataframe: the dataframe containing all match events for the game.
        :param league: the league that the game was played in (Using given format. Ensure name is included in pitch_dimensions.py).
        :param home_team: the home team of the game. (First line in match_data_dataframe where 'type'== Start).
        :return: the match_data_dataframe with appended columns including new columns:
            * event_distance - The distance the ball has travelled in an event (if applicable).
            * x_distance - The distance the ball has moved vertically up or down the pitch (greater x value -> towards opponents goal).
            * y_distance - The distance the ball has moved horizontally across the pitch (greater y value -> towards left side of the pitch).
            * distance_to_centre_of_goal - The distance the ball is from the centre of the goal in the beginning of the event.
            * distance_to_left_post - The distance the ball is from the goal at the beginning of the event.
            * distance_to_right_post - The distance the ball is from the right post at the beginning of the event.
            * is_towards_goal - True if the ball has travelled in the direction of the centre of the goal.
        """

        x_pitch_length, y_pitch_width = get_pitch_dimensions(league, get_ws_abbreviation_to_name_map(league, home_team))

        match_data_dataframe['event_distance'] = np.sqrt(
            (((match_data_dataframe['end_x'] - match_data_dataframe['x']) / 100) * x_pitch_length) ** 2
            + (((match_data_dataframe['end_y'] - match_data_dataframe['y']) / 100) * y_pitch_width) ** 2
        )

        match_data_dataframe['x_distance'] = np.sqrt(
            ((match_data_dataframe['end_x'] - match_data_dataframe['x']) / 100) * x_pitch_length)

        match_data_dataframe['y_distance'] = np.sqrt(
            ((match_data_dataframe['end_y'] - match_data_dataframe['y']) / 100) * y_pitch_width)

        match_data_dataframe['distance_to_left_post'] = np.sqrt(
            (((100 - match_data_dataframe['x']) / 100) * x_pitch_length) ** 2
            + ((((50 - match_data_dataframe['y']) / 100) * y_pitch_width) + 4) ** 2
        )

        match_data_dataframe['distance_to_centre_of_goal'] = np.sqrt(
            (((100 - match_data_dataframe['x']) / 100) * x_pitch_length) ** 2
            + (((50 - match_data_dataframe['y']) / 100) * y_pitch_width) ** 2
        )

        match_data_dataframe['distance_to_right_post'] = np.sqrt(
            (((100 - match_data_dataframe['x']) / 100) * x_pitch_length) ** 2
            + ((((50 - match_data_dataframe['y']) / 100) * y_pitch_width) - 4) ** 2
        )

        match_data_dataframe['is_towards_goal'] = np.sqrt(
            (((100 - match_data_dataframe['end_x']) / 100) * x_pitch_length) ** 2
            + (((50 - match_data_dataframe['end_y']) / 100) * y_pitch_width) ** 2
        ) < match_data_dataframe['distance_to_centre_of_goal']

        ###

        #print(match_data_dataframe.loc[match_data_dataframe['type'].isin(['Pass', 'BlockedPass']), ['minute', 'second', 'distance_to_centre_of_goal', 'distance_to_left_post', 'distance_to_right_post', 'event_distance']])


        return match_data_dataframe


    def append_match_event_qualifier_rows(self, match_data_dataframe):

        qualifier_columns = get_qualifier_dict_columns()
        match_data_dataframe.loc[:, qualifier_columns] = False

        return match_data_dataframe



    def apply_match_event_qualifiers(self, match_data_dataframe, qualifier_column_positions, qualifiers, row_index):

        for q_dict in qualifiers:

            q_column_name = get_qualifier(q_dict['type']['value'])

            if q_column_name is not None:
                column_index = qualifier_column_positions[q_column_name]
                match_data_dataframe.iloc[row_index, column_index] = True



    def insert_column_data(self, match_data_dataframe, total_stat_df, league, home_team) -> pd.DataFrame:

        '''

        :param match_data_dataframe: pandas dataframe containing the data relating to the match events for a given game
        :param total_stat_df: pandas dataframe containing the player rows for stats from the match events to be added to.
        :param league: league that the given game takes place in. (Make sure it is in the correct format ex. (ENG-Premier League, ESP-La Liga))
        :param home_team: the name of the home team in that given game. (Used for pitch dimensions for example.) See pitch_dimensions.py for the dictionary containing names of included teams. Home team is the first line in the match_data_dataframe where 'type' == Start.
        :return: a pandas dataframe containing the data relating to the match events for a given game
        '''


        match_data_dataframe = self.append_match_event_distances(match_data_dataframe, league, home_team) # compute and add extra distance rows
        #match_data_dataframe = self.append_match_event_pitch_regions(match_data_dataframe, league, home_team)

        match_data_dataframe = self.append_match_event_qualifier_rows(match_data_dataframe) # append column names to match_event_dataframe
        qualifier_column_positions = {column: match_data_dataframe.columns.get_loc(column) for column in get_qualifier_dict_columns()} #get the position of each column in match_data_dataframe

        stat_columns = [c for c in total_stat_df.columns.tolist() if c not in ('player', 'position', 'start_minute', 'start_second', 'end_minute', 'end_second', 'expanded_start_minute', 'expanded_end_minute')]
        total_stat_df[stat_columns] = total_stat_df[stat_columns].fillna(0)

        # Add all stat columns with 0 as initialised values
        total_stat_df[self.event_data_processing.get_all_stat_columns()] = 0

        print(total_stat_df.columns.tolist())
        print(total_stat_df.columns[total_stat_df.columns.duplicated(keep=False)].tolist())

        #start_total_seconds = total_stat_df['expanded_start_minute'] * 60 + total_stat_df['start_second']
        #end_total_seconds = total_stat_df['expanded_end_minute'] * 60 + total_stat_df['end_second']
        match_data_dataframe['event_total_seconds'] = (match_data_dataframe['expanded_minute'] * 60 + match_data_dataframe['second'])

        player_row_lookup = self.build_player_row_lookup(total_stat_df)

        for row_index, row in enumerate(match_data_dataframe.itertuples()):

            # Update qualifier columns
            self.apply_match_event_qualifiers(match_data_dataframe, qualifier_column_positions, row.qualifiers, row_index)

            event_type = row.type
            outcome_type = row.outcome_type #Outcome type is if the event was successful or not.

            event_total_seconds = row.event_total_seconds

            row_index_to_update_in_tsdf = None #Find the row index in total_stat_df that needs updating
            matches = [stat_index for start_time, end_time, stat_index in player_row_lookup.get(row.player, ()) if start_time <= event_total_seconds <= end_time] #Go through all start and end times of the given player to find # If the event happens within the start and end time of a given player
            if matches:
                if len(matches) > 1 and event_type != 'FormationChange': #Formation Change is only really the only time that the same player will overlap in time with another stint, but this check allows easy modification of who any overlapping stats should be assigned to.
                    row_index_to_update_in_tsdf = matches[0]  # non-formation event on a boundary
                else:
                    row_index_to_update_in_tsdf = matches[-1]

            #Error if the index is not found

            #Get standard data for the given event type:

            columns_to_update = self.event_data_processing.get_standard_data(type, outcome_type)

            #Any extra data for the given event type can be listed here to be calculated:
            match event_type:
                case 'Pass':
                    event_distance = row.event_distance
                    columns_to_update += self.event_data_processing.get_pass_extra_data(outcome_type, event_distance)

                case 'MissedShots' | 'SavedShot':

                    '''
                    event_distance = row.event_distance
                    event_goal_mouth_y = row.goal_mouth_y
                    event_goal_mouth_z = row.goal_mouth_z
                    pitch_dimensions = get_pitch_dimensions(league, home_team)
                    if pitch_dimensions:
                        pitch_dimension_y = pitch_dimensions[1]
                    else:
                        pitch_dimension_y = 68
                    columns_to_update += self.event_data_processing.get_missed_or_saved_shot_extra_data(event_distance, event_goal_mouth_y, event_goal_mouth_z, pitch_dimension_y)
                    '''

                    pass

                case 'Goal':
                    pass
                case _:
                    pass

            if not columns_to_update: #Ensure a column actually needs updating after both gets, otherwise just continue.
                continue

            total_stat_df.loc[row_index_to_update_in_tsdf, columns_to_update] += 1 #Locate the row that needs updating, then increase the value by 1

        return total_stat_df




    def build_player_position_dataframe(self, season, league, game_id):

        '''
        Requires match event dataframe to be in correct file.
        :param season: the season that the game takes place in
        :param league: the league that the game takes place in
        :param game_id: the who_scored game_id of the game, used to select the correct .parquet file
        :return:
        '''

        match_event_table = pq.read_table(
            Path(f'{ROOT_DIR}/match_event_datasets/{season}/{league}/data/{game_id}.parquet'))
        match_event_dataframe = match_event_table.to_pandas()

        match_event_dataframe = match_event_dataframe[match_event_dataframe['period'] != 'PreMatch']

        home_team = match_event_dataframe['team'].iloc[0]
        away_team = match_event_dataframe['team'].iloc[1]

        home_formation_change_dict, home_sub_change_dict, away_formation_change_dict, away_sub_change_dict = self.get_formation_and_sub_change_data(
            season, league, game_id)

        current_home_formation_dict = home_formation_change_dict['0:0']
        current_away_formation_dict = away_formation_change_dict['0:0']
        combined_formation_dict = current_home_formation_dict | current_away_formation_dict

        print(match_event_dataframe[
                  (match_event_dataframe['minute'].isin([45, 84])) &
                  (match_event_dataframe['type'].isin(['SubstitutionOn', 'FormationChange']))
                  ][['minute', 'second', 'type', 'team', 'player']])

        columns = [
            'player', 'position', 'start_minute', 'start_second', 'end_minute', 'end_second',
            'expanded_start_minute', 'expanded_end_minute', 'goals', 'attempted_passes',
            'completed_passes', 'poss_keeping_touches', 'miscontrolled_touches', 'ball_recoveries',
            'missed_shots', 'chances_missed', 'post_shots', 'clearances', 'aerials',
            'successful_aerials', 'dispossessed', 'attempted_tackles', 'successful_tackles',
            'balls_shielded_out', 'shielded_from_ball', 'good_skills', 'take_ons',
            'successful_take_ons', 'challenges', 'successful_challenges','blocked_passes',
            'saved_shots', 'saves', 'corners_won', 'corners_lost', 'fouls_won',
            'fouls_lost', 'offsides_given', 'offside_passes', 'offsides_provoked',
            'penalties_faced', 'penalties_saved', 'keeper_pickups', 'keeper_sweepers',
            'keeper_smothers', 'interceptions', 'claims', 'punches', 'errors', 'yellow_cards',
            'second_yellow_cards', 'red_cards', 'sub_ons', 'sub_offs',
        ]
        columns = ['player', 'position', 'start_minute', 'start_second', 'end_minute', 'end_second', 'expanded_start_minute', 'expanded_end_minute']

        #Columns to be created once the columns above have been populated:

        total_match_df = pd.DataFrame(
            [{'player': player, 'position': position, 'start_minute': 0, 'start_second': 0, 'expanded_start_minute': 0} for player, position in
             combined_formation_dict.items()],
            columns=columns
        )

        pending_subs = {}

        for row in match_event_dataframe.itertuples():

            if row.type == 'FormationChange':
                minute = row.minute
                second = row.second
                expanded_minute = row.expanded_minute

                if row.team == home_team:
                    new_home_formation_dict = home_formation_change_dict[f'{int(minute)}:{int(second)}']
                    old_home_formation_dict = current_home_formation_dict

                    changed_players_old = {
                        p: old_home_formation_dict[p]
                        for p in old_home_formation_dict
                        if p in new_home_formation_dict and new_home_formation_dict[p] != old_home_formation_dict[p]
                    }

                    total_match_df = self.update_player_end_times(total_match_df, changed_players_old, minute, second, expanded_minute)
                    current_home_formation_dict = new_home_formation_dict

                    if pending_subs:
                        total_match_df = self.update_players_in_dataframe_from_pending_subs(total_match_df, pending_subs, current_home_formation_dict, current_away_formation_dict, home_team)
                        pending_subs = {}

                    # Rows to (re)open: players whose position changed, PLUS players who are new to the formation entirely (e.g. the vacated 'None' slot)
                    rows_to_open = {
                        p: new_pos for p, new_pos in new_home_formation_dict.items()
                        if p not in old_home_formation_dict or old_home_formation_dict.get(p) != new_pos
                    }

                    total_match_df = self.update_players_in_dataframe(total_match_df, rows_to_open, minute, second, expanded_minute)

                elif row.team == away_team:
                    new_away_formation_dict = away_formation_change_dict[f'{int(minute)}:{int(second)}']
                    old_away_formation_dict = current_away_formation_dict

                    changed_players_old = {
                        p: old_away_formation_dict[p]
                        for p in old_away_formation_dict
                        if p in new_away_formation_dict and new_away_formation_dict[p] != old_away_formation_dict[p]
                    }

                    total_match_df = self.update_player_end_times(total_match_df, changed_players_old, minute, second, expanded_minute)
                    current_away_formation_dict = new_away_formation_dict

                    if pending_subs:
                        total_match_df = self.update_players_in_dataframe_from_pending_subs(total_match_df, pending_subs, current_home_formation_dict, current_away_formation_dict, home_team)
                        pending_subs = {}

                    # Rows to (re)open: players whose position changed, PLUS players who are new to the formation entirely (e.g. the vacated 'None' slot)
                    rows_to_open = {
                        p: new_pos for p, new_pos in new_away_formation_dict.items()
                        if p not in old_away_formation_dict or old_away_formation_dict.get(p) != new_pos
                    }

                    total_match_df = self.update_players_in_dataframe(total_match_df, rows_to_open, minute, second, expanded_minute)

            elif row.type == 'SubstitutionOn':
                minute = row.minute
                second = row.second
                team = row.team
                player = row.player
                expanded_minute = row.expanded_minute

                if team == home_team:
                    sub = home_sub_change_dict[f'{int(minute)}:{int(second)}']
                    player_off = sub[0]
                    player_off_position = current_home_formation_dict[player_off]

                    current_home_formation_dict[sub[1]] = current_home_formation_dict.pop(sub[0])
                    position = current_home_formation_dict[player]

                    total_match_df = self.update_player_end_times(total_match_df, {player_off: player_off_position}, minute, second, expanded_minute)

                    if self.is_formation_change_after_substitution(match_event_dataframe, minute, home_team):
                        pending_subs.update({player: (position, minute, second, expanded_minute, home_team)})
                    else:
                        total_match_df = self.update_players_in_dataframe(total_match_df, {player: position}, minute, second, expanded_minute)

                elif team == away_team:
                    sub = away_sub_change_dict[f'{int(minute)}:{int(second)}']
                    player_off = sub[0]
                    player_off_position = current_away_formation_dict[player_off]

                    current_away_formation_dict[sub[1]] = current_away_formation_dict.pop(sub[0])
                    position = current_away_formation_dict[player]

                    total_match_df = self.update_player_end_times(total_match_df, {player_off: player_off_position}, minute, second, expanded_minute)

                    if self.is_formation_change_after_substitution(match_event_dataframe, minute, away_team):
                        pending_subs.update({player: (position, minute, second, expanded_minute, away_team)})
                    else:
                        total_match_df = self.update_players_in_dataframe(total_match_df, {player: position}, minute, second, expanded_minute)

            elif row.type == 'End' and row.period == 'SecondHalf':
                minute = row.minute
                second = row.second
                expanded_minute = row.expanded_minute

                if pending_subs:
                    total_match_df = self.update_players_in_dataframe_from_pending_subs(total_match_df, pending_subs, current_home_formation_dict, current_away_formation_dict, home_team)
                    pending_subs = {}

                total_match_df = self.update_player_end_times(total_match_df, current_home_formation_dict, minute, second, expanded_minute)
                total_match_df = self.update_player_end_times(total_match_df, current_away_formation_dict, minute, second, expanded_minute)

            elif row.type == 'Card' and row.card_type in ('Red', 'SecondYellow'):
                player = row.player
                team = row.team
                minute = row.minute
                second = row.second
                expanded_minute = row.expanded_minute

                current_dict = current_home_formation_dict if team == home_team else current_away_formation_dict
                if player in current_dict:
                    position = current_dict[player]
                    total_match_df = self.update_player_end_times(total_match_df, {player: position}, minute, second, expanded_minute)
                    current_dict.pop(player, None)

            else:
                pass


        total_match_df = self.insert_column_data(match_event_dataframe, total_match_df, league, home_team) #Main method to insert all data into the dataframe.

        print(match_event_dataframe[:10])

        return total_match_df
























#for file in os.listdir(f'{ROOT_DIR}/match_event_datasets/2526/ITA-Serie A/data'):
    #game_id = file.split('.')[0]

    #b = get_formation_change_data(2526, 'ITA-Serie A', game_id=game_id)

#save_who_scored_event_data(['FRA-Ligue 1', 'GER-Bundesliga'], [2025])
#a = load_who_scored_event_data(2025, 'ESP-La Liga', 'Real Madrid', 'Elche')
'''
edc = EventDataCollector()

a, b, c, d = edc.get_formation_and_sub_change_data(2526, 'ESP-La Liga', '1913892') #1913882
print('a', a)
print('b', b)
print('c', c)
print('d', d)

print(edc.build_player_position_dataframe(2526, 'ENG-Premier League', '1903234'))
'''