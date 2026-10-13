season_to_starting_year = {
    1920: '2019',
    2021: '2020',
    2122: '2021',
    2223: '2022',
    2324: '2023',
    2425: '2024',
    2526: '2025',
    2627: '2026',
}

starting_to_season_year = {
    '2019': 1920,
    '2020': 2021,
    '2021': 2122,
    '2022': 2223,
    '2023': 2324,
    '2024': 2425,
    '2025': 2526,
    '2026': 2627,
}

def convert_season_to_year(year: int):
    try:
        return season_to_starting_year.get(year)
    except:
        KeyError('The year provided is not a valid key in the season_to_starting_year dict.')

def convert_year_to_season(year):
    try:
        return starting_to_season_year.get(year)
    except:
        KeyError('The year provided is not a valid key in the starting_to_season_year dict.')
