import pandas as pd
import soccerdata as sd
import ScraperFC as Sfc
from understatapi import UnderstatClient
from team_maps import compatibilise_team
from year_map import convert_year_to_season, convert_season_to_year



pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)



def build_scrapers(season):

    return {
    'ws' : sd.WhoScored(leagues="ENG-Premier League", seasons=season),
    'us' : sd.Understat(leagues="ENG-Premier League", seasons=season),
    'mh' : sd.MatchHistory(leagues="ENG-Premier League", seasons=season),
    'ss' : sd.Sofascore(leagues="ENG-Premier League", seasons=season),
    'en' : sd.ESPN(leagues="ENG-Premier League", seasons=season),
    'ss_sfc' : Sfc.Sofascore()
    }

def get_match_history_df(mh_scraper, season: int) -> pd.DataFrame:
    if season in [2021, 2122]:
        df = pd.read_csv('https://www.football-data.co.uk/mmz4281/2122/E0.csv')
        if 'Div' in df.columns:
            df = df.rename(columns={'Div': 'league'})
        return df
    else:
        return mh_scraper.read_games()


#Return percentage difference. To prevent division by 0 error: If both nums are 0, return 0 as neither is better than the other. if only away_num is 0, deduce home_num is 100% better than away_num and if vice versa return -1.
def percentage_difference(home_num: float, away_num: float) -> float:
    if home_num == 0 and away_num == 0:
        return 0
    elif home_num == 0:
        return -1
    elif away_num == 0:
        return 1

    return (home_num - away_num) / away_num

def symmetric_difference(home_num: float, away_num: float) -> float:
    if home_num == 0 and away_num == 0: # Cover division by 0 errors
        return 0

    return (home_num - away_num) / (home_num + away_num)

def correct_odds_to_total_one(odds_list: list) -> list:

    if len(odds_list) == 0:
        raise IOError("Odds list cannot be empty in this function")

    common_denominator = 0

    for i in odds_list: #O(N) time complexity? (2N)
        common_denominator += i

    for i in range(len(odds_list)):
        odds_list[i] /= common_denominator

    return odds_list




'''
ESPNMatchLineup Class

A class to organise the lineup, position, and minutes played data for all players in a given match
'''

