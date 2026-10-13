WS_TEAM_MAP = {
    'ENG-Premier League': {
        "Man Utd": "Manchester United",
        "Man City": "Manchester City",
        "Wolves": "Wolverhampton Wanderers",
        "Tottenham": "Tottenham Hotspur",
        "Leicester": "Leicester City",
        "Ipswich": "Ipswich Town",
        "Nottingham Forest": "Nottingham Forest",
        "West Ham": "West Ham United",
        "Brighton": "Brighton & Hove Albion",
        "Newcastle": "Newcastle United",
        "Bournemouth": "AFC Bournemouth",
        "Arsenal": "Arsenal",
        "Everton": "Everton",
        "Fulham": "Fulham",
        "Chelsea": "Chelsea",
        "Aston Villa": "Aston Villa",
        "Southampton": "Southampton",
        "Crystal Palace": "Crystal Palace",
        "Liverpool": "Liverpool",
        "Brentford": "Brentford",
        "Burnley": "Burnley",
        "Norwich City": "Norwich City",
        "Leeds United": "Leeds United",
        "Luton Town": "Luton Town",
        "Sheffield United": "Sheffield United",
        "Watford": "Watford",
        "Sunderland": "Sunderland",
    }
}

def get_ws_abbreviation_to_name_map(league, home_team_abb):
    return WS_TEAM_MAP.get(league, {}).get(home_team_abb, None)

