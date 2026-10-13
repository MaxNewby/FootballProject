import numpy as np
import pandas as pd
from bisect import bisect_right

class EventDataProcessing:

    def __init__(self):

        self.TYPE_TO_COLUMN = {
            ('Start', None): [],  # (type, outcome_type): [list of stats to add +1 to]
            ('BallTouch', 'Successful'): ['possession_keeping_touches'],
            ('BallTouch', 'Unsuccessful'): ['miscontrolled_touches'],
            ('BallRecovery', 'Successful'): ['ball_recoveries'],
            ('MissedShots', 'Successful'): ['missed_shots', 'attempted_shots'],
            ('Clearance', 'Successful'): ['clearances'],
            ('Dispossessed', 'Successful'): ['dispossessed'],
            ('ShieldBallOpp', 'Successful'): ['balls_shielded_out'],
            ('ShieldBallOpp', 'Unsuccessful'): ['shielded_from_ball'],
            ('GoodSkill', 'Successful'): ['good_skills'],
            ('OffsideGiven', 'Successful'): ['offsides_given'],
            ('OffsidePass', 'Successful'): ['offside_passes'],
            ('OffsideProvoked', 'Successful'): ['offsides_provoked'],
            ('KeeperPickup', 'Successful'): ['keeper_pickups'],
            ('BlockedPass', 'Successful'): ['blocked_passes', 'attempted_passes'],
            ('SavedShot', 'Successful'): ['saved_shots', 'attempted_shots'],
            ('Save', 'Successful'): ['saves'],
            ('KeeperSweeper', 'Successful'): ['keeper_sweepers'],
            ('Interception', 'Successful'): ['interceptions'],
            ('CornerAwarded', 'Successful'): ['corners_won'],
            ('CornerAwarded', 'Unsuccessful'): ['corners_lost'],
            ('Foul', 'Successful'): ['fouls_won'],
            ('Foul', 'Unsuccessful'): ['fouls_lost'],
            ('Error', 'Successful'): ['errors'],
            ('ChanceMissed', 'Successful'): ['chances_missed', 'attempted_shots'],
            ('ShotOnPost', 'Successful'): ['post_shots', 'attempted_shots'],
            ('End', None): [],  # match/period marker, not a stat
            ('Claim', 'Successful'): ['claims'],
            ('Goal', 'Successful'): ['goals', 'attempted_shots', 'shots_on_target'],
            ('Punch', 'Successful'): ['punches'],
            ('SubstitutionOn', 'Successful'): ['sub_ons'],  # handled separately in your position-tracking loop
            ('SubstitutionOff', 'Successful'): ['sub_offs'],  # handled separately in your position-tracking loop
            ('Smother', 'Successful'): ['keeper_smothers'],
            ('FormationChange', None): [],  # handled separately in your position-tracking loop
            ('Pass', 'Successful'): ['attempted_passes', 'completed_passes'],
            ('Pass', 'Unsuccessful'): ['attempted_passes'],
            ('Tackle', 'Successful'): ['attempted_tackles', 'successful_tackles'],
            ('Tackle', 'Unsuccessful'): ['attempted_tackles'],
            ('Aerial', 'Successful'): ['attempted_passes', 'completed_passes', 'attempted_aerials', 'completed_aerials'],
            ('Aerial', 'Unsuccessful'): ['attempted_passes', 'attempted_aerials'],
            ('TakeOn', 'Successful'): ['take_ons', 'successful_take_ons'],
            ('TakeOn', 'Unsuccessful'): ['take_ons'],
            ('Challenge', 'Successful'): ['challenges', 'successful_challenges'],
            ('Challenge', 'Unsuccessful'): ['challenges'],
            ('PenaltyFaced', 'Successful'): ['penalties_faced', 'penalties_saved'],
            ('PenaltyFaced', 'Unsuccessful'): ['penalties_faced'],
        }

        self.successful_pass_dist_labels, self.successful_pass_dist_edges = ['successful_x<10_yard_pass', 'successful_10<=x<20_yard_pass', 'successful_20<=x<30_yard_pass', 'successful_30<=x<40_yard_pass', 'successful_40<=x<50_yard_pass', 'successful_x>50_yard_pass'], [0, 10, 20, 30, 40, 50, np.inf]
        self.unsuccessful_pass_dist_labels, self.unsuccessful_pass_dist_edges = ['unsuccessful_x<10_yard_pass', 'unsuccessful_10<=x<20_yard_pass', 'unsuccessful_20<=x<30_yard_pass', 'unsuccessful_30<=x<40_yard_pass', 'unsuccessful_40<=x<50_yard_pass', 'unsuccessful_x>50_yard_pass'], [0, 10, 20, 30, 40, 50, np.inf]
        self.shot_inside_box_dist_labels = ['six_yard_box_shot', 'in_penalty_box_shot']
        self.shot_outside_box_dist_labels, self.shot_outside_box_dist_edges = ['edge_of_the_box_shot', 'x>25_yard_shot', 'x>35_yard_shot'], [0, 25, 35, np.inf]
        self.shots_on_target_label = ['shots_on_target']
        self.card_labels = ['Yellow', 'SecondYellow', 'Red']



    def get_all_stat_columns(self) -> list:
        #Ensure a unique list of all the possible columns are returned to help construct the overall match stats datasets.
        column_list = list({item for sublist in self.TYPE_TO_COLUMN.values() for item in sublist}) + self.successful_pass_dist_labels + self.unsuccessful_pass_dist_labels + self.shot_outside_box_dist_labels + self.shot_inside_box_dist_labels + self.shots_on_target_label + self.card_labels
        return column_list


    def get_standard_data(self, type, success):
        columns = self.TYPE_TO_COLUMN.get((type, success), [])
        return columns.copy()


    def get_pass_extra_data(self, outcome_type, event_distance):
        #If an event distance is on the boundary, (e.g. exactly 10), it will be included in the bin to the right, which is the larger distance bracket (e.g. 10_to_20_yard_pass)
        column_name_list = []

        match outcome_type: #Get correct distance label for the pass
            case 'Successful':
                label = self.successful_pass_dist_labels[bisect_right(self.successful_pass_dist_edges, event_distance) - 1]
                column_name_list += [label]
            case 'Unsuccessful':
                label = self.unsuccessful_pass_dist_labels[bisect_right(self.unsuccessful_pass_dist_edges, event_distance) - 1]
                column_name_list += [label]
            case _:
                pass

        return column_name_list


    def get_missed_or_saved_shot_extra_data(self, event_distance, goal_mouth_y, goal_mouth_z, pitch_dimension_y):
        #max_y is pitch width, max z is 20 feet
        column_name_list = ['attempted_shots']
        label = self.shot_outside_box_dist_labels[bisect_right(self.shot_outside_box_dist_edges, event_distance) - 1]
        column_name_list += [label]

        pitch_middle = pitch_dimension_y / 2
        left_post = ((pitch_middle + 12)/pitch_dimension_y)*100
        right_post = ((pitch_middle - 12)/pitch_dimension_y)*100

        if goal_mouth_z < 40.0 and left_post > goal_mouth_y > right_post: #Because ball further left is actually a higher coordinate value
            column_name_list += ['shots_on_target']


    def get_goals_extra_data(self, event_distance):
        pass
