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


def check_custom_emoji(base_api_url, headers, server_id):
  '''
  Function to check if the custom emoji's are available on the server
  '''
  emoji_count = 0
  emoji_list = {
    "Zeus"    : "",
    "Command" : "",
    "SL"      : "",
    "Medic"   : "",
    "MSC"     : "",
    "Maybe"   : ""
  }
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
          emoji_list[emoji] = (':' + custom_emoji["name"]+':'+custom_emoji["id"])
          print(f"{emoji_list[emoji]} is found.")
  return emoji_list
    

def create_custom_emoji(base_api_url, headers):
  '''
  Function to create the custom emoji's if necesary
  '''
  server_ids = get_server_ids()
  for server_id in server_ids:
    emoji_list = check_custom_emoji(base_api_url, headers, server_id)

    for emoji in emoji_list:
      if emoji_list[emoji] == "":
        headers = {
          "Authorization": f"Bot {bot_token}",
          "Content-Type": "application/json"
        }
        emoji_url = f"{base_api_url}/guilds/{server_id}/emojis"
        emoji_path = f"emojis/{emoji}.png"       
        
        try:
          with open(emoji_path, "rb") as emoji_png:
            emoji_data = base64.b64encode(emoji_png.read()).decode()
        except FileNotFoundError:
          print(
            f"Emoji: {emoji} not found in {emoji_path}.\n" +
            "This is a critical error, the program will shutdown now."
          )
          exit()
        
        data = {
          "name": f"{emoji}",
          "image": f"data:image/png;base64,{emoji_data}"
        }

        json_data = json.dumps(data)
        created_emoji = requests.post(emoji_url, headers=headers, data=json_data)
        
        if created_emoji.status_code == 201:
          created_emoji = created_emoji.json()
        else:
          print(f"Failed to upload emoji. Error: {created_emoji.text}.")

        emoji_list[emoji] = (':'+created_emoji["name"]+':'+created_emoji["id"])
        print(f"{emoji_list[emoji]} has been created.")
    return emoji_list


def regex_compiler(message, key):
  '''
  Function to recompile regex
  '''
  regex = re.compile(key)
  text = re.findall(regex, message.content)[0]

  return text


async def check_category(guild):
  '''
  Function to check if the necesary categories are on the server
  '''
  for channel in channel_list:
    for category in channel_list[channel]:
      if category == "category":
        category_needed = channel_list[channel][category]
        category_exists = False
        for guild_cat in guild.categories:
          if category_needed == str(guild_cat):
            category_exists = True
            break
        
        if category_exists == False:
          print(f"Category: {category_needed} is being created.")
          await guild.create_category(category_needed)


async def check_channels(guild):
  '''
  Function to check if the necesary channels are on the server
  '''
  await check_category(guild)

  for channel in channel_list:
    channel_exists = False
    for existing_channel in guild.text_channels:
      existing_channel = str(existing_channel)
      if existing_channel in channel_list[channel]["name"]:
        channel_exists = True
        break
      
    if channel_exists == False:
      category = discord.utils.get(guild.categories, name=channel_list[channel]["category"])
      channel_name = channel_list[channel]["name"]
      channel_position = channel_list[channel]["position"]

      print(f"Channel: {channel_name} is being created in Categorie: {category}")
      await category.create_text_channel(name=channel_name, position=channel_position)


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


async def get_channel(guild, category_name, channel_name):
  '''
  Function to get the channel from a channel name
  '''
  category = discord.utils.get(guild.categories, name=category_name)
  channel = discord.utils.get(category.channels, name=channel_name)

  return channel


async def get_message(guild, category_name, channel_name, message_id):
  '''
  Function to get a message from a message id
  '''
  channel = await get_channel(guild, category_name, channel_name)
  message = await channel.fetch_message(message_id)

  return message


async def emoji_add(emoji_list, emoji_filter, information, squad_list_message, event_member_name):
  '''
  Function to check what emoji got added and adjust the reacted lists
  '''
  for emoji in emoji_list:
    if emoji_filter == emoji_list[emoji]:
      emoji_reacted = emoji + "_reacted"
      information["squad_list"][emoji_reacted].append(event_member_name)
      print(f"Added {event_member_name} to the {emoji_reacted} list for mission: {information['mission_name']}.")
      await send_squad_lists(
        information["squad_list"],
        squad_list_message,
        information['mission_name']
      )

  return information


async def reaction_delete(emoji_list, emoji_filter, information, squad_list_message, reposted_message):
  '''
  Function to check what emoji got removed and adjust the reacted lists
  '''
  for emoji in emoji_list:
    for reaction in reposted_message.reactions:
      reaction_emoji = (":"+str(reaction.emoji.name)+":"+str(reaction.emoji.id))
      if emoji_filter == emoji_list[emoji] and emoji_filter == reaction_emoji:
        emoji_reacted = emoji+"_reacted"
        async for user in reaction.users():
          for player in information["squad_list"][emoji_reacted]:
            if not player == user.name:
              information["squad_list"][emoji_reacted].remove(player)
              print(f"Removed {player} from the {emoji_reacted} list for mission: {information['mission_name']}.")
              await send_squad_lists(
                information["squad_list"],
                squad_list_message,
                information['mission_name']
              )

  return information  



# #########################################################################
# Main Variables
# #########################################################################

load_dotenv()
bot_token = os.getenv("DISCORD_TOKEN")
server_name = os.getenv("DISCORD_SERVER")
bot_name = os.getenv("DISCORD_BOT_NAME")

client = discord.Client(intents=discord.Intents.all())

channel_list = {
  "attendance-setup":
    {
    "category":"Missions",
    "name":"attendance-setup",
    "position":3
    },
  "attendance":
    {
    "category":"Missions",
    "name":"attendance",
    "position":0
    },
  "squad-list":
    {
    "category":"Missions",
    "name":"squad-list",
    "position":2
    },
  "announcements":
    {
    "category":"UNIT Information",
    "name":"📣announcements",
    "position":2
    }
}
mission_list = []
mission_count = 0

contract_keywords = {
  "Contract ": r"(Contract .*)",
  "Operation ": r"(Operation .*)",
  "**Contract ": r"..(Contract .*)..",
  "**Operation ": r"..(Operation .*)..",
  "date": r"Date: <t:(.*):F>"
}
command_messages = {
  "help": "?help",
  "exit": "?exit"
}

bot_startup = ""
bot_startup_message = f"The bot is active now, type '{command_messages['help']}' for help and '{command_messages['exit']}' to shutdown."
shutdown_message = "The bot will shutdown in 5 seconds."

squad_list_message_init = "Squad list waiting to be build for mission: "
announcements_template = "@everyone The attendance for **{}** on <t:{}:F>! Please make sure to mark if you plan to attend."
help_message_template = (
  "**Help for the {}**\n\n" +
  "This message is a reply to the ?help-command in the server: {}.\n\n" +
  "The bot works with a few keywords in the {}:\n\t- 'Contract '\n\t- 'Operation '\n\t- '**Contract **'\n\t- '**Operation **'\n\n" 
  "Upon starting the mission briefing with these words the bot will repost the briefing in the attendance channel and add the custom emoji's. "
  "After this the players can select their roles and then there will be a username posted in the {} channel."      
)

base_api_url = "https://discord.com/api/v10"
headers = {
    "Authorization":f"Bot {bot_token}"
  }

emoji_list = create_custom_emoji(base_api_url, headers)



# #########################################################################
# Bot events
# #########################################################################

@client.event
async def on_ready():
  '''
  Bot startup
  '''
  global bot_startup
  guild = discord.utils.get(client.guilds, name = server_name)

  print(
    f'{client.user} has connected to the following guild:\n'
    f'Guild name: {guild.name}, Guild id: {guild.id}'
  )

  await check_channels(guild)
  
  attendance_setup_channel = await get_channel(
    guild,
    channel_list["attendance-setup"]["category"],
    channel_list["attendance-setup"]["name"]
  )

  bot_startup = await attendance_setup_channel.send(bot_startup_message)


@client.event
async def on_message(message):
  '''
  Bot message recieved
  '''
  guild = discord.utils.get(client.guilds, name=server_name)
  global mission_list

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
        mission_name = regex_compiler(message, contract_keywords[keyword])
        mission_date = regex_compiler(message, contract_keywords["date"])
 
    if mission_name != "":
      attendance_channel = await get_channel(
        guild,
        channel_list["attendance"]["category"],
        channel_list["attendance"]["name"]
      )
      squad_list_channel = await get_channel(
        guild,
        channel_list["squad-list"]["category"],
        channel_list["squad-list"]["name"]
      )
      announcements_channel = await get_channel(
        guild,
        channel_list["announcements"]["category"],
        channel_list["announcements"]["name"]
      )
      announcements_message = announcements_template.format(mission_name, mission_date)

      reposted_message = await attendance_channel.send(message.content)
      squad_list_message = await squad_list_channel.send(squad_list_message_init + mission_name)

      mission_messages = {
        "mission_name": mission_name,
        "mission_date": mission_date,
        "reposted_message": reposted_message,
        "squad_list_message": squad_list_message,
        "squad_list": {
          "Zeus_reacted"    : [],
          "Command_reacted" : [],
          "SL_reacted"      : [],
          "Medic_reacted"   : [],
          "MSC_reacted"     : [],
          "Maybe_reacted"   : []
        }
      }

      mission_count = 0
      if mission_list != []:
        for _ in mission_list:
          mission_count += 1

      mission_list.append({mission_count:mission_messages})

      for emoji in emoji_list:
        await reposted_message.add_reaction(emoji_list[emoji])
        
      await announcements_channel.send(announcements_message)

      if mission_list[mission_count] != {}:
        await asyncio.sleep(10)
        await message.delete()

  elif message.content.find("?") == 0:
    if message.content.lower() == command_messages["help"]:
      print("Help command executed by: " + message.author.name)

      help_message_content = help_message_template.format(
        bot_name,
        server_name,
        channel_list['attendance-setup']['name'],
        channel_list['squad-list']['name']
      )

      await message.author.send(help_message_content)
      await message.delete()

    elif message.content.lower() == command_messages["exit"]:
      print("Shutdown command executed by: " + message.author.name)
      await bot_startup.edit(content=shutdown_message)
      await message.delete()
      print(shutdown_message)
      await asyncio.sleep(4)
      await bot_startup.delete()
      await asyncio.sleep(1)
      await client.close()


@client.event
async def on_raw_reaction_add(event):
  '''
  Bot reaction added
  '''
  guild = discord.utils.get(client.guilds, name=server_name)
  emoji_filter = (":"+str(event.emoji.name)+":"+str(event.emoji.id))
  event_member_name = event.member.name

  if not event.member.name == bot_name:
    for missions in mission_list:
      for _, information in missions.items():
        if event.message_id == information["reposted_message"].id:
          squad_list_message = await get_message(
            guild,
            channel_list["squad-list"]["category"],
            channel_list["squad-list"]["name"],
            information["squad_list_message"].id
          )

          information = await emoji_add(emoji_list, emoji_filter, information, squad_list_message, event_member_name)


@client.event
async def on_raw_reaction_remove(event):
  '''
  Bot reaction removed
  '''
  guild = discord.utils.get(client.guilds, name=server_name)
  emoji_filter = (":"+str(event.emoji.name)+":"+str(event.emoji.id))
  for missions in mission_list:
    for _, information in missions.items():
      if event.message_id == information["reposted_message"].id:
        squad_list_message = await get_message (
          guild,
          channel_list["squad-list"]["category"],
          channel_list["squad-list"]["name"],
          information["squad_list_message"].id
        )
        reposted_message = await get_message (
          guild,
          channel_list["attendance"]["category"],
          channel_list["attendance"]["name"],
          information["reposted_message"].id
        )
        
        information = await reaction_delete(emoji_list, emoji_filter, information, squad_list_message, reposted_message)



# #########################################################################
# Bot start
# #########################################################################

client.run(bot_token)