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
    },
  "zeus-planning":
    {
      "category":"SPECIALIST CHANNELS",
      "name":"zeus-planning",
      "position":4,
      "topic":"Here is the planning for the zeus missions being discussed."
    }
  }
mission_list = []
mission_count = 0
date_counter = 10
mission_folder_path = "E:\Games\ArmA3\A3Master\mpmissions"

contract_keywords = {
  "Contract ": r"(Contract .*)",
  "Operation ": r"(Operation .*)",
  "**Contract ": r"..(Contract .*)..",
  "**Operation ": r"..(Operation .*)..",
  "_date": r"Date: <t:(.*):F>",
  "_additional_mods": r"Additional mods: (.*)",
  "_air_assets": r"Air Assets: ",
  "_slot_number": r"!.* (.*)",
  }
command_messages = {
  "help": "!help",
  "exit": "!exit",
  "add_mission": "!add_mission",
  "clear_messages": "!clear_messages",
  "zeus_slots": "!missions",
  "take_zeus_slot": "!take",
  "remove_zeus_slot": "!remove",
  }

bot_startup = ""
help_message_template = (
  f"{bot_name} has the following commands:"+
  f"\n\n\t**{command_messages['help']}**: Shows this help message."+
  f"\n\t**{command_messages['exit']}**: Shuts the bot down (admin only in {channel_list['zeus-setup']['name']})."+
  f"\n\t**{command_messages['add_mission']}**: Upload a mission to the server (Mission_Upload role in {channel_list['zeus-setup']['name']})."+
  f"\n\t**{command_messages['clear_messages']}**: Clears all messages in **{channel_list['zeus-setup']['name']}**, **{channel_list['squad-list']['name']}**, **{channel_list['attendance']['name']}** (admin only)."+
  f"\n\nInner working of the bot:"+
  f"\n\nIn the {channel_list['zeus-setup']['name']} you can setup a contract with the following syntax:"+
  f"\n\tStart of the message with one of the following options: Contract (PMC OP) or Operation (Side OP) + a mission name. These can be in normal or in **markdown**."+
  f"\n\tSecond line of the message need to be the date with the hammertime syntax: Date: <t:time:F>."+
  f"\n\tThe rest of the message can be own formatting, just make sure everything is in one post."+
  f"\n\nThe bot will automatically add the message in attendance, add the reactions to the message and posts an attendance with the mission name and date."+
  f"\nUpon adding or removing reactions on the message the squadlist will be dynamically build in the **{channel_list['squad-list']['name']}**."
  )
