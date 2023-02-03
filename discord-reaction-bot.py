# #########################################################################
# Necesary packets to be installed
# #########################################################################

'''
- Python 3.10.8

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
import discord
import asyncio
import datetime
from function_library import *
from dotenv import load_dotenv



# #########################################################################
# Main Variables
# #########################################################################

load_dotenv()
bot_token = os.getenv("DISCORD_TOKEN")
server_name = os.getenv("DISCORD_SERVER")
bot_name = os.getenv("DISCORD_BOT_NAME")

client = discord.Client(intents=discord.Intents.all())

channel_list = {
  "zeus-setup":
    {
    "category":"MISSIONS",
    "name":"zeus-setup",
    "position":3,
    "topic": "In this channel you can send the bot commands to make attendance missions and copy missionfiles to the server."
    },
  "attendance":
    {
    "category":"MISSIONS",
    "name":"attendance",
    "position":1,
    "topic": "This channel shows the attendance messages for the missions, please use the reactions to select the role you play."
    },
  "squad-list":
    {
    "category":"MISSIONS",
    "name":"squad-list",
    "position":2,
    "topic": "In this channel the squad lists for the missions are being shown based on the reactions in the attendance channel."
    },
  "announcements":
    {
    "category":"UNIT INFORMATION",
    "name":"📣announcements",
    "position":2,
    "topic": "Important announcements are shown here."
    }
  }
mission_list = []
mission_count = 0
mission_folder_path = "E:\Games\ArmA3\A3Master\mpmissions"

contract_keywords = {
  "Contract ": r"(Contract .*)",
  "Operation ": r"(Operation .*)",
  "**Contract ": r"..(Contract .*)..",
  "**Operation ": r"..(Operation .*)..",
  "date": r"Date: <t:(.*):F>"
  }
command_messages = {
  "help": "?help",
  "exit": "?exit",
  "add_mission": "!add_mission",
  "clear_messages": "!clear_messages"
  }

bot_startup = ""
help_message_template = (
  "**Help for the {}**\n\n" +
  "This message is a reply to the ?help-command in the server: {}.\n\n" +
  "The bot works with a few keywords in the {}:\n\t- 'Contract '\n\t- 'Operation '\n\t- '**Contract **'\n\t- '**Operation **'\n\n" 
  "Upon starting the mission briefing with these words the bot will repost the briefing in the attendance channel and add the custom emoji's. "
  "After this the players can select their roles and then there will be a username posted in the {} channel."      
  )
bot_messages = {
  "bot_startup_message": f"The bot is active now, type '{command_messages['help']}' for help and '{command_messages['exit']}' to shutdown.",
  "shutdown_message": "The bot will shutdown in 5 seconds.",
  "squad_list_message_init": "Squad list waiting to be build for mission: ",
  "announcements_template": "@everyone The attendance for **{}** on <t:{}:F> is up! Please make sure to mark if you plan to attend.",
  "file_exists": "This mission is already on the server, please give the mission a different name.\nThis message deletes itself in 20 seconds.",
  "incorrect_format": "Please upload a correct missionfile for arma3.\nThis message deletes itself in 20 seconds.",
  "incorrect_time": "You have entered an incorrect Date for this mission, its starting time is older than the current time.\nThis message deletes itself in 20 seconds.",
  "attachement_saved": "Mission is saved in the MPmissions folder on the server.\nThis message deletes itself in 5 seconds.",
  "no_attachments": "No attachments found in the message, please post a new message.\nThis message deletes itself in 20 seconds.",
  "insufficient_rights": "Please contact an administrator, it seems that you don't have the necesary role to upload a mission.\nThis message deletes itself in 20 seconds."
  }

base_api_url = "https://discord.com/api/v10"
headers = {
    "Authorization":f"Bot {bot_token}"
  }

emoji_list = create_custom_emoji(
  base_api_url,
  headers,
  server_name,
  bot_token
  )



# #########################################################################
# Bot events
# #########################################################################

@client.event
async def on_ready():
  '''
  Bot startup
  '''
  global bot_startup
  global mission_list
  guild = discord.utils.get(client.guilds, name = server_name)
  current_time = round(datetime.datetime.now().timestamp())
  print(
    f'{client.user} has connected to the following guild:\n'
    f'Guild name: {guild.name}, Guild id: {guild.id}'
    )

  await check_channels(guild, channel_list)
  
  zeus_setup_channel = await get_channel(
    guild,
    channel_list["zeus-setup"]["category"],
    channel_list["zeus-setup"]["name"]
    )
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

  mission_list = await old_missions(
    attendance_channel,
    squad_list_channel,
    mission_list,
    emoji_list,
    current_time,
    contract_keywords,
    bot_name
    )
  bot_startup = await zeus_setup_channel.send(bot_messages["bot_startup_message"])


@client.event
async def on_message(message):
  '''
  Bot message recieved
  '''
  guild = discord.utils.get(client.guilds, name=server_name)
  current_time = round(datetime.datetime.now().timestamp())

  try:
    message.channel.name
  except AttributeError:
    print("Last message was a DM and does not have a channel name, skipping.")
    return


  if message.author == client.user:
    print("Last message sent by bot, skipping.")
    return


  elif message.channel.name == channel_list["zeus-setup"]["name"]:
    if message.content.lower() == command_messages["add_mission"]:
      print("Add mission command executed by: " + message.author.name)
      await save_attachements(
        message,
        command_messages,
        mission_folder_path,
        bot_messages
        )
    
    elif message.content.lower() == command_messages["clear_messages"]:
      print("Purge messages command executed by: " + message.author.name)
      await purge_channel_messages(
        guild,
        message,
        channel_list
        )

    elif message.content.lower() == command_messages["help"]:
      print("Help command executed by: " + message.author.name)
      await reply_help_message(
        message,
        help_message_template,
        channel_list,
        bot_name,
        server_name
        )

    elif message.content.lower() == command_messages["exit"]:
      await bot_shutdown(
        client,
        message,
        bot_messages,
        bot_startup
        )

    else:
      mission_name = ""
      mission_messages = {}
      for keyword in contract_keywords:
        if message.content.startswith(keyword):
          mission_name = regex_compiler(message, contract_keywords[keyword])
          mission_date = regex_compiler(message, contract_keywords["date"])
  
      if mission_name != "" and int(mission_date) > current_time:
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
        announcements_message = bot_messages["announcements_template"].format(mission_name, mission_date)

        reposted_message = await attendance_channel.send(message.content)
        squad_list_message = await squad_list_channel.send(bot_messages["squad_list_message_init"] + mission_name)

        mission_messages = {
          "mission_name": mission_name,
          "mission_date": mission_date,
          "reposted_message": reposted_message,
          "squad_list_message": squad_list_message,
          "squad_list": {}
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

      elif mission_name != "" and int(mission_date) <= current_time:
        reply = await message.reply(bot_messages["incorrect_time"])
        await asyncio.sleep(20)
        await reply.delete()
        await message.delete()


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
          information = await reaction_added(
            emoji_list,
            emoji_filter,
            information,
            squad_list_message,
            event_member_name
            )


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
        information = await reaction_deleted(
          emoji_list,
          emoji_filter,
          information,
          squad_list_message,
          reposted_message
          )



# #########################################################################
# Bot start
# #########################################################################

client.run(bot_token)