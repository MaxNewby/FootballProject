import os
import time
import pandas as pd
import ScraperFC as sfc
from understatapi import UnderstatClient
from uvicorn.config import is_dir
from GetFootballData.transfermarkt_scraper import TransfermarktScraper
from year_map import convert_season_to_year
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
from league_map import league_dict
from GetFootballData.fotmob_scraper import FotmobScraper
from GetFootballData.sofascore_scraper import SofascoreScraper
from GetFootballData.transfermarkt_scraper import TransfermarktScraper
from GetFootballData.scraper_utilities.league_to_sofascore_map import league_to_sofascore_dict

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

ROOT = Path(__file__).resolve().parents[2]

year_to_str_season_dict = {'2019':'19/20', '2020': '20/21', '2021': '21/22', '2022': '22/23', '2023': '23/24', '2024': '24/25', '2025': '25/26', '2026': '26/27'}
year_to_int_season_dict = {2019: 1920, 2020: 2021, 2021: 2122, 2022: 2223, 2023: 2324, 2024: 2425, 2025: 2526, 2026: 2627}

'''
Supply the season as an int in the form for ex: 2021, 2022, 2023. The starting year of the season
'''

def get_season_player_data(year_list: list):

    season_list = [year_to_int_season_dict[x] for x in year_list]

    dataframe = pd.read_parquet(f'{ROOT}/player_data_analysis/player_lists/squad_mi_dataframe.parquet')

    print(dataframe.head())

    understat_data = []

    with UnderstatClient() as understat:

        for season in season_list:

            season_data = dataframe.loc[season]
            league_player_data = understat.league(league="EPL").get_player_data(season=convert_season_to_year(season))
            print(league_player_data)

            for player in league_player_data:
                understat_data.append({
                    "season": season,
                    "player_name": player["player_name"],
                    "id": player["id"],
                    "games": player["games"],
                    "time": player["time"],
                    "goals": player["goals"],
                    "xG": player["xG"],
                    "assists": player["assists"],
                    "xA": player["xA"],
                    "shots": player["shots"],
                    "key_passes": player["key_passes"],
                    "yellow_cards": player["yellow_cards"],
                    "red_cards": player["red_cards"],
                    "npg": player["npg"],
                    "npxG": player["npxG"],
                    "xGChain": player["xGChain"],
                    "xGBuildup": player["xGBuildup"],
                })

#get_season_player_data(season_list=[2526])


'''
Included leagues are:
'Argentina Liga Profesional', 'Argentina Copa de la Liga Profesional', 'Bulgaria Parva Liga', 'CONCACAF Gold Cup', 'CONMEBOL Copa Libertadores', 'England Premier League', 'England EFL Championship', 'England WSL', 'England WSL 2', 'FIFA World Cup', 'FIFA Womens World Cup', 'France Ligue 1', 'France Ligue 2', 'France National 1', 'Germany Bundesliga', 'Germany 2.Bundesliga', 'Italy Serie A', 'Italy Serie B', 'Mexico Liga MX Apertura', 'Mexico Liga MX Clausura', 'Netherlands Eredivisie', 'Peru Liga 1', 'Portugal Primeira Liga', 'Portugal Liga Portugal 2', 'Saudi Arabia Pro League', 'Spain La Liga', 'Spain La Liga 2', 'Turkiye Super Lig', 'UEFA Champions League', 'UEFA Europa League', 'UEFA Conference League', 'UEFA European Championship', 'Ukraine Premier League', 'USA MLS', 'USA USL championship', 'USA USL League 1', 'USA USL Leauge 2'

'''
def save_player_season_data(league_list: list , year_list: list):

    '''

    :param league_list: list of strings containing each league name data is wanted from
    :param year_list: list of ints containing the starting years of the seasons that data will be collected from.
    :return:
    '''

    invalid_list = {}

    sss = SofascoreScraper()

    for league in league_list:

        for year in year_list:

            season = year_to_int_season_dict[year]

            player_data = sss.get_player_stat_dataframe_test(year, league) #Get player data
            if player_data.empty: #If the dataframe is empty, there is data to save so skip this iteration
                continue

            print(f'{league}, {season}, Type: {type(player_data)}, {len(player_data)}')

            if not Path.is_dir(Path(f'{ROOT}/player_data_analysis/player_data')):
                os.mkdir(Path(f'{ROOT}/player_data_analysis/player_data'))

            if not Path.is_dir(Path(f'{ROOT}/player_data_analysis/player_data/{season}')):
                os.mkdir(Path(f'{ROOT}/player_data_analysis/player_data/{season}'))

            table = pa.Table.from_pandas(player_data)
            pq.write_table(table, f'{ROOT}/player_data_analysis/player_data/{season}/{league}.parquet')

    if len(invalid_list) > 0:
        print(f'Invalid List: {invalid_list}')



