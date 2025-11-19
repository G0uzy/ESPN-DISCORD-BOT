from espn_client import connect_to_league

# PLACEHOLDER CREDENTIALS - PLEASE REPLACE WITH YOUR ACTUAL DATA
LEAGUE_ID = 12345678  # Replace with your League ID (int)
YEAR = 2024           # Replace with the current year (int)
ESPN_S2 = 'PLACEHOLDER' # Replace with your espn_s2 cookie string
SWID = 'PLACEHOLDER'    # Replace with your swid cookie string

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
