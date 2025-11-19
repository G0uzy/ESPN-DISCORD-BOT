from espn_api.football import League

def connect_to_league(league_id, year, espn_s2=None, swid=None):
    """
    Connects to an ESPN Fantasy Football league.
    
    Args:
        league_id (int): The ID of the league.
        year (int): The year of the season.
        espn_s2 (str, optional): The espn_s2 cookie for private leagues.
        swid (str, optional): The swid cookie for private leagues.
        
    Returns:
        League: The connected League object.
    """
    try:
        print(f"Connecting to league {league_id} for year {year}...")
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
        return league
    except Exception as e:
        print(f"Error connecting to league: {e}")
        return None