def save_player_season_data_p90(year_list=None, league_list=None):

    inputted_year_list = year_list
    inputted_league_list = league_list

    if not is_dir(Path(f'{ROOT}/player_data_analysis/player_data_p90')):
        os.mkdir(Path(f'{ROOT}/player_data_analysis/player_data_p90'))

    if inputted_year_list is None or inputted_year_list is None:
        year_list = os.listdir(f'{ROOT}/player_data_analysis/player_data') #Default is to do every file in /player_data

    for year in year_list:

        season = year_to_int_season_dict[year]

        if inputted_year_list is None or inputted_league_list is None:
            league_list = os.listdir(f'{ROOT}/player_data_analysis/player_data/{season}')
            league_list = [league[:-8] for league in league_list]
            print(year, league_list)

        for league in league_list:
            table = pq.read_table(f'{ROOT}/player_data_analysis/player_data/{year}/{season}.parquet')
            dataframe = table.to_pandas()
            print(year, league)

            if dataframe.empty:
                continue

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
                dataframe[column] = dataframe[column]/(dataframe['minutesPlayed']/90)

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

            if not is_dir(Path(f'{ROOT}/player_data_analysis/player_data_p90/{season}')):
                os.mkdir(f'{ROOT}/player_data_analysis/player_data_p90/{season}')

            table = pa.Table.from_pandas(dataframe)
            pq.write_table(table, f'{ROOT}/player_data_analysis/player_data_p90/{year}/{season}.parquet')


def percentile_rank_player_data_dataframe(dataframe):

    data_only_dataframe = dataframe.drop(['player', 'team', 'player id', 'team id'], axis=1)
    data_only_dataframe = data_only_dataframe.rank(pct=True, ascending=True)
    dataframe[data_only_dataframe.columns] = data_only_dataframe

    return dataframe



def save_player_season_data_percentiles(year_list=None, league_list=None, per_ninety=False):

    '''
    :param season_list: optional list of specific seasons to save percentile data for
    :param league_list: optional list of specific leagues to save percentile data for
    :param per_ninety: save percentile data for normal player data or per ninety player data
    '''

    inputted_year_list = year_list
    inputted_league_list = league_list

    if per_ninety: #Add string to file paths to change the directory that is read, and to keep the if statements less complex
        per_ninety_string = '_p90'
    else:
        per_ninety_string = ''

    if not is_dir(Path(f'{ROOT}/player_data_analysis/player_data{per_ninety_string}_percentiles')):
        os.mkdir(Path(f'{ROOT}/player_data_analysis/player_data{per_ninety_string}_percentiles'))

    if inputted_year_list is None or inputted_league_list is None:
        season_list = os.listdir(f'{ROOT}/player_data_analysis/player_data{per_ninety_string}')

    for year in year_list:

        season = year_to_int_season_dict[year]

        if inputted_year_list is None or inputted_league_list is None:
            league_list = os.listdir(f'{ROOT}/player_data_analysis/player_data{per_ninety_string}/{season}')
            league_list = [column[:-8] for column in league_list] #Get rid of the .parquet part to standardise it for reading the table so i don't do file.parquet.parquet

        for league in league_list:
            table = pq.read_table(f'{ROOT}/player_data_analysis/player_data{per_ninety_string}/{season}/{league}.parquet')
            dataframe = table.to_pandas()

            if dataframe.empty:
                continue

            dataframe = percentile_rank_player_data_dataframe(dataframe)

            if not is_dir(Path(f'{ROOT}/player_data_analysis/player_data{per_ninety_string}_percentiles/{season}')):
                os.mkdir(f'{ROOT}/player_data_analysis/player_data{per_ninety_string}_percentiles/{season}')

            table = pa.Table.from_pandas(dataframe)
            pq.write_table(table, f'{ROOT}/player_data_analysis/player_data{per_ninety_string}_percentiles/{season}/{league}.parquet')


