import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from espn_client import connect_to_league

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
LEAGUE_ID = int(os.getenv('LEAGUE_ID', '0'))
YEAR = int(os.getenv('YEAR', '2024'))
ESPN_S2 = os.getenv('ESPN_S2')
SWID = os.getenv('SWID')
GUILD_ID = os.getenv('GUILD_ID')

class FantasyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Synced commands to guild {GUILD_ID}")
        else:
            await self.tree.sync()
            print("Synced commands globally (may take up to an hour)")

client = FantasyBot()

@client.tree.command(name="league_info", description="Get information about the ESPN League")
async def league_info(interaction: discord.Interaction):
    """Fetches and displays basic league information."""
    await interaction.response.defer()
    
    if not LEAGUE_ID:
        await interaction.followup.send("League ID not configured.")
        return

    try:
        league = connect_to_league(LEAGUE_ID, YEAR, espn_s2=ESPN_S2, swid=SWID)
        
        if league:
            embed = discord.Embed(
                title=f"{league.settings.name} ({league.year})",
                description="League Information",
                color=discord.Color.green()
            )
            
            teams_list = "\n".join([f"• {team.team_name}" for team in league.teams])
            if len(teams_list) > 1000:
                teams_list = teams_list[:1000] + "..."
                
            embed.add_field(name="Teams", value=teams_list, inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Failed to connect to ESPN League. Please check credentials.")
            
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")

@client.tree.command(name="standings", description="Get the current league standings")
async def standings(interaction: discord.Interaction):
    """Fetches and displays the league standings."""
    await interaction.response.defer()
    
    try:
        league = connect_to_league(LEAGUE_ID, YEAR, espn_s2=ESPN_S2, swid=SWID)
        if not league:
            await interaction.followup.send("Could not connect to league.")
            return

        if hasattr(league, 'standings'):
            teams = league.standings()
        else:
            teams = sorted(league.teams, key=lambda x: (x.wins, x.points_for), reverse=True)

        embed = discord.Embed(title=f"Standings - {league.settings.name}", color=discord.Color.gold())
        
        description = ""
        for i, team in enumerate(teams, 1):
            description += f"**{i}. {team.team_name}** ({team.wins}-{team.losses}-{team.ties})\n"
            description += f"PF: {team.points_for:.2f} | PA: {team.points_against:.2f}\n\n"
            
        embed.description = description
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"Error fetching standings: {str(e)}")

@client.tree.command(name="matchups", description="Get the current week's matchups")
async def matchups(interaction: discord.Interaction):
    """Fetches and displays the current week's matchups."""
    await interaction.response.defer()
    
    try:
        league = connect_to_league(LEAGUE_ID, YEAR, espn_s2=ESPN_S2, swid=SWID)
        if not league:
            await interaction.followup.send("Could not connect to league.")
            return

        # Get current week's box scores
        box_scores = league.box_scores()
        current_week = league.current_week
        
        embed = discord.Embed(title=f"Week {current_week} Matchups", color=discord.Color.blue())
        
        for matchup in box_scores:
            home_team = matchup.home_team
            home_score = matchup.home_score
            
            away_team = matchup.away_team
            away_score = matchup.away_score
            
            if away_team:
                value = f"**{home_team.team_name}** ({home_score})\nvs\n**{away_team.team_name}** ({away_score})"
            else:
                value = f"**{home_team.team_name}** ({home_score}) (BYE)"
                
            embed.add_field(name="Matchup", value=value, inline=True)
            
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"Error fetching matchups: {str(e)}")

@client.tree.command(name="team_info", description="Get details for a specific team")
async def team_info(interaction: discord.Interaction, team_name: str):
    """Fetches details for a specific team by name (partial match)."""
    await interaction.response.defer()
    
    try:
        league = connect_to_league(LEAGUE_ID, YEAR, espn_s2=ESPN_S2, swid=SWID)
        if not league:
            await interaction.followup.send("Could not connect to league.")
            return

        found_team = None
        for team in league.teams:
            if team_name.lower() in team.team_name.lower():
                found_team = team
                break
        
        if found_team:
            embed = discord.Embed(title=f"{found_team.team_name}", color=discord.Color.purple())
            embed.add_field(name="Record", value=f"{found_team.wins}-{found_team.losses}-{found_team.ties}", inline=True)
            embed.add_field(name="Standing", value=f"Rank: {found_team.standing}", inline=True)
            embed.add_field(name="Points", value=f"For: {found_team.points_for}\nAgainst: {found_team.points_against}", inline=False)
            
            roster = "\n".join([f"{p.name} ({p.position})" for p in found_team.roster[:15]])
            if len(found_team.roster) > 15:
                roster += "\n..."
            
            embed.add_field(name="Roster", value=roster, inline=False)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"Team '{team_name}' not found.")
            
    except Exception as e:
        await interaction.followup.send(f"Error fetching team info: {str(e)}")

    except Exception as e:
        await interaction.followup.send(f"Error fetching team info: {str(e)}")

