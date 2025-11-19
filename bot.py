import discord
import os
from discord.ext import commands
from dotenv import load_dotenv
from espn_client import connect_to_league

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
LEAGUE_ID = int(os.getenv('LEAGUE_ID', '0'))
YEAR = int(os.getenv('YEAR', '2024'))
ESPN_S2 = os.getenv('ESPN_S2')
SWID = os.getenv('SWID')

class FantasyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = FantasyBot()

@client.tree.command(name="league_info", description="Get information about the ESPN League")
async def league_info(interaction: discord.Interaction):
    """Fetches and displays basic league information."""
    await interaction.response.defer()
    
    if not LEAGUE_ID:
        await interaction.followup.send("League ID not configured.")
        return

    try:
        # Note: connect_to_league is synchronous. For a production bot, 
        # this should be run in an executor to avoid blocking the event loop.
        # For this simple example, we call it directly.
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

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Bot is ready and slash commands are synced.')

if __name__ == '__main__':
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