def save_transfermarkt_overview_data(year_list, league_list):
    """Save the data scraped from transfermarkt to files"""

    tms = TransfermarktScraper()

    for year in year_list:

        season = year_to_int_season_dict[year]

        for league in league_list:

            players_dataframe = tms.get_all_player_overview_df(year, league)

            print(players_dataframe.columns.tolist())
            players_dataframe['league'] = league

            if not Path.is_dir(Path(f'{ROOT}/player_data_analysis/player_overview')):
                os.mkdir(Path(f'{ROOT}/player_data_analysis/player_overview'))

            if not Path.is_dir(Path(f'{ROOT}/player_data_analysis/player_overview/{season}')):
                os.mkdir(Path(f'{ROOT}/player_data_analysis/player_overview/{season}'))

            #players_dataframe.set_index(['ID'], inplace=True)

            table = pa.Table.from_pandas(players_dataframe)
            pq.write_table(table, f'{ROOT}/player_data_analysis/player_overview/{season}/{league}.parquet')


def save_transfermarkt_player_transfer_history(year_list, league_list):
    """Scrape and saves transfer history from transfermarkt for each given player in the dataframe"""

    tms = TransfermarktScraper()

    for year in year_list:

        season = year_to_int_season_dict[year]

        for league in league_list:

            if os.path.isfile(Path(f'{ROOT}/player_data_analysis/player_overview/{season}/{league}.parquet')):

                if not is_dir(Path(f'{ROOT}/player_data_analysis/player_transfer_history/{season}')):
                    os.mkdir(Path(f'{ROOT}/player_data_analysis/player_transfer_history/{season}'))

                table = pq.read_table(f'{ROOT}/player_data_analysis/player_overview/{season}/{league}.parquet')
                player_dataframe = table.to_pandas()
                print(len(player_dataframe))

                player_total = len(player_dataframe)
                count = 0

                transfer_history_list = []

                player_dataframe.columns = player_dataframe.columns.str.replace(' ', '_')
                print(player_dataframe.columns.tolist())

                for player in player_dataframe.itertuples():

                    player_name = player.player_name
                    player_id = player.Index[0]

                    transfer_df = tms.get_player_transfer_history(player_id)
                    transfer_df.reset_index(inplace=True)
                    print(transfer_df.columns.tolist())
                    #print(transfer_df.season.tolist())

                    if transfer_df.empty:
                        continue

                    transfer_df['name'] = player_name

                    transfer_history_list.append(transfer_df)

                    count += 1
                    print(f'{count}/{player_total}')

                    time.sleep(0.3)

                print(len(transfer_history_list))

                dataframe = pd.concat(transfer_history_list, ignore_index=True)

                dataframe.set_index(['player_id'], inplace=True)

                table = pa.Table.from_pandas(dataframe)
                pq.write_table(table, f'{ROOT}/player_data_analysis/player_transfer_history/{season}/{league}.parquet')

            else:
                raise Exception(f'File {season}/{league}.parquet not found in player_data_analysis/player_overview directory')





def create_player_list(season=2526):
    '''
    :param optional - players from a specific season
    :return:
    '''

    season = str(season)

    if is_dir(Path(f'{ROOT}/player_data_analysis/player_overview/{season}')):

        player_dict = {}

        total_file_number = len(os.listdir(Path(f'{ROOT}/player_data_analysis/player_overview/{season}')))
        count = 1

        for file in os.listdir(Path(f'{ROOT}/player_data_analysis/player_overview/{season}')):

            print(f'Extracting file {count}/{total_file_number}')

            table = pq.read_table(f'{ROOT}/player_data_analysis/player_overview/{season}/{file}')
            player_dataframe = table.to_pandas()
            player_dataframe.columns = player_dataframe.columns.str.replace(' ', '_')

            for player in player_dataframe.itertuples():
                player_dict.update({player.Name: player.league})

            print(f'{count}/{total_file_number} files complete')
            count += 1

        player_list_df = pd.DataFrame(list(player_dict.items()), columns=['name', 'league']).set_index('name')
        table = pa.Table.from_pandas(player_list_df)
        pq.write_table(table, f'{ROOT}/player_data_analysis/player_lists/player_list.parquet')




