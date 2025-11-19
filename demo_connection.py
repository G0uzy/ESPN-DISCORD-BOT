from espn_client import connect_to_league

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

LEAGUE_ID = int(os.getenv('LEAGUE_ID', '0'))
YEAR = int(os.getenv('YEAR', '2024'))
ESPN_S2 = os.getenv('ESPN_S2')
SWID = os.getenv('SWID')

def main():
    print("Attempting to connect to ESPN League...")
    
    # Note: This will likely fail with placeholders, but demonstrates usage.
    # For public leagues, you can omit espn_s2 and swid.
    league = connect_to_league(LEAGUE_ID, YEAR, espn_s2=ESPN_S2, swid=SWID)
    
    if league:
        print(f"Successfully connected to League: {league.settings.name}")
        if league.teams:
            first_team = league.teams[0]
            print(f"First Team Name: {first_team.team_name}")
        else:
            print("No teams found in the league.")
    else:
        print("Failed to connect to league. Please check your credentials.")

if __name__ == "__main__":
    main()
