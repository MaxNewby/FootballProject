import pandas as pd
from pathlib import Path
import pyarrow.parquet as pq
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)

ROOT = Path(__file__).resolve().parents[2]

def load_game(season: int, game_id=None, home_team=None, away_team=None):

    if game_id is not None:
        game_data = pd.read_parquet(f'{ROOT}/match_analysis_datasets/{str(season)}_matches_overview.parquet', filters=[('game_id', '=', game_id)])

    elif home_team is not None and away_team is not None:
        game_data = pd.read_parquet(f'{ROOT}/match_analysis_datasets/{str(season)}_matches_overview.parquet', filters=[('home_team', '=', home_team), ('away_team', '=', away_team)])

    else:
        raise Exception('Must specify either game_id or home_team and away_team to find game.')

    return game_data

def load_season(season: int):

    try:
        season_data = pd.read_parquet(f'{ROOT}/match_analysis_datasets/{str(season)}_matches_overview.parquet')
    except:
        raise Exception('Invalid season provided. Enter it as an int, for example: 2122, 2223, 2324, 2425, 2526')

    return season_data



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


def compare_formation_matchups(dataframe, visualisation=False):

    dataframe = dataframe.fillna(0)

    matchup_dict = {}

    for match in dataframe.itertuples():

        try:
            home_formation = match.formation_home
            away_formation = match.formation_away
            odds_list = match.betting_odds
            result = match.result
            home_xg = match.expectedGoals_home
            away_xg = match.expectedGoals_away
            home_big_chances = match.bigChanceCreated_home
            away_big_chances = match.bigChanceCreated_away
            home_shots = match.totalShotsOnGoal_home
            away_shots = match.totalShotsOnGoal_away
            home_shots_ot = match.shotsOnGoal_home
            away_shots_ot = match.shotsOnGoal_away

            #Because these are percentages, they will never be outside the range of -100% to 100%, (-1 to 1 in code)

            '''xG Diff: closer to 0, the closer the game.'''

            xg_percentage_dif = symmetric_difference(home_xg, away_xg)
            big_chances_percentage_dif = symmetric_difference(home_big_chances, away_big_chances)
            shots_percentage_dif = symmetric_difference(home_shots, away_shots)
            shots_ot_percentage_dif = symmetric_difference(home_shots_ot, away_shots_ot)

            average_percentage_dif = (xg_percentage_dif + big_chances_percentage_dif + shots_percentage_dif + shots_ot_percentage_dif)/4
            #print('average_percentage_dif', average_percentage_dif)

            true_odds_list = [] #Odds 0 < x
            true_probability_list = [] #0 to 1

            #Correct the inflated odds by calculating the overpushing margin and dividing to find the true odds
            margin = 0
            for i in odds_list:
                margin += 1/i

            for i in odds_list:
                true_odds_list.append(i/margin)
                true_probability_list.append(1/(i/margin))

            true_probability_list = correct_odds_to_total_one(true_probability_list)

            #print('true_probability_list:', true_probability_list)

            home_matchup = f'{home_formation} (H) vs {away_formation} (A)'
            away_matchup = f'{away_formation} (A) vs {home_formation} (H)'

            if result == 'H':

                home_odds = true_probability_list[0]/2
                away_odds = true_probability_list[2]/2

                home_odds_percentage_dif = home_odds - away_odds
                away_odds_percentage_dif = away_odds - home_odds

                #print(average_percentage_dif)
                #print(home_odds_percentage_dif)
                #print(away_odds_percentage_dif)


                #Difference between performance using stats and the betting odds
                final_home_performance_dif = average_percentage_dif - home_odds_percentage_dif
                final_away_performance_dif = average_percentage_dif - away_odds_percentage_dif

                print('Home Win', 'home_odds:', home_odds, 'away_odds:', away_odds, 'avg_perc_dif:', average_percentage_dif)
                print('H', final_home_performance_dif)
                print('A', final_away_performance_dif)


            elif result == 'D':

                home_odds = true_probability_list[0]
                draw_odds = true_probability_list[1]
                away_odds = true_probability_list[2]

                home_odds_percentage_dif = draw_odds - home_odds
                away_odds_percentage_dif = draw_odds - away_odds

                final_home_performance_dif = average_percentage_dif - home_odds_percentage_dif
                final_away_performance_dif = average_percentage_dif - away_odds_percentage_dif

            elif result == 'A':

                home_odds = true_probability_list[0]
                away_odds = true_probability_list[2]

                away_odds_percentage_dif = away_odds - home_odds
                home_odds_percentage_dif = home_odds - away_odds

                #Difference between performance using stats and the betting odds
                final_home_performance_dif = average_percentage_dif - home_odds_percentage_dif
                final_away_performance_dif = average_percentage_dif - away_odds_percentage_dif


            if matchup_dict.get(home_matchup) is not None:

                matchup_dict.update(
                    {
                        home_matchup: [
                            matchup_dict.get(home_matchup)[0] + final_home_performance_dif,
                            # Actual Score Update. If it doesn't exist, default values are set
                            matchup_dict.get(home_matchup)[1] + 1  # Games played update
                        ]
                    }
                )

                matchup_dict.update(
                    {
                        away_matchup: [
                            matchup_dict.get(away_matchup)[0] + final_away_performance_dif,  # Actual Score Update
                            matchup_dict.get(away_matchup)[1] + 1  # Games played update
                        ]
                    }
                )
            else:
                matchup_dict.update({home_matchup: [final_home_performance_dif, 1]})
                matchup_dict.update({away_matchup: [final_away_performance_dif, 1]})



        except:
            SyntaxError('Some stat in this game could not be found. Skipping match')
            pass

        else:
            pass

    matchup_dict = {
        matchup: [stats[0], stats[1], stats[0]/stats[1]] for matchup, stats in matchup_dict.items() if stats[1] >= 10 #Append a 3rd item to the list that is score/games played
    }

    '''
    matchup_dict now has matchup: [score, games played, average]. Filtering for only matchups with more than 10 games played included.
    Print results in order:
    '''

    matchup_results_list = []

    for matchup, stats in matchup_dict.items():


        if not matchup_results_list: #If list is empty, add first matchup to list
            matchup_results_list.append([matchup, stats[2]])
        else: #If list contains items, go through each item in the list and place item where the averaged score
            inserted = False
            for i, mr in enumerate(matchup_results_list):
                if matchup_dict.get(mr[0])[2] < stats[2]:
                    matchup_results_list.insert(i, [matchup, stats[2]])
                    inserted = True
                    break

            #If no item has a smaller score than the current matchup, and it hasn't broke the loop, append it to the end of the list
            if not inserted:
                matchup_results_list.append([matchup, stats[2]])

    for i in matchup_results_list:
        print(f'{i[0]}: {i[1]}')

    if visualisation:
        formation_list = [x[0] for x in matchup_results_list]
        score_list = [x[1] for x in matchup_results_list]

        plt.figure(figsize=(34, 96))
        bar_plot = plt.barh(formation_list, score_list)

        plt.gca().invert_xaxis()
        plt.gca().invert_yaxis()

        for bar in bar_plot:
            width = bar.get_width()
            plt.text(width/2, bar.get_y() + bar.get_height()/2, f'{width:.3f}', ha='center', va='center', fontsize=24, fontweight='bold')

        plt.title('Averaged calculated performance of formations across 3 seasons in comparison to the betting odds.', fontsize=40)
        plt.ylabel('Formations', fontsize=40)
        plt.yticks(size=32, fontweight='bold')
        plt.xlabel('Performance averaged across games played', fontsize=40)
        plt.xticks(fontsize=32)
        plt.subplots_adjust(left=0.25)

        for i in range(5, len(formation_list), 5):
            plt.axhline(i - 0.5, linestyle=":", linewidth=4, alpha=0.75)

        plt.savefig(f'{ROOT}/analysis_plots/formation_betting_performance.png')

        '''
        plt.figure(figsize=(96, 32))
        
        bars = plt.bar(formation_list, score_list)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f'{height:.2f}',
                ha='center',
                va='bottom',
                fontsize=20,
                fontweight='bold'
            )
        
        plt.title(
            'Averaged calculated performance of formations across 3 seasons in comparison to the betting odds.',
            fontsize=40
        )
        plt.xlabel('Formations', fontsize=40)
        plt.xticks(rotation=90, size=32, fontweight='bold')
        plt.ylabel('Performance averaged across games played', fontsize=40)
        plt.yticks(fontsize=32)
        
        plt.subplots_adjust(bottom=0.35)
        
        for i in range(5, len(formation_list), 5):
            plt.axvline(i - 0.5, linestyle=":", linewidth=2, alpha=0.5)
        
        plt.show()
        '''


    return matchup_dict






test_df = load_season(2526)
test_df_two = load_season(2425)
test_df_three = load_season(2324)

test_df = pd.concat([test_df, test_df_two, test_df_three])

print(compare_formation_matchups(test_df, True))