def collect_season_stats(player_name, season_list=None):
    """Collect career stats for all provided seasons for a given player

    :param: player_name: name of the player
    :param: (optional) season_list: collect stats across specified season(s) since 21/22
    """

    table = pq.read_table(f'{ROOT}/player_data_analysis/player_lists/player_list.parquet')
    player_list_dataframe = table.to_pandas()
    player_league = player_list_dataframe.loc[player_name]['league']
    season_league_dict = {}

    player_overview_table = pq.read_table(f'{ROOT}/player_data_analysis/player_overview/2526/{player_league}.parquet')
    player_overview_dataframe = player_overview_table.to_pandas()
    player_id = player_overview_dataframe.loc[player_name].index[0]

    transfer_history_overview_table = pq.read_table(f'{ROOT}/player_data_analysis/player_transfer_history/2526/{player_league}.parquet')
    transfer_history_dataframe = transfer_history_overview_table.to_pandas()

    years_to_leagues_dict = {}
    career_path_dataframe = transfer_history_dataframe.loc[(player_name, player_id),['source_competition', 'destination_competition', 'season']]






#save_player_season_data(['ENG-Premier League', 'ENG-Championship', 'ESP-La Liga', 'ESP-Segunda División', 'ITA-Serie A', 'ITA-Serie B', 'GER-Bundesliga', 'GER-2. Bundesliga', 'FRA-Ligue 1', 'FRA-Ligue 2', 'ARG-Liga Profesional de Fútbol', 'ARG-Copa de la Liga Profesional', 'BUL-Parva Liga', 'CONCACAF-Gold Cup', 'CONMEBOL-Copa Libertadores', "ENG-Women's Super League", "ENG-Women's Super League 2", 'INT-FIFA World Cup', "INT-FIFA Women's World Cup", 'FRA-National 1', 'MEX-Liga MX, Apertura', 'MEX-Liga MX, Clausura', 'NED-Eredivisie', 'PER-Liga 1', 'POR-Liga Portugal', 'POR-Liga Portugal 2', 'KSA-Saudi Pro League', 'TUR-Trendyol Süper Lig', 'UEFA-Champions League', 'UEFA-Europa League', 'UEFA-Conference League', 'UEFA-European Championship', 'UKR-Premier League', 'USA-MLS', 'USA-USL Championship'], [2021])
#save_player_season_data(['EUR-UEFA Champions League', 'EUR-UEFA Europa League', 'EUR-UEFA Conference League'], [2021, 2022, 2023, 2024, 2025, 2026])
#save_transfermarkt_overview_data([2025], ['ENG-Premier League', 'SPA-La Liga', 'ITA-Serie A', 'FRA-Ligue 1', 'GER-Bundesliga'])
#save_transfermarkt_player_transfer_history([2526], ['ENG-Premier League', 'SPA-La Liga', 'ITA-Serie A', 'FRA-Ligue 1', 'GER-Bundesliga'])
#save_player_season_data_p90()
#save_player_season_data_percentiles()

#Save player_data -> save player_data p90 -> save percentile data for both

'''
table = pq.read_table(f"{ROOT}/player_data_analysis/player_data/2526/ENG-Premier League.parquet")
player_data_dataframe = table.to_pandas()
player_data_names_list = player_data_dataframe['player'].tolist()
print(len(player_data_dataframe))

table = pq.read_table(f"{ROOT}/player_data_analysis/player_overview/2526/ENG-Premier League.parquet")
player_overview_dataframe = table.to_pandas()
print(player_overview_dataframe.columns.to_list())
player_overview_names_list = player_overview_dataframe['player_name'].tolist()

non_matching_names_list = [name for name in player_data_names_list if name not in player_overview_names_list]
print(non_matching_names_list)
'''