# #########################################################################
# Necesary packets to be installed
# #########################################################################

'''
- Python 3.10.7

Execute this command from the location where the bot and the files are stored:
pip install -r requirements.txt
'''



# #########################################################################
# Information Sources
# #########################################################################

'''
Discord bot: https://discordpy.readthedocs.io/en/stable/discord.html
Discord Documentation: https://discord.com/developers/docs/intro
ChatGPT for code explainations
'''



# #########################################################################
# Imports
# #########################################################################

import os
import re
import discord
import requests
import asyncio
import base64
import json
from dotenv import load_dotenv



# #########################################################################
# Helper Function
# #########################################################################

def get_server_ids():
  '''
  Function to save all the id's from the guild the bot is joined.
  '''
  guilds_url = f"{base_api_url}/users/@me/guilds"
  servers = requests.get(guilds_url, headers=headers)
  server_ids = []

  if servers.status_code == 200:
    servers = servers.json()
    for server in servers:
      if server["name"] == server_name:
        server_ids.append(server["id"])
        break
    return server_ids
  else:
    print("Error in connecting to discord API.")


def check_emoji_status(headers):
  '''
  Function to check if the necesary custom emoji's are available.
  If not, then they are automatically created if there is enough free emoji space.
  '''
  server_ids = get_server_ids()
  emoji_count = 0

  emoji_list = {
    "Zeus"    : "",
    "Command" : "",
    "SL"      : "",
    "Medic"   : "",
    "MSC"     : "",
    "Maybe"   : ""
  }

  for server_id in server_ids:
    emojis_url = f"{base_api_url}/guilds/{server_id}/emojis"
    emojis = requests.get(emojis_url, headers=headers)

    if emojis.status_code == 200:
      emojis = emojis.json()

      for custom_emoji in emojis:
        emoji_count = emoji_count + 1

      if emoji_count >= 45:
        print(
          "There are too much custom emoji's on this server. This is a critical problem.\n" +
          "The program will shutdown now."
        )
        exit()
      else:
        for custom_emoji in emojis:
          for emoji in emoji_list:
            if emoji == custom_emoji["name"]:
              emoji_list[emoji] = (':' + custom_emoji["name"] + ':' + custom_emoji["id"])
              print(f"{emoji_list[emoji]} is found.")

        for emoji in emoji_list:
          emoji_file_found = False
          if emoji_list[emoji] == "":
            headers = {
              "Authorization": f"Bot {bot_token}",
              "Content-Type": "application/json"
            }
            emoji_url = f"{base_api_url}/guilds/{server_id}/emojis"
            emoji_path = f"npe-eindopdracht-voske123/emojis/{emoji}.png"

            try:
              test_path = open(emoji_path)
              test_path.close()
              emoji_file_found = True
            except FileNotFoundError:
              print(
                f"Emoji: {emoji} not found in {emoji_path}.\n" +
                "This is a critical error, the program will shutdown now."
              )
              exit()

            
            if emoji_file_found:
              with open(emoji_path, "rb") as emoji_png:
                emoji_data = base64.b64encode(emoji_png.read()).decode()
              
              data = {
                "name": f"{emoji}",
                "image": f"data:image/png;base64,{emoji_data}"
              }

              created_emoji = requests.post(emoji_url, headers=headers, data=json.dumps(data))
              
              if created_emoji.status_code == 201:
                created_emoji = created_emoji.json()
              else:
                print(f"Failed to upload emoji. Error: {created_emoji.text}.")

              emoji_list[emoji] = (':' + created_emoji["name"] + ':' + created_emoji["id"])
              print(f"{emoji_list[emoji]} has been created.")
  return emoji_list


async def check_channel_status(guild):
  '''
  Function to check if the necesary category and channels are available or need to be created
  '''
  zeus_missions_category = None
  for category in guild.categories:
    if category.name == category_name:
      zeus_missions_category = category
      break
  if zeus_missions_category == None:
    print(f"Creating category: {category_name}.")
    zeus_missions_category = await guild.create_category(category_name)
  else:
    print(f"{category_name} already exists.")

  for channel in channel_list:
    channel_exists = False
    for channels in zeus_missions_category.text_channels:
      if channels.name == channel_list[channel]["name"]:
        channel_exists = True
        break
    
    if channel_exists == False:
      await zeus_missions_category.create_text_channel(name=channel_list[channel]["name"], position=channel_list[channel]["position"])
      print(f"Creating channel: {channel}")
    else:
      print(f"{channel} exists already.")


