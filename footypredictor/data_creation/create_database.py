import pandas as pd
import soccerdata as sd
from pathlib import Path
from team_data_collector import MatchHistoryFromESPN, ESPNMatchLineup, UnderstatFromESPN, SofascoreFromESPN, build_scrapers, get_match_history_df


ROOT_DIR = Path(__file__).resolve().parents[2]

'''
sd.ESPN -> ESPN.read_schedule() -> ESPNMatchLineup (For Lineup Players) -> MatchHistoryFromESPN (For Match Stats)

sd.ESPN: The original GetFootballData provided by soccerdata

ESPN.read_schedule(): Gets the dataframe of selected matches. Take 'game' and 'game_id' columns, and turn them into a list

ESPNMatchLineup: Provides a selection of data on a given match.
Use the conversion methods in this class to use the 'FromESPN' classes for more data (by getting fetching compatible game_id)

MatchHistoryFromESPN - For betting odds and match stats
UnderstatFromESPN - For xg
SofascoreFromESPN - For big chances
'''

def create_database(season_list: list):

    for season in season_list:

        scrapers = build_scrapers(season)
        en = scrapers['en']
        ss = scrapers['ss']
        mh = scrapers['mh']
        ss_sfc = scrapers['ss_sfc']

        match_history_df = get_match_history_df(mh, season)
        en_epl_schedule = en.read_schedule()
        ss_epl_schedule = ss.read_schedule()

        games = en_epl_schedule.reset_index()[["game", "game_id"]].itertuples(index=False, name=None)
        games = list(games)
        print(games[0])
        espn_match_lineup_games = list(map(lambda x: ESPNMatchLineup(x, season, en), games))
        print(espn_match_lineup_games)

        metadata_column_names = [
            "game_id",
            "home_team",
            "away_team",
            "date",
            "result",
            "formation_home",
            "formation_away",
            "lineup_shots_home",
            "sub_shots_home",
            "lineup_shots_away",
            "sub_shots_away",
            "lineup_shots_on_target_home",
            "sub_shots_on_target_home",
            "lineup_shots_on_target_away",
            "sub_shots_on_target_away",
            "betting_odds",
            "understat_raw_data",
            "sofascore_raw_data",
            "match_history_name",
            "lineup_list_home",
            "lineup_list_away",
            "sub_list_home",
            "sub_list_away"
        ]

        matchup_list = []
        matchup_count = 0
        total_matchups = len(espn_match_lineup_games)
        for matchup in espn_match_lineup_games:

            match_history = MatchHistoryFromESPN(matchup.get_matchhistory_row(match_history_df))
            sofascore = SofascoreFromESPN(matchup.get_scraper_fc_sofascore_match_data(ss_epl_schedule), ss_sfc)

            metadata_entry = [
                matchup.get_match_id(),
                matchup.get_home_team(),
                matchup.get_away_team(),
                matchup.get_date(),
                match_history.get_result(),
                matchup.get_formation(is_home=True),
                matchup.get_formation(is_home=False),
                matchup.get_home_lineup_shots(),
                matchup.get_home_sub_shots(),
                matchup.get_away_lineup_shots(),
                matchup.get_away_sub_shots(),
                matchup.get_home_lineup_shots_on_target(),
                matchup.get_home_sub_shots_on_target(),
                matchup.get_away_lineup_shots_on_target(),
                matchup.get_away_sub_shots_on_target(),
                match_history.get_result_betting_odds(),
                matchup.get_understat_match_data(),
                matchup.get_scraper_fc_sofascore_match_data(ss_epl_schedule),
                matchup.get_matchhistory_name(),
                matchup.get_home_lineup_player_list(),
                matchup.get_away_lineup_player_list(),
                matchup.get_home_sub_player_list(),
                matchup.get_away_sub_player_list(),
            ]

            home_names, home_match_data = sofascore.get_home_data()
            away_names, away_match_data = sofascore.get_away_data()

            home_column_names = [f"{name}_home" for name in home_names]
            away_column_names = [f"{name}_away" for name in away_names]

            metadata_column_names_end = [
            "lineup_goals_home",
            "lineup_goals_away",
            "subs_goals_home",
            "subs_goals_away",
            "lineup_shots_player_dict_home",
            "lineup_shots_player_dict_away",
            "sub_shots_player_dict_home",
            "sub_shots_player_dict_away",
            "lineup_shots_on_target_player_dict_home",
            "lineup_shots_on_target_player_dict_away",
            "sub_shots_on_target_player_dict_home",
            "sub_shots_on_target_player_dict_away",
            "sub_in_times_player_dict_home",
            "sub_in_times_player_dict_away",
            "sub_out_times_player_dict_home",
            "sub_out_times_player_dict_away",
            "lineup_fouls_commited_player_dict_home",
            "lineup_fouls_commited_player_dict_away",
            "sub_fouls_commited_player_dict_home",
            "sub_fouls_commited_player_dict_away",
            "lineup_fouls_suffered_player_dict_home",
            "lineup_fouls_suffered_player_dict_away",
            "sub_fouls_suffered_player_dict_home",
            "sub_fouls_suffered_player_dict_away",
            "lineup_own_goals_player_dict_home",
            "lineup_own_goals_player_dict_away",
            "sub_own_goals_player_dict_home",
            "sub_own_goals_player_dict_away",
            "lineup_yellow_cards_player_dict_home",
            "lineup_yellow_cards_player_dict_away",
            "sub_yellow_cards_player_dict_home",
            "sub_yellow_cards_player_dict_away",
            "lineup_red_cards_player_dict_home",
            "lineup_red_cards_player_dict_away",
            "sub_red_cards_player_dict_home",
            "sub_red_cards_player_dict_away",
            "lineup_goals_conceded_player_dict_home",
            "lineup_goals_conceded_player_dict_away",
            "sub_goals_conceded_player_dict_home",
            "sub_goals_conceded_player_dict_away",
            "lineup_saves_player_dict_home",
            "lineup_saves_player_dict_away",
            "sub_saves_player_dict_home",
            "sub_saves_player_dict_away",
            "lineup_shots_faced_player_dict_home",
            "lineup_shots_faced_player_dict_away",
            "sub_shots_faced_player_dict_home",
            "sub_shots_faced_player_dict_away"
            ]

            metadata_entry_end = [
                matchup.get_home_lineup_total_goals_dict(),
                matchup.get_away_lineup_total_goals_dict(),
                matchup.get_home_sub_total_goals_dict(),
                matchup.get_away_sub_total_goals_dict(),
                matchup.get_home_lineup_assists_dict(),
                matchup.get_away_lineup_assists_dict(),
                matchup.get_home_sub_assists_dict(),
                matchup.get_away_sub_assists_dict(),
                matchup.get_home_lineup_shots_dict(),
                matchup.get_away_lineup_shots_dict(),
                matchup.get_home_sub_shots_on_target_dict(),
                matchup.get_away_sub_shots_on_target_dict(),
                matchup.get_home_sub_in_dict(),
                matchup.get_away_sub_in_dict(),
                matchup.get_home_sub_out_dict(), #
                matchup.get_away_sub_out_dict(),
                matchup.get_home_lineup_fouls_committed_dict(),
                matchup.get_away_lineup_fouls_committed_dict(),
                matchup.get_home_sub_fouls_committed_dict(),
                matchup.get_away_sub_fouls_committed_dict(),
                matchup.get_home_lineup_fouls_suffered_dict(),
                matchup.get_away_lineup_fouls_suffered_dict(),
                matchup.get_home_sub_fouls_suffered_dict(),
                matchup.get_away_sub_fouls_suffered_dict(),
                matchup.get_home_lineup_own_goals_dict(),
                matchup.get_away_lineup_own_goals_dict(),
                matchup.get_home_sub_own_goals_dict(),
                matchup.get_away_sub_own_goals_dict(),
                matchup.get_home_lineup_yellow_cards_dict(),
                matchup.get_away_lineup_yellow_cards_dict(),
                matchup.get_home_sub_yellow_cards_dict(),
                matchup.get_away_sub_yellow_cards_dict(),
                matchup.get_home_lineup_red_cards_dict(),
                matchup.get_away_lineup_red_cards_dict(),
                matchup.get_home_sub_red_cards_dict(),
                matchup.get_away_sub_red_cards_dict(),
                matchup.get_home_lineup_goals_conceded_dict(),
                matchup.get_away_lineup_goals_conceded_dict(),
                matchup.get_home_sub_goals_conceded_dict(),
                matchup.get_away_sub_goals_conceded_dict(),
                matchup.get_home_lineup_saves_dict(),
                matchup.get_away_lineup_saves_dict(),
                matchup.get_home_sub_saves_dict(),
                matchup.get_away_sub_saves_dict(),
                matchup.get_home_lineup_shots_faced_dict(),
                matchup.get_away_lineup_shots_faced_dict(),
                matchup.get_home_sub_shots_faced_dict(),
                matchup.get_away_sub_shots_faced_dict()
            ]

            metadata_entry_end = [data if data else None for data in metadata_entry_end] #keep data if data (exists in dict). If empty, become None, for data in metadata_entry_end

            all_column_names = metadata_column_names + home_column_names + away_column_names + metadata_column_names_end
            all_values = metadata_entry + home_match_data + away_match_data + metadata_entry_end




            match_row = dict(zip(all_column_names, all_values))

            matchup_list.append(match_row)

            matchup_count += 1
            print(f'{matchup_count}/{total_matchups} added')


        matches_df = pd.DataFrame(matchup_list)

        #Rearranging the column indexs




        matches_df.to_parquet(f'{ROOT_DIR}/match_analysis_datasets/{season}_matches_overview.parquet', index=False)

        '''
        "game_id", "understat_raw_data", "sofascore_raw_data", "match_history_name", "date", "result", "home_team", "away_team",
        "home_formation", "away_formation", "home_lineup_shots", "home_sub_shots", "away_lineup_shots", "away_sub_shots",
        "home_lineup_shots_on_target", "home_sub_shots_on_target", "away_lineup_shots_on_target", "away_sub_shots_on_target",
        "betting_odds"
        
        'Ball possession' 'Distance covered' 'Expected goals' 'Total shots' 'Goalkeeper saves' 'Number of sprints' 'Corner kicks' 'Fouls' 'Passes'
         'Tackles' 'Free kicks' 'Yellow cards' 'Shots on target' 'Hit woodwork' 'Shots off target' 'Blocked shots' 'Shots inside box' 'Shots outside box'
         'Through balls' 'Touches in penalty area' 'Fouled in final third' 'Offsides' 'Accurate passes' 'Throw-ins' 'Final third entries'
         'Final third phase' 'Long balls' 'Crosses' 'Duels' 'Dispossessed' 'Ground duels' 'Aerial duels' 'Dribbles' 'Tackles won' 'Total tackles'
         'Interceptions' 'Recoveries' 'Clearances' 'Total saves' 'Goals prevented' 'Big saves' 'High claims' 'Goal kicks'

         append _home for home stats
         append _away for away stats
         no total column so you will have to add them together to get a total
        '''

season_list = [2223, 2324, 2425, 2526]
create_database(season_list)