# --- Monitoring System ---

from discord.ext import tasks
import asyncio

# Global state for monitoring
notification_channel_id = None
last_activity_date = 0
last_scores = {}

@client.tree.command(name="set_channel", description="Set the channel for league notifications")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    """Sets the notification channel to the current channel or a specified one."""
    global notification_channel_id
    target_channel = channel or interaction.channel
    notification_channel_id = target_channel.id
    await interaction.response.send_message(f"Notifications will be sent to {target_channel.mention}")

@tasks.loop(minutes=5)
async def monitor_activity():
    """Polls for recent league activity (trades, adds/drops)."""
    global last_activity_date, notification_channel_id
    
    if not notification_channel_id:
        return

    try:
        league = connect_to_league(LEAGUE_ID, YEAR, espn_s2=ESPN_S2, swid=SWID)
        if not league:
            return

        # Fetch recent activity
        activities = league.recent_activity()
        
        # Filter for new activities
        new_activities = []
        if last_activity_date == 0:
             if activities:
                 last_activity_date = activities[0].date
        else:
            for activity in activities:
                if activity.date > last_activity_date:
                    new_activities.append(activity)
                else:
                    break
            
            if new_activities:
                last_activity_date = new_activities[0].date
                
                channel = client.get_channel(notification_channel_id)
                if channel:
                    for act in reversed(new_activities):
                        embed = discord.Embed(title="League Activity", description=str(act), color=discord.Color.orange())
                        await channel.send(embed=embed)

    except Exception as e:
        print(f"Error in monitor_activity: {e}")

@tasks.loop(minutes=1)
async def monitor_scores():
    """Polls for score changes and potential touchdowns."""
    global last_scores, notification_channel_id
    
    if not notification_channel_id:
        return

    try:
        league = connect_to_league(LEAGUE_ID, YEAR, espn_s2=ESPN_S2, swid=SWID)
        if not league:
            return

        box_scores = league.box_scores()
        
        for matchup in box_scores:
            # Check Home Team
            if matchup.home_team:
                prev_score = last_scores.get(matchup.home_team.team_id, 0)
                current_score = matchup.home_score
                
                if current_score >= prev_score + 6:
                    channel = client.get_channel(notification_channel_id)
                    if channel:
                        await channel.send(f"🏈 **TOUCHDOWN ALERT** 🏈\n**{matchup.home_team.team_name}** just scored! New Score: {current_score}\n {matchup.home_team.team_name} now has a projected score of {matchup.projected_score}")

                elif current_score >= prev_score + 3:
                    channel = client.get_channel(notification_channel_id)
                    if channel:
                        await channel.send(f"🏈 **FIELD GOAL ALERT** 🏈\n**{matchup.home_team.team_name}** just scored! New Score: {current_score}\n {matchup.home_team.team_name} now has a projected score of {matchup.projected_score}")
                
                last_scores[matchup.home_team.team_id] = current_score

            # Check Away Team
            if matchup.away_team:
                prev_score = last_scores.get(matchup.away_team.team_id, 0)
                current_score = matchup.away_score
                
                if current_score >= prev_score + 6:
                    channel = client.get_channel(notification_channel_id)
                    if channel:
                        await channel.send(f"🏈 **TOUCHDOWN ALERT** 🏈\n**{matchup.away_team.team_name}** just scored! New Score: {current_score}\n {matchup.away_team.team_name} now has a projected score of {matchup.projected_score}")
                
                elif current_score >= prev_score + 3:
                    channel = client.get_channel(notification_channel_id)
                    if channel:
                        await channel.send(f"🏈 **FIELD GOAL ALERT** 🏈\n**{matchup.away_team.team_name}** just scored! New Score: {current_score}\n {matchup.away_team.team_name} now has a projected score of {matchup.projected_score}")
                
                last_scores[matchup.away_team.team_id] = current_score
            
    except Exception as e:
        print(f"Error in monitor_scores: {e}")

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Bot is ready and slash commands are synced.')
    
    # Start background tasks
    if not monitor_activity.is_running():
        monitor_activity.start()
    if not monitor_scores.is_running():
        monitor_scores.start()

if __name__ == '__main__':
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