class ESPNMatchLineup:

    # lineup and subs include {player: [position, minutes]}
    def __init__(self, game: list, season, espn_scraper: sd.ESPN):
        self.espn_scraper = espn_scraper
        self.match_id = game[1]
        self.home_team = game[0].split(' ', 1)[1].split('-')[0]
        self.away_team = game[0].split(' ', 1)[1].split('-')[1]
        self.date = game[0].split(' ', 1)[0]
        self.season = season
        lineups_dataframe = espn_scraper.read_lineup(self.match_id)
        home_team_dataframe = lineups_dataframe[lineups_dataframe["is_home"]]
        away_team_dataframe = lineups_dataframe[lineups_dataframe["is_home"] == False]
        self.game = home_team_dataframe.index.get_level_values("game").values[0]
        self.home_lineup_dataframe = home_team_dataframe[home_team_dataframe["sub_in"] == "start"]
        self.home_sub_dataframe = home_team_dataframe[home_team_dataframe["sub_in"] != "start"]
        self.away_lineup_dataframe = away_team_dataframe[away_team_dataframe["sub_in"] == "start"]
        self.away_sub_dataframe = away_team_dataframe[away_team_dataframe["sub_in"] != "start"]

    def __repr__(self):
        return f'Match ID: {self.match_id}, Home Team: {self.home_team}, Away Team: {self.away_team}, Date: {self.date}'

    def get_match_id(self):
        return self.match_id

    def get_home_team(self):
        return self.home_team

    def get_away_team(self):
        return self.away_team

    def get_date(self):
        return self.date

    def get_match(self):
        return self.game

    def get_season(self):
        return self.season

    def get_home_lineup_dataframe(self) -> pd.DataFrame: #Lineups and sub dataframes include much data on each one.
        return self.home_lineup_dataframe

    def get_home_sub_dataframe(self) -> pd.DataFrame:
        return self.home_sub_dataframe

    def get_away_lineup_dataframe(self) -> pd.DataFrame:
        return self.away_lineup_dataframe

    def get_away_sub_dataframe(self) -> pd.DataFrame:
        return self.away_sub_dataframe

    def get_home_lineup_as_dict(self):
        home_player_position_dict = (self.home_lineup_dataframe.reset_index().set_index("player")["position"].to_dict())
        return home_player_position_dict

    def get_away_lineup_as_dict(self):
        away_player_position_dict = (self.away_lineup_dataframe.reset_index().set_index("player")["position"].to_dict())
        return away_player_position_dict

    def update_home_formation_times(self) -> list:
        cleaned_update_times = []

        home_uncleaned_update_times = self.home_sub_dataframe.loc[self.home_sub_dataframe["sub_in"].notna(), "sub_in"].astype(
            int).unique().tolist()

        for i in home_uncleaned_update_times:
            if i not in cleaned_update_times:
                cleaned_update_times.append(i)

        cleaned_update_times.sort()

        return cleaned_update_times

    def update_away_formation_times(self) -> list:
        cleaned_update_times = []

        away_uncleaned_update_times = self.away_sub_dataframe.loc[self.away_sub_dataframe["sub_in"].notna(), "sub_in"].astype(
            int).unique().tolist()

        for i in away_uncleaned_update_times:
            if i not in cleaned_update_times:
                cleaned_update_times.append(i)

        cleaned_update_times.sort()

        return cleaned_update_times

    '''
    get_formation method
    To get the home team, is_home = True
    To get the away team, is_home = False 
    '''

    def get_formation(self, is_home: bool) -> str:
        if is_home:
            position_list = self.home_lineup_dataframe.reset_index("player")["position"].tolist()
        else:
            position_list = self.away_lineup_dataframe.reset_index("player")["position"].tolist()

        position_list.remove("Goalkeeper")

        print(position_list)

        formation_list = [0, 0, 0, 0, 0]
        position_dictionary = {"Left Back": 0,
                               "Right Back": 0,
                               "Center Left Defender": 0,
                               "Center Right Defender": 0,
                               "Center Defender": 0,
                               "Sweeper": 0,
                               "Defensive Midfielder": 1,
                               "Center Defensive Midfielder": 1,
                               "Left Defensive Midfielder": 1,
                               "Right Defensive Midfielder": 1,
                               "Rear Center Midfielder": 1,
                               "Left Midfielder": 2,
                               "Right Midfielder": 2,
                               "Center Left Midfielder": 2,
                               "Center Right Midfielder": 2,
                               "Center Midfielder": 2,
                               "Midfielder": 2,
                               "Attacking Midfielder Left": 3,
                               "Attacking Midfielder Right": 3,
                               "Attacking Midfielder": 3,
                               "Forward": 4,
                               "Right Forward": 4,
                               "Left Forward": 4,
                               "Center Right Forward": 4,
                               "Center Left Forward": 4,
                               "Rear Center Forward": 4,
                               }

        for i in position_list:
            formation_row = position_dictionary[i]
            formation_list[formation_row] = formation_list[formation_row] + 1

        formation_string = ''

        for i, row in enumerate(formation_list):
            if row != 0:
                formation_string = formation_string + str(row)

                if i < 4:
                    formation_string = formation_string + '-'

        if is_home:
            formation_string = formation_string
        else:
            formation_string = formation_string

        return formation_string

    def get_home_lineup_shots(self):
        return self.home_lineup_dataframe.reset_index("player")["total_shots"].sum()

    def get_home_lineup_shots_on_target(self):
        return self.home_lineup_dataframe.reset_index("player")["shots_on_target"].sum()

    def get_home_sub_shots(self):
        return self.home_sub_dataframe.reset_index("player")["total_shots"].sum()

    def get_home_sub_shots_on_target(self):
        return self.home_sub_dataframe.reset_index("player")["shots_on_target"].sum()

    def get_away_lineup_shots(self):
        return self.away_lineup_dataframe.reset_index("player")["total_shots"].sum()

    def get_away_lineup_shots_on_target(self):
        return self.away_lineup_dataframe.reset_index("player")["shots_on_target"].sum()

    def get_away_sub_shots(self):
        return self.away_sub_dataframe.reset_index("player")["total_shots"].sum()

    def get_away_sub_shots_on_target(self):
        return self.away_sub_dataframe.reset_index("player")["shots_on_target"].sum()

    def  get_home_lineup_player_list(self):
        return self.home_lineup_dataframe.index.get_level_values("player").tolist()

    def  get_away_lineup_player_list(self):
        return self.away_lineup_dataframe.index.get_level_values("player").tolist()

    def  get_home_sub_player_list(self):
        return self.home_sub_dataframe.index.get_level_values("player").tolist()

    def  get_away_sub_player_list(self):
        return self.away_sub_dataframe.index.get_level_values("player").tolist()

    def get_home_lineup_shots_on_target_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["shots_on_target"] > 0]["shots_on_target"].groupby(level="player").sum().to_dict()

    def get_away_lineup_shots_on_target_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["shots_on_target"] > 0]["shots_on_target"].groupby(level="player").sum().to_dict()

    def get_home_sub_shots_on_target_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["shots_on_target"] > 0]["shots_on_target"].groupby(level="player").sum().to_dict()

    def get_away_sub_shots_on_target_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["shots_on_target"] > 0]["shots_on_target"].groupby(level="player").sum().to_dict()

    def get_home_lineup_shots_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["total_shots"] > 0]["total_shots"].groupby(level="player").sum().to_dict()

    def get_away_lineup_shots_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["total_shots"] > 0]["total_shots"].groupby(level="player").sum().to_dict()

    def get_home_sub_shots_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["total_shots"] > 0]["total_shots"].groupby(level="player").sum().to_dict()

    def get_away_sub_shots_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["total_shots"] > 0]["total_shots"].groupby(level="player").sum().to_dict()

    def get_home_lineup_offsides_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["offsides"] > 0]["offsides"].groupby(level="player").sum().to_dict()

    def get_away_lineup_offsides_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["offsides"] > 0]["offsides"].groupby(level="player").sum().to_dict()

    # Total Goals
    def get_home_lineup_total_goals_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["total_goals"] > 0]["total_goals"].groupby(level="player").sum().to_dict()

    def get_away_lineup_total_goals_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["total_goals"] > 0]["total_goals"].groupby(level="player").sum().to_dict()

    # Goal Assists
    def get_home_lineup_assists_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["goal_assists"] > 0]["goal_assists"].groupby(level="player").sum().to_dict()

    def get_away_lineup_assists_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["goal_assists"] > 0]["goal_assists"].groupby(level="player").sum().to_dict()

    # Shots Faced
    def get_home_lineup_shots_faced_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["shots_faced"] > 0]["shots_faced"].groupby(level="player").sum().to_dict()

    def get_away_lineup_shots_faced_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["shots_faced"] > 0]["shots_faced"].groupby(level="player").sum().to_dict()

    # Saves
    def get_home_lineup_saves_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["saves"] > 0]["saves"].groupby(level="player").sum().to_dict()

    def get_away_lineup_saves_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["saves"] > 0]["saves"].groupby(level="player").sum().to_dict()

    # Goals Conceded
    def get_home_lineup_goals_conceded_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["goals_conceded"] > 0]["goals_conceded"].groupby(level="player").sum().to_dict()

    def get_away_lineup_goals_conceded_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["goals_conceded"] > 0]["goals_conceded"].groupby(level="player").sum().to_dict()

    # Yellow Cards
    def get_home_lineup_yellow_cards_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["yellow_cards"] > 0]["yellow_cards"].groupby(level="player").sum().to_dict()

    def get_away_lineup_yellow_cards_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["yellow_cards"] > 0]["yellow_cards"].groupby(level="player").sum().to_dict()

    # Red Cards
    def get_home_lineup_red_cards_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["red_cards"] > 0]["red_cards"].groupby(level="player").sum().to_dict()

    def get_away_lineup_red_cards_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["red_cards"] > 0]["red_cards"].groupby(level="player").sum().to_dict()

    # Own Goals
    def get_home_lineup_own_goals_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["own_goals"] > 0]["own_goals"].groupby(level="player").sum().to_dict()

    def get_away_lineup_own_goals_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["own_goals"] > 0]["own_goals"].groupby(level="player").sum().to_dict()

    # Fouls Suffered
    def get_home_lineup_fouls_suffered_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["fouls_suffered"] > 0]["fouls_suffered"].groupby(level="player").sum().to_dict()

    def get_away_lineup_fouls_suffered_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["fouls_suffered"] > 0]["fouls_suffered"].groupby(level="player").sum().to_dict()

    # Fouls Committed
    def get_home_lineup_fouls_committed_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["fouls_committed"] > 0]["fouls_committed"].groupby(level="player").sum().to_dict()

    def get_away_lineup_fouls_committed_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["fouls_committed"] > 0]["fouls_committed"].groupby(level="player").sum().to_dict()

    # Appearances
    def get_home_lineup_appearances_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["appearances"] > 0]["appearances"].groupby(level="player").sum().to_dict()

    def get_away_lineup_appearances_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["appearances"] > 0]["appearances"].groupby(level="player").sum().to_dict()

    # Sub Out
    def get_home_sub_out_dict(self):
        df = self.home_lineup_dataframe.reset_index("player").set_index("player")
        return df[df["sub_out"] != "end"]["sub_out"].to_dict()

    def get_away_sub_out_dict(self):
        df = self.away_lineup_dataframe.reset_index("player").set_index("player")
        return df[df["sub_out"] != "end"]["sub_out"].to_dict()

    # Position
    def get_home_lineup_position_dict(self):
        return self.home_lineup_dataframe.reset_index("player").set_index("player")["position"].to_dict()

    def get_away_lineup_position_dict(self):
        return self.away_lineup_dataframe.reset_index("player").set_index("player")["position"].to_dict()

    '''
    SUBS
    '''

    def get_home_sub_offsides_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["offsides"] > 0]["offsides"].groupby(level="player").sum().to_dict()

    def get_away_sub_offsides_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["offsides"] > 0]["offsides"].groupby(level="player").sum().to_dict()

    # Total Goals
    def get_home_sub_total_goals_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["total_goals"] > 0]["total_goals"].groupby(level="player").sum().to_dict()

    def get_away_sub_total_goals_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["total_goals"] > 0]["total_goals"].groupby(level="player").sum().to_dict()

    # Goal Assists
    def get_home_sub_assists_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["goal_assists"] > 0]["goal_assists"].groupby(level="player").sum().to_dict()

    def get_away_sub_assists_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["goal_assists"] > 0]["goal_assists"].groupby(level="player").sum().to_dict()

    # Shots Faced
    def get_home_sub_shots_faced_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["shots_faced"] > 0]["shots_faced"].groupby(level="player").sum().to_dict()

    def get_away_sub_shots_faced_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["shots_faced"] > 0]["shots_faced"].groupby(level="player").sum().to_dict()

    # Saves
    def get_home_sub_saves_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["saves"] > 0]["saves"].groupby(level="player").sum().to_dict()

    def get_away_sub_saves_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["saves"] > 0]["saves"].groupby(level="player").sum().to_dict()

    # Goals Conceded
    def get_home_sub_goals_conceded_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["goals_conceded"] > 0]["goals_conceded"].groupby(level="player").sum().to_dict()

    def get_away_sub_goals_conceded_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["goals_conceded"] > 0]["goals_conceded"].groupby(level="player").sum().to_dict()

    # Yellow Cards
    def get_home_sub_yellow_cards_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["yellow_cards"] > 0]["yellow_cards"].groupby(level="player").sum().to_dict()

    def get_away_sub_yellow_cards_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["yellow_cards"] > 0]["yellow_cards"].groupby(level="player").sum().to_dict()

    # Sub Ins
    def get_home_sub_in_dict(self):
        df = self.home_sub_dataframe.reset_index()
        return df[df["sub_in"].notna()].set_index("player")["sub_in"].to_dict()

    def get_away_sub_in_dict(self):
        df = self.away_sub_dataframe.reset_index()
        return df[df["sub_in"].notna()].set_index("player")["sub_in"].to_dict()

    # Red Cards
    def get_home_sub_red_cards_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["red_cards"] > 0]["red_cards"].groupby(level="player").sum().to_dict()

    def get_away_sub_red_cards_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["red_cards"] > 0]["red_cards"].groupby(level="player").sum().to_dict()

    # Own Goals
    def get_home_sub_own_goals_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["own_goals"] > 0]["own_goals"].groupby(level="player").sum().to_dict()

    def get_away_sub_own_goals_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["own_goals"] > 0]["own_goals"].groupby(level="player").sum().to_dict()

    # Fouls Suffered
    def get_home_sub_fouls_suffered_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["fouls_suffered"] > 0]["fouls_suffered"].groupby(level="player").sum().to_dict()

    def get_away_sub_fouls_suffered_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["fouls_suffered"] > 0]["fouls_suffered"].groupby(level="player").sum().to_dict()

    # Fouls Committed
    def get_home_sub_fouls_committed_dict(self):
        return self.home_sub_dataframe[self.home_sub_dataframe["fouls_committed"] > 0]["fouls_committed"].groupby(level="player").sum().to_dict()

    def get_away_sub_fouls_committed_dict(self):
        return self.away_sub_dataframe[self.away_sub_dataframe["fouls_committed"] > 0]["fouls_committed"].groupby(level="player").sum().to_dict()

    # Appearances
    def get_home_sub_appearances_dict(self):
        return self.home_lineup_dataframe[self.home_lineup_dataframe["appearances"] > 0]["appearances"].groupby(level="player").sum().to_dict()

    def get_away_sub_appearances_dict(self):
        return self.away_lineup_dataframe[self.away_lineup_dataframe["appearances"] > 0]["appearances"].groupby(level="player").sum().to_dict()



    def get_matchhistory_name(self):

        split_game = self.game.split(' ', 1)
        teams_listed = split_game[1].split('-')
        mh_home_team = compatibilise_team(teams_listed[0], self.season, 'mh')
        mh_away_team = compatibilise_team(teams_listed[1], self.season, 'mh')
        mh_name = split_game[0] + ' ' + mh_home_team + '-' + mh_away_team

        return mh_name

    def get_matchhistory_row(self, match_history_df) -> pd.Series:
        mh_home_team = compatibilise_team(self.home_team, self.season, 'mh')
        mh_away_team = compatibilise_team(self.away_team, self.season, 'mh')

        if self.season in [2122]:
            row = match_history_df.loc[(match_history_df['HomeTeam'] == mh_home_team) & (match_history_df['AwayTeam'] == mh_away_team)].iloc[0]
        else:
            row = match_history_df.loc[(match_history_df['home_team'] == mh_home_team) & (match_history_df['away_team'] == mh_away_team)].iloc[0]

        if row.empty:
            print(f"No match found for '{mh_home_team}' vs '{mh_away_team}'")

        return row


    def get_understat_match_data(self):

        us_home_team = compatibilise_team(self.home_team, self.season, 'us')
        us_away_team = compatibilise_team(self.away_team, self.season, 'us')

        if not us_home_team or not us_away_team:
            raise KeyError("Team not found in team name conversion dictionary. Might be misspelled or missing")

        with UnderstatClient() as understat:

            #self.season is an int that is in the form 2122 for the 2021/2022 season, 2223 for the 2022/2023 season etc. This will need to be changed to scrape data from the 90s. Using dictionaries in year_map.py for understat

            understat_team_match_data = understat.team(us_home_team).get_match_data(season=convert_season_to_year(self.season))

            for i in understat_team_match_data:
                if i['a']['title'] == us_away_team:
                    return i

        raise IndexError("Away team could not be found for the given home team."
                         " Check the season to make sure the team are in the league that season,"
                         " or ensure the team was inputted correctly ")




    def get_scraper_fc_sofascore_match_data(self, ss_epl_schedule):

        us_home_team = compatibilise_team(self.home_team, self.season, 'ss')
        us_away_team = compatibilise_team(self.away_team, self.season, 'ss')

        if not us_home_team or not us_away_team:
            raise KeyError("Team not found in team name conversion dictionary. Might be misspelled or missing")

        ss_game = self.date + ' ' + us_home_team + '-' + us_away_team

        try:
            game_id = ss_epl_schedule.loc[ss_epl_schedule.index.get_level_values('game') == ss_game, 'game_id'].iat[0]
            game_id = str(game_id)
        except IndexError:
            print('Schedule:', ss_epl_schedule)
            print('Game:', ss_game)
            raise IndexError

        return game_id


class MatchHistoryFromESPN:

    def __init__(self, mh_match_data: pd.Series):
        self.row = mh_match_data

    '''
    get_result
    gets the result(outcome) of the game. Returned as a string. Either 'H', 'D' or 'A'
    '''

    def get_result(self) -> str:
        return self.row['FTR']

    '''
    get_score
    get's the home and away goals for the game. Returned as a list [home goals, away goals]
    '''

    def get_score(self) -> list[int]:
        return [self.row['FTHG'], self.row['FTAG']]

    '''
    get_betting_odds
    Return odds as average at closing time. Returns as a list of ints: home, draw, away
    '''

    def get_result_betting_odds(self) -> list[int]:
        return [self.row['AvgCH'], self.row['AvgCD'], self.row['AvgCA']]

    '''
    get_handicap
    get's the average handicap line at close. Returns handicap as an int
    '''

    def get_handicap(self) -> int:
        return self.row['AHCh']

    '''
    get_asian_handicap
    get's the average odds at close for the handicap line. The handicap line can be accessed through get_handicap(). Returned as a list of ints [home_ah, away_ah]
    '''

    def get_asian_handicap(self) -> list[int]:
        return [self.row['AvgCAHH'], self.row['AvgCAHA']]

    '''
    get_two_point_five_goal_odds
    get's the average odds at close for above and below 2.5 goals.
    '''

    def get_two_point_five_goal_odds(self) -> list[int]:
        return [self.row['Avg>2.5'], self.row['Avg<2.5']]


'''
Retrieve understat data about a given game from originally using ESPN data
'''
class UnderstatFromESPN:
    def __init__(self, understat_match_data):
        self.match_data = understat_match_data #List of dictionaries, to which some keys in that dictionary may contain another dictionary

    def get_home_xg(self):
        return self.match_data['xG']['h']

    def get_away_xg(self):
        return self.match_data['xG']['a']


'''
'Ball possession' 'Distance covered' 'Expected goals' 'Total shots' 'Goalkeeper saves' 'Number of sprints' 'Corner kicks' 'Fouls' 'Passes'
 'Tackles' 'Free kicks' 'Yellow cards' 'Shots on target' 'Hit woodwork' 'Shots off target' 'Blocked shots' 'Shots inside box' 'Shots outside box'
 'Through balls' 'Touches in penalty area' 'Fouled in final third' 'Offsides' 'Accurate passes' 'Throw-ins' 'Final third entries'
 'Final third phase' 'Long balls' 'Crosses' 'Duels' 'Dispossessed' 'Ground duels' 'Aerial duels' 'Dribbles' 'Tackles won' 'Total tackles'
 'Interceptions' 'Recoveries' 'Clearances' 'Total saves' 'Goals prevented' 'Big saves' 'High claims' 'Goal kicks'
'''