bot_messages = {
  "bot_startup_message": f"The bot is active now, type '{command_messages['help']}' for help.",
  "shutdown_message": "The bot will shutdown in 5 seconds.",
  "squad_list_message_init": "Squad list waiting to be build for mission: ",
  "announcements_template": "@everyone The attendance for **{}** on <t:{}:F> is up! Please make sure to mark if you plan to attend.",
  "announcements_template_mods": "@everyone The attendance for **{}** on <t:{}:F> is up!\nDont forget to download and load the extra mods:\n{}\nPlease make sure to mark if you plan to attend.",
  "contract_accepted": "The contract is correctly formatted and is now ready to be used.\nThis message autodeletes.",
  "file_exists": "This mission is already on the server, please give the mission a different name.\nThis message autodeletes.",
  "incorrect_format": "Please upload a correct missionfile for arma3 (.pbo file).\nThis message autodeletes.",
  "incorrect_time": "You have entered an incorrect Date for this mission, its starting time is older than the current time.\nThis message autodeletes.",
  "incorrect_time_format": "You have entered an incorrect Date for this mission, please use the hammertime format: <t:time:F>.\n This message autodeletes.",
  "incorrect_name_format": "You have entered an incorrect format for the contract name.\nThis message autodeletes.",
  "attachement_saved": "Mission is saved in the MPmissions folder on the server.\nThis message autodeletes.",
  "no_attachments": "No attachments found in the message, please post a new message with the mission file.\nThis message autodeletes.",
  "insufficient_rights": "Please contact an administrator, it seems that you don't have the necesary role to upload a mission.\nThis message autodeletes."
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

  PARAMS
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
  zeus_planning_channel = await get_channel(
    guild,
    channel_list["zeus-planning"]["category"],
    channel_list["zeus-planning"]["name"]
    )
  

  mission_list = await old_missions(
    attendance_channel,
    squad_list_channel,
    zeus_planning_channel,
    mission_list,
    emoji_list,
    current_time,
    contract_keywords,
    bot_name,
    date_counter
    )
  
  bot_startup = await zeus_setup_channel.send(bot_messages["bot_startup_message"])


@client.event
async def on_message(message):
  '''
  Bot message recieved

  PARAMS
  - message
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

  elif message.channel.name == channel_list["zeus-planning"]["name"]:
    zeus_planning_channel = await get_channel(
      guild,
      channel_list["zeus-planning"]["category"],
      channel_list["zeus-planning"]["name"]
      )
    
    if message.content.lower() == command_messages["zeus_slots"]:
      await update_mission_dates(mission_list, date_counter)
      await mission_dates_reply(mission_list, message, 30, zeus_planning_channel, command_messages, False)


    elif message.content.lower().startswith(command_messages["take_zeus_slot"]):
      numbers = message.content.split()[1].split(",")
      
      for _, values in mission_list[0].items():
        for value in values:
          for number in numbers:
            if int(value["key"]) == int(number) and value["zeus"] == "FREE":
              value["zeus"] = message.author.name
              break
      await mission_dates_reply(mission_list, message, 30, zeus_planning_channel, command_messages, False)
      

    elif message.content.lower().startswith(command_messages["remove_zeus_slot"]):
      numbers = message.content.split()[1].split(",")

      for _, values in mission_list[0].items():
        if len(values) > 0:
          for value in values:
            for number in numbers:
              if int(number) == int(value["key"]) and value["zeus"] == message.author.name:
                value["zeus"] = "FREE"
                break
      await mission_dates_reply(mission_list, message, 30, zeus_planning_channel, command_messages, False)
      

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
      await reply_message(
        message,
        60,
        help_message_template
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
      for keyword in contract_keywords:
        if message.content.startswith(keyword):
          incorrect_date = True
          mission_name = regex_compiler(message, contract_keywords[keyword])
          try:
            mission_date = regex_compiler(message, contract_keywords["_date"])
            incorrect_date = False
          except IndexError:
            await reply_message(message, 30, bot_messages["incorrect_time_format"])
          try:
            extra_mods = regex_compiler(message, contract_keywords["_additional_mods"])
          except IndexError:
            extra_mods = ""

          pilot = regex_compiler(message, contract_keywords["_air_assets"])
          if pilot != []:
            pilot_role = True
          else:
            pilot_role = False
  
      if mission_name != "" and incorrect_date == False:
        if int(mission_date) > current_time:
          await create_contract(
            guild,
            message,
            channel_list,
            bot_messages,
            mission_list,
            emoji_list,
            mission_name,
            mission_date,
            extra_mods,
            pilot_role
            )
        else:
          await reply_message(
            message,
            30,
            bot_messages["incorrect_time"]
            )
      
      elif mission_name == "":
        await reply_message(
          message,
          30,
          bot_messages["incorrect_name_format"]
          )


@client.event
async def on_raw_reaction_add(event):
  '''
  Bot reaction added

  PARAMS
  - event
  '''
  guild = discord.utils.get(client.guilds, name=server_name)

  if not event.member.name == bot_name:
    for missions in mission_list:
        for key, information in missions.items():
          if key != 0:
            if event.message_id == information["reposted_message"].id:
              squad_list_message = await get_message(
                guild,
                channel_list["squad-list"]["category"],
                channel_list["squad-list"]["name"],
                information["squad_list_message"].id
                )
              information = await reaction_added(
                guild,
                emoji_list,
                event,
                information,
                squad_list_message,
                )


@client.event
async def on_raw_reaction_remove(event):
  '''
  Bot reaction removed

  PARAMS
  - event
  '''
  guild = discord.utils.get(client.guilds, name=server_name)
  
  for missions in mission_list:
    for key, information in missions.items():
      if key != 0:
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
            event,
            information,
            squad_list_message,
            reposted_message
            )



# #########################################################################
# Bot start
# #########################################################################

client.run(bot_token)