async def send_squad_lists(squad_lists, squad_list_message, mission_name):
  '''
  Function to adjust the squad list message with the signed up users.
  '''
  total_player_count = (
    len(squad_lists["Zeus_reacted"])     +
    len(squad_lists["Command_reacted"])  +
    len(squad_lists["SL_reacted"])       +
    len(squad_lists["Medic_reacted"])    +
    len(squad_lists["MSC_reacted"])      +
    len(squad_lists["Maybe_reacted"])
  )

  message_content = (
    '**Squad list for Mission: **'  + mission_name                                        + "\n\n" +
    '**Zeus**: '                    + ' '.join(squad_lists["Zeus_reacted"])     +"."      + "\n\n" +
    '**Commanding**: '              + ' '.join(squad_lists["Command_reacted"])  +"."      + "\n\n" +
    '**Squad Leaders**: '           + ' '.join(squad_lists["SL_reacted"])       +"."      + "\n\n" +
    '**Medics**: '                  + ' '.join(squad_lists["Medic_reacted"])    +"."      + "\n\n" + 
    '**Unassigned**: '              + ' '.join(squad_lists["MSC_reacted"])      +"."      + '\n\n' +
    '**Maybe**: '                   + ' '.join(squad_lists["Maybe_reacted"])    +"."      + '\n\n' +
    '**Total attendance**: '        + str(total_player_count)
  )

  await asyncio.sleep(1)
  await squad_list_message.edit(content=message_content)   



# #########################################################################
# Main Variables
# #########################################################################

load_dotenv()
bot_token = os.getenv("DISCORD_TOKEN")
server_name = os.getenv("DISCORD_SERVER")
bot_name = os.getenv("DISCORD_BOT_NAME")

client = discord.Client(intents=discord.Intents.all())

category_name = "Missions"
channel_list = {
  "attendance-setup":{"name":"attendance-setup","position":3},
  "attendance":{"name":"attendance","position":0},
  "squad-list":{"name":"squad-list","position":2}
}
bot_startup = ""
message_list = []
squad_list_mission = []
squad_list_message_init = "Squad list waiting to be build for mission: "
contract_keywords = {
  "Contract ": r"(Contract .*)",
  "Operation ": r"(Operation .*)",
  "**Contract ": r"..(Contract .*)..",
  "**Operation ": r"..(Operation .*)..",
}
command_messages = {
  "help": "?help",
  "exit": "?exit"
}

base_api_url = "https://discord.com/api/v10"
headers = {
    "Authorization":f"Bot {bot_token}"
  }
emoji_list = check_emoji_status(headers)



# #########################################################################
# Bot events
# #########################################################################

@client.event
async def on_ready():
  '''
  Initialization of the discord bot, loading in the guild and execute channel check.
  '''
  global bot_startup
  guild = discord.utils.get(client.guilds, name = server_name)
  print(
    f'{client.user} has connected to the following guild:\n'
    f'Guild name: {guild.name}, Guild id: {guild.id}'
  )

  await check_channel_status(guild)
  
  category = discord.utils.get(guild.categories, name=category_name)
  attendance_setup_channel = discord.utils.get(category.channels, name=channel_list["attendance-setup"]["name"])
  bot_startup = await attendance_setup_channel.send(f"The bot is active now, type '{command_messages['help']}' for help and '{command_messages['exit']}' to shutdown.")


@client.event
async def on_message(message):

  '''
  On a message it will check if the author is the bot or if its a dm to the bot, in both cases the message will be skipped.
  If not then it will check if the message is send in channel_list["attendance-setup"] and starts with the word "Contract " or "Operation ".
  After this it reposts the message in the channel_list["attendance"] and posts a message in channel_list["squad-list"].
  Both these messages are being saved in a dictionary with key: mission_name and value: both messages.
  After this the emoji's are being posted as a reaction on the reposted message.
  '''
  guild = discord.utils.get(client.guilds, name=server_name)
  global message_list

  try:
    message.channel.name
  except AttributeError:
    print("Last message was a DM and does not have a channel name, skipping.")
    return

  if message.author == client.user:
    print("Last message sent by bot, skipping.")
    return
  
  elif message.channel.name == channel_list["attendance-setup"]["name"] and not message.content.find("?") == 0:
    mission_name = ""
    mission_messages = {}
    for keyword in contract_keywords:
      if message.content.startswith(keyword):
        regex = re.compile(contract_keywords[keyword])
        mission_name = re.findall(regex, message.content)[0]

    if mission_name != "":
      category = discord.utils.get(guild.categories, name=category_name)
      attendance_channel = discord.utils.get(category.channels, name=channel_list["attendance"]["name"])
      squad_list_channel = discord.utils.get(category.channels, name=channel_list["squad-list"]["name"])

      reposted_message = await attendance_channel.send(message.content)
      squad_list_message = await squad_list_channel.send(squad_list_message_init + mission_name)

      mission_messages = {
        "reposted_message":reposted_message,
        "squad_list_message":squad_list_message
      }
      message_list.append({mission_name:mission_messages})

      for emoji in emoji_list:
        await reposted_message.add_reaction(emoji_list[emoji])
      
      if mission_messages != {}:
        await asyncio.sleep(10)
        await message.delete()
  
  elif message.content.find("?") == 0:
    if message.content.lower() == command_messages["help"]:
      print("Help command executed by: " + message.author.name)
      help_message_content = (
        f"**Help for the {bot_name}**\n\n" +
        f"This message is a reply to the ?help-command that has been send in the discord: {message.guild.name}.\n\n" +
        f"The bot works with a few keywords in the {channel_list['attendance-setup']['name']}:\n\t- 'Contract '\n\t- 'Operation '\n\t- '**Contract **'\n\t- '**Operation **'\n\n" 
        f"Upon starting the mission briefing with these words the bot will repost the briefing in the attendance channel and add the custom emoji's. "
        f"After this the players can select their roles and then there will be a username posted in the {channel_list['squad-list']['name']} channel."      
      )
      await message.author.send(help_message_content)
      await message.delete()

    elif message.content.lower() == command_messages["exit"]:
      print("Shutdown command executed by: " + message.author.name)
      await bot_startup.edit(content="The bot will shutdown in 5 seconds.")
      await message.delete()
      print("The bot will shutdown in 5 seconds.")
      await asyncio.sleep(4)
      await bot_startup.delete()
      await asyncio.sleep(1)
      await client.close()


@client.event
async def on_raw_reaction_add(event):
  '''
  On a reaction added that is not being made by the bot.
  Then a check is being made if there already were reactions.
  If not then the list is being initialized with empty values
  The reaction is being transformed in the correct syntax
  Then it iterates over the lists until it found the correct emoji and add the user to the according list
  Next step the message in the squad-list channel is being edited with the list of username who signed up
  After this the bot deletes the message in attendance-setup channel

  Help and Exit commands are also being traced in this function.
  '''
  global squad_list_mission

  if not event.member.name == bot_name:
    mission_found = False

    for messages in message_list:
      for mission_name, message in messages.items():
        if event.message_id == message["reposted_message"].id:
          squad_list_channel = client.get_channel(message["squad_list_message"].channel.id)
          squad_list_message = await squad_list_channel.fetch_message(message["squad_list_message"].id)

          lines = squad_list_message.content.split("\n")

          if lines[0].startswith(squad_list_message_init):
            for missions in squad_list_mission:
              for squad_mission_name, squad_list in missions.items():
                if squad_mission_name == mission_name:
                  mission_found = True

            if mission_found == False:
              print("Initializing the new list.")
              squad_lists = {
                "Zeus_reacted"    : [],
                "Command_reacted" : [],
                "SL_reacted"      : [],
                "Medic_reacted"   : [],
                "MSC_reacted"     : [],
                "Maybe_reacted"   : []
              }
              squad_list_mission.append({mission_name:squad_lists})

          emoji_filter = (":" + str(event.emoji.name) + ":" + str(event.emoji.id))
          for emoji in emoji_list:
            emoji_reacted = emoji+"_reacted"
            if emoji_filter == emoji_list[emoji]:
              for mission in squad_list_mission:
                for squad_mission_name, squad_lists in mission.items():
                  if squad_mission_name == mission_name:
                    squad_lists[emoji_reacted].append(event.member.name)
                    print(f"Added {event.member.name} to the {emoji_reacted} list for mission: {mission_name}.")
                    await send_squad_lists(squad_lists, squad_list_message, mission_name)


@client.event
async def on_raw_reaction_remove(event):
  '''
  On reaction remove it checks the according message in the squad-list channel.
  There it extracts the mission_name (starts either with Contract or Operation).
  It iterates the list created on reaction added to search all the users who are still reacted to the message with that emoji
  After this it compares this list with the squad-list list and it removes the users in this list that are not in the current reactions
  Last the squad-list message gets updated with the latest usernames who reacted or removed the reaction
  '''
  emoji_removed = (":"+str(event.emoji.name)+":"+str(event.emoji.id))
  for messages in message_list:
    for mission_name, message in messages.items():
      if event.message_id == message["reposted_message"].id:
        squad_channel = client.get_channel(message["squad_list_message"].channel.id)
        squad_list_message = await squad_channel.fetch_message(message["squad_list_message"].id)
        repost_channel = client.get_channel(message["reposted_message"].channel.id)
        repost_message = await repost_channel.fetch_message(message["reposted_message"].id)

        lines = squad_list_message.content.split("\n")
        if lines[0].startswith("**Squad list for Mission: **"):
          existing_mission_name = ""
          for keyword in contract_keywords:
            regex = re.compile(contract_keywords[keyword])
            try: 
              existing_mission_name = re.findall(regex, lines[0])[0]
              print("Mission name found!")
              break
            except IndexError:
              continue

          if existing_mission_name != "":
            for mission in squad_list_mission:
              for squad_mission_name, squad_lists in mission.items():
                if existing_mission_name == squad_mission_name:
                  for emoji in emoji_list:
                    emoji_reacted = emoji+"_reacted"
                    if emoji_removed == emoji_list[emoji]:
                      for reaction in repost_message.reactions:
                        if emoji_removed == (":"+str(reaction.emoji.name)+":"+str(reaction.emoji.id)):
                          async for user in reaction.users():
                            for player in squad_lists[emoji_reacted]:
                              if not player == user.name: 
                                squad_lists[emoji_reacted].remove(player)
                                print(f"Removed {player} from the {emoji_reacted} list for mission: {existing_mission_name}.")

                                await send_squad_lists(squad_lists, squad_list_message, existing_mission_name)



# #########################################################################
# Bot start
# #########################################################################

client.run(bot_token)