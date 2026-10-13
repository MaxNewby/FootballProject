import os
import pandas as pd
import pyarrow.parquet as pq
from numpy.ma.core import identity

from config import ROOT_DIR
from footypredictor.data_creation.year_map import convert_season_to_year

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

class PlayerDataFetcher:

    def _player_data_per_90(self, dataframe):

        if dataframe.empty:
            return pd.DataFrame()

        column_dict = {'accurateChippedPasses': 'accurateChippedPasses_p90',
                       'accurateCrosses': 'accurateCrosses_p90',
                       'accurateFinalThirdPasses': 'accurateFinalThirdPasses_p90',
                       'accurateLongBalls': 'accurateLongBalls_p90',
                       'accurateOppositionHalfPasses': 'accurateOppositionHalfPasses_p90',
                       'accurateOwnHalfPasses': 'accurateOwnHalfPasses_p90',
                       'accuratePasses': 'accuratePasses_p90',
                       'aerialDuelsWon': 'aerialDuelsWon_90',
                       'aerialLost': 'aerialLost_90',
                       'assists': 'assists_p90',
                       'ballRecovery': 'ballRecovery_p90',
                       'bigChancesCreated': 'bigChancesCreated_p90',
                       'bigChancesMissed': 'bigChancesMissed_p90',
                       'blockedShots': 'blockedShots_p90',
                       'clearances': 'clearances_p90',
                       'crossesNotClaimed': 'crossesNotClaimed_p90',
                       'directRedCards': 'directRedCards_p90',
                       'dispossessed': 'dispossessed_p90',
                       'dribbledPast': 'dribbledPast_p90',
                       'duelLost': 'duelLost_p90',
                       'errorLeadToGoal': 'errorLeadToGoal_p90',
                       'errorLeadToShot': 'errorLeadToShot_p90',
                       'expectedAssists': 'expectedAssists_p90',
                       'expectedGoals': 'expectedGoals_p90',
                       'fouls': 'fouls_p90',
                       'freeKickGoal': 'freeKickGoal_p90',
                       'goalKicks': 'goalKicks_p90',
                       'goals': 'goals_p90',
                       'goalsAssistsSum': 'goalsAssistsSum_p90',
                       'goalsConceded': 'goalsConceded_p90',
                       'goalsConcededInsideTheBox': 'goalsConcededInsideTheBox_p90',
                       'goalsConcededOutsideTheBox': 'goalsConcededOutsideTheBox_p90',
                       'goalsFromInsideTheBox': 'goalsFromInsideTheBox_p90',
                       'goalsFromOutsideTheBox': 'goalsFromOutsideTheBox_p90',
                       'goalsPrevented': 'goalsPrevented_p90',
                       'groundDuelsWon': 'groundDuelsWon_p90',
                       'headedGoals': 'headedGoals_p90',
                       'highClaims': 'highClaims_p90',
                       'hitWoodwork': 'hitWoodwork_p90',
                       'inaccuratePasses': 'inaccuratePasses_p90',
                       'interceptions': 'interceptions_p90',
                       'keyPasses': 'keyPasses_p90',
                       'leftFootGoals': 'leftFootGoals_p90',
                       'offsides': 'offsides_p90',
                       'outfielderBlocks': 'outfielderBlocks_p90',
                       'ownGoals': 'ownGoals_p90',
                       'passToAssist': 'passToAssist_p90',
                       'penaltiesTaken': 'penaltiesTaken_p90',
                       'penaltyConceded': 'penaltyConceded_p90',
                       'penaltyFaced': 'penaltyFaced_p90',
                       'penaltyGoals': 'penaltyGoals_p90',
                       'penaltySave': 'penaltySave_p90',
                       'penaltyWon': 'penaltyWon_p90',
                       'possessionLost': 'possessionLost_p90',
                       'possessionWonAttThird': 'possessionWonAttThird_p90',
                       'punches': 'punches_p90',
                       'redCards': 'redCards_p90',
                       'rightFootGoals': 'rightFootGoals_p90',
                       'runsOut': 'runsOut_p90',
                       'savedShotsFromInsideTheBox': 'savedShotsFromInsideTheBox_p90',
                       'savedShotsFromOutsideTheBox': 'savedShotsFromOutsideTheBox_p90',
                       'saves': 'saves_p90',
                       'savesCaught': 'savesCaught_p90',
                       'savesParried': 'savesParried_p90',
                       'shotFromSetPiece': 'shotFromSetPiece_p90',
                       'shotsFromInsideTheBox': 'shotsFromInsideTheBox_p90',
                       'shotsFromOutsideTheBox': 'shotsFromOutsideTheBox_p90',
                       'shotsOffTarget': 'shotsOffTarget_p90',
                       'shotsOnTarget': 'shotsOnTarget_p90',
                       'successfulDribbles': 'successfulDribbles_p90',
                       'successfulRunsOut': 'successfulRunsOut_p90',
                       'tackles': 'tackles_p90',
                       'tacklesWon': 'tacklesWon_p90',
                       'totalAttemptAssist': 'totalAttemptAssist_p90',
                       'totalChippedPasses': 'totalChippedPasses_p90',
                       'totalContest': 'totalContest_p90',
                       'totalCross': 'totalCross_p90',
                       'totalDuelsWon': 'totalDuelsWon_p90',
                       'totalLongBalls': 'totalLongBalls_p90',
                       'totalOppositionHalfPasses': 'totalOppositionHalfPasses_p90',
                       'totalOwnHalfPasses': 'totalOwnHalfPasses_p90',
                       'totalPasses': 'totalPasses_p90',
                       'totalShots': 'totalShots_p90',
                       'touches': 'touches_p90',
                       'wasFouled': 'wasFouled_p90',
                       'yellowCards': 'yellowCards_p90',
                       'yellowRedCards': 'yellowRedCards_p90',
                       }

        dataframe.rename(columns=column_dict, inplace=True)

        for column in column_dict.values():
            dataframe[column] = dataframe[column] / (dataframe['minutesPlayed'] / 90)

        dataframe.drop([
            'accurateCrossesPercentage',
            'accurateLongBallsPercentage',
            'accuratePassesPercentage',
            'aerialDuelsWonPercentage',
            'appearances',
            'attemptPenaltyMiss',
            'attemptPenaltyPost',
            'attemptPenaltyTarget',
            'cleanSheet',
            'countRating',
            'goalConversionPercentage',
            'groundDuelsWonPercentage',
            'matchesStarted',
            'minutesPlayed',
            'penaltyConversion',
            'rating',
            'scoringFrequency',
            'setPieceConversion',
            'successfulDribblesPercentage',
            'tacklesWonPercentage',
            'totalDuelsWonPercentage',
            'totalRating',
            'totwAppearances'
        ], axis=1, inplace=True)

        return dataframe

    def _player_data_min_max(self, dataframe, p90_dataframe, min_dict, max_dict):

        if min_dict is None:
            min_dict = {}
        if max_dict is None:
            max_dict = {}

        #Min Values

        for column, min_value in min_dict.items():

            if column in dataframe.columns.tolist():
                dataframe = dataframe[dataframe[column] >= min_value]
                dataframe_players = dataframe['player'].tolist()
                p90_dataframe = p90_dataframe[p90_dataframe['player'].isin(dataframe_players)]

            elif column in p90_dataframe.columns.tolist():

                p90_dataframe = p90_dataframe[p90_dataframe[column] >= min_value]
                p90_dataframe_players = p90_dataframe['player'].tolist()
                dataframe = dataframe[dataframe['player'].isin(p90_dataframe_players)]

            else:
                pass

        #Max Values

        for column, max_value in max_dict.items():

            if column in dataframe.columns.tolist():
                dataframe = dataframe[dataframe[column] <= max_value]
                dataframe_players = dataframe['player'].tolist()
                p90_dataframe = p90_dataframe[p90_dataframe['player'].isin(dataframe_players)]

            elif column in p90_dataframe.columns.tolist():

                p90_dataframe = p90_dataframe[p90_dataframe[column] <= max_value]
                p90_dataframe_players = p90_dataframe['player'].tolist()
                dataframe = dataframe[dataframe['player'].isin(p90_dataframe_players)]

            else:
                pass

        return dataframe, p90_dataframe



    def get_player_percentiles(self, player_name: str, season=None, league=None, per_90=True, by_position=False, by_nation=False, by_club=False, include_europe=False, additional_leagues=None, min_stat_dict=None, max_stat_dict=None)->pd.DataFrame:
        '''
        This method returns the percentile data for a given player according to the chosen parameters.
        The player will be compared to every player in the leagues they have appeared in for each given season.

        :param player_name: The name of the player to get the percentile data for.
        :param season: The season that the percentile data is for. Provided as a string in the format '2526' Defaults to the most recent season.
        :param league: The league to get the percentile data for from a player. Defaults to the league with most minutes played in.
        :param per_90: The percentile data that is returned will rank the data based on their output per 90 minutes. Can be set to False to get raw data
        :param by_position: Can be set to True to ensure players are compared to only those of the same position
        :param by_nation: Can be set to True to ensure players are compared to only those of the same nationality
        :param by_club: Can be set to True to ensure players are compared to only those at the same club
        :param include_europe: Can be set to True to include the stats of european competitions for the season
        :param additional_leagues: Accepts a list of other leagues to include in the comparison
        :param min_stat_dict: A dictionary containing {stat: min_value} pairs, providing the minimum values player's must have in a certain column to be used in the comparison. Ex: {'goals': 5, ...}
        :param max_stat_dict: A dictionary containing {stat: min_value} pairs, providing the maximum values player's must have in a certain column to be used in the comparison. Ex: {'minutesPlayed': 3000, ...}

        :return: A pd.Dataframe containing a single row with the player's percentile data for that given league and season. An empty pd.Dataframe instance will be returned if the player is not in the dataset.
        '''


        seasons = [season for season in os.listdir(f'{ROOT_DIR}/player_data_analysis/player_overview')] #Change seasons from strings for directories to a list of ints
        current_season = str(max(seasons))
        if season is None: #Ensure the season list gets set to just the most recent season if None
            season = current_season

        #Attain all leagues a player has played in each season from the available data

        if league is None:
            most_minutes = 0
            for dir_league in os.listdir(f'{ROOT_DIR}/player_data_analysis/player_data/{season}'):
                table = pq.read_table(f'{ROOT_DIR}/player_data_analysis/player_data/{season}/{league}')
                player_data_dataframe = table.to_pandas()
                if player_data_dataframe['player_name'].contains(player_name):
                    current_minutes = player_data_dataframe.loc[player_data_dataframe['player_name'] == player_name, 'minutesPlayed'].iloc[0]
                    if current_minutes > most_minutes:
                        league = dir_league[:-8] #Slice off the .parquet
                        most_minutes = current_minutes #Update most minutes

            if most_minutes == 0:
                return pd.DataFrame()




        table = pq.read_table(f'{ROOT_DIR}/player_data_analysis/player_data/{season}/{league}.parquet')
        player_data_dataframe = table.to_pandas()
        table = pq.read_table(f'{ROOT_DIR}/player_data_analysis/player_overview/{current_season}/{league}.parquet')
        player_overview_dataframe = table.to_pandas()

        player_row = player_overview_dataframe.loc[player_overview_dataframe['player_name'] == player_name]

        if additional_leagues:
            for added_league in additional_leagues:
                table = pq.read_table(f'{ROOT_DIR}/player_data_analysis/player_data/{season}/{added_league}.parquet')
                additional_player_data_df = table.to_pandas()
                player_data_dataframe = pd.concat([player_data_dataframe, additional_player_data_df], ignore_index=True)

        if by_position:
            print(player_row)
            position = player_row['position'].values[0]
            player_overview_dataframe = player_overview_dataframe.loc[player_overview_dataframe['position'] == position]
            player_overview_dataframe_players = player_overview_dataframe['player_name'].values.tolist()
            player_data_dataframe = player_data_dataframe[player_data_dataframe['player'].isin(player_overview_dataframe_players)]

        if by_nation:
            nation = player_row['nationality'].values[0]
            player_overview_dataframe = player_overview_dataframe.loc[player_overview_dataframe['nationality'] == nation]
            player_overview_dataframe_players = player_overview_dataframe['player_name'].values.tolist()
            player_data_dataframe = player_data_dataframe[player_data_dataframe['player'].isin(player_overview_dataframe_players)]

        if by_club:
            team = player_row['team'].values[0]
            player_overview_dataframe = player_overview_dataframe.loc[player_overview_dataframe['team'] == team]
            player_overview_dataframe_players = player_overview_dataframe['player_name'].values.tolist()
            player_data_dataframe = player_data_dataframe[player_data_dataframe['player'].isin(player_overview_dataframe_players)]

        if include_europe:

            european_league_list = ['UEFA Champions League', 'UEFA Europa League', 'UEFA Conference League']

            if league in european_league_list:
                european_league_list.remove(league)

            if additional_leagues is not None:
                for added_league in additional_leagues:
                    if added_league in european_league_list:
                        european_league_list.remove(added_league)

            if len(european_league_list) != 0:

                dataframes_to_combine_list = [player_data_dataframe]

                player_data_dataframe_names = player_data_dataframe['player'].tolist()

                for european_league in european_league_list:
                    table = pq.read_table(f'{ROOT_DIR}/player_data_analysis/player_data/{season}/{european_league}.parquet')
                    new_player_data_dataframe = table.to_pandas()
                    new_player_data_dataframe = new_player_data_dataframe[new_player_data_dataframe['player'].isin(player_data_dataframe_names)]
                    dataframes_to_combine_list.append(new_player_data_dataframe)

                player_data_dataframe = pd.concat(dataframes_to_combine_list, ignore_index=True)

                identity_columns = ['player', 'team', 'team id']
                stat_columns = player_data_dataframe.drop(columns=identity_columns + ['player id']).columns.tolist()
                identity_dict = {x: 'last' for x in identity_columns}
                stat_dict = {x: 'sum' for x in stat_columns}

                player_data_dataframe = player_data_dataframe.groupby('player id', as_index=False).agg({**identity_dict, **stat_dict})


        if min_stat_dict is not None or max_stat_dict is not None:
            print(player_data_dataframe.columns.tolist())
            player_data_dataframe_p90 = self._player_data_per_90(player_data_dataframe.copy())
            print(player_data_dataframe.columns.tolist())
            player_data_dataframe, player_data_dataframe_p90 = self._player_data_min_max(player_data_dataframe, player_data_dataframe_p90, min_stat_dict, max_stat_dict)

        #Set dataframe to desired normal or p90 dataframe
        print('p', per_90)
        if per_90:
            player_data_dataframe = self._player_data_per_90(player_data_dataframe)

        player_data_dataframe_ranking = player_data_dataframe.drop(columns=['player', 'team', 'player id', 'team id'])
        player_data_dataframe_ranking = player_data_dataframe_ranking.rank(pct=True, ascending=True)
        player_data_dataframe = player_data_dataframe[['player', 'team', 'player id', 'team id']].join(player_data_dataframe_ranking)

        return player_data_dataframe.loc[player_data_dataframe['player'] == player_name]

player_data_fetcher = PlayerDataFetcher()
result = player_data_fetcher.get_player_percentiles(player_name='Matias Fernandez-Pardo', season=2526, league='FRA-Ligue 1', per_90=True, by_position=True)


print(' ')
print(type(result))
print(result)
print('df length: ', len(result))