class SofascoreFromESPN:
    def __init__(self, game_id, ss_sfc_scraper):
        self.match_data = ss_sfc_scraper.scrape_team_match_stats(game_id)

    def get_home_data(self, period='ALL'): #'1ST' for 1st half, '2ND' for 2nd half
        data = self.match_data.loc[self.match_data['period'] == period]
        return data['key'].tolist(), data['homeValue'].tolist()

    def get_away_data(self, period='ALL'):
        data = self.match_data.loc[self.match_data['period'] == period]
        return data['key'].tolist(), data['awayValue'].tolist()


'''
Placeholder

A class to
'''

class FormationAnalyser:

    def __init__(self, matches: list[ESPNMatchLineup]):

        self.matches = matches

    '''
    This function will score the performance of the two teams in the match using certain statistics and record this through the formation matchup. (ex. 4-2-3-1 vs 4-3-3)
    
    This function compares the difference between the betting odds at close with the difference between certain statistics.
    
    So, if 75% of bets were for the home team to win, but in calculating the performance of the away team it was found that they performed 20% better than the home team, 
    the score would be -0.7. (- for the away team). Why this score? Well this is how the algorithm works. (Description needs an update because it has been simplified)
    
    An average performance difference is taken which will lie between 1 and -1, where 1 is in favour of the home team, and -1 is in favour of the away team.
    To put these stats into context, the betting odds were used to counter-weight the performance difference calculated above, as one team may simply have much better players than the other. 
    This is done by using the percentage difference between the outcomes in the betting odds.
    For a home win, it's the home odds - away odds and vice versa for an away win.
    For a draw, a difference is calculated for both home and away results by doing the draw odds - home odds/away odds
    The average performance difference - the odds percentage difference = final score. This score is then added to the home team   
    
    '''

if __name__ == '__main__':

    scrapers = build_scrapers(2425)

    en = scrapers['en']
    mh = scrapers['mh']
    ss = scrapers['ss']
    ss_sfc = scrapers['ss_sfc']

    # epl_schedule = ws.read_schedule()
    en_epl_schedule = en.read_schedule()
    ss_epl_schedule = ss.read_schedule()

    # print(en_epl_schedule.head())
    # en_lineup = en.read_lineup(704279)
    # print(en_lineup)

    games = en_epl_schedule.reset_index()[["game", "game_id"]].itertuples(index=False, name=None)
    games = list(games)

    espn_match_lineup_games = list(map(lambda x: ESPNMatchLineup(x, 2425, en), games))

    match = ESPNMatchLineup(games[0], 2425, en)
    ss_data = SofascoreFromESPN(match.get_scraper_fc_sofascore_match_data(ss_epl_schedule), ss_sfc)

    analyser = FormationAnalyser(espn_match_lineup_games)

    print(match.get_home_sub_dataframe())

