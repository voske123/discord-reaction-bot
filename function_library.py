# #########################################################################
# Imports
# #########################################################################

import re
import discord
import requests
import asyncio
import base64
import json
import datetime



# #########################################################################
# Helper Function
# #########################################################################

def get_server_ids(base_api_url, headers, server_name):
  '''
  Function to save all the id's from the guild the bot is joined.

  PARAMS
  - base_api_url
  - headers
  - server_name
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

  PARAMS
  - base_api_url
  - headers
  - server_id
  '''
  emoji_count = 0
  emoji_list = {
    "Zeus"    : "",
    "Command" : "",
    "SL"      : "",
    "Medic"   : "",
    "Pilot"   : "",
    "MSC"     : "",
    "Maybe"   : ""
    }
  emojis_url = f"{base_api_url}/guilds/{server_id}/emojis"
  emojis = requests.get(emojis_url, headers=headers)

  if emojis.status_code == 200:
    emojis = emojis.json()

  for custom_emoji in emojis:
    emoji_count = emoji_count + 1

  if emoji_count >= (50 - len(emoji_list)):
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


def create_custom_emoji(base_api_url, headers, server_name, bot_token):
  '''
  Function to create the custom emoji's if necesary

  PARAMS
  - base_api_url
  - headers
  - server_name
  - bot_token
  '''
  server_ids = get_server_ids(base_api_url, headers, server_name)
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

  PARAMS
  - message
  - key
  '''
  regex = re.compile(key)
  if key.startswith("Additional mods: (.*)"):
    text = re.findall(regex, message.content)
  elif key.startswith("Air Support: "):
    text = re.findall(regex, message.content)
  else:
    text = re.findall(regex, message.content)[0]
  return text


async def check_category(guild, channel_list):
  '''
  Function to check if the necesary categories are on the server

  PARAMS
  - guild
  - channel_list
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


async def check_channels(guild, channel_list):
  '''
  Function to check if the necesary channels are on the server

  PARAMS
  - guild
  - channel_list
  '''
  await check_category(guild, channel_list)

  for channel in channel_list:
    channel_exists = False
    category = discord.utils.get(guild.categories, name=channel_list[channel]["category"])
    for existing_channel in category.text_channels:
      existing_channel = str(existing_channel)
      if channel_list[channel]["name"] == existing_channel:
        channel_exists = True
        break
      
    if channel_exists == False:
      channel_name = channel_list[channel]["name"]
      channel_position = channel_list[channel]["position"]
      channel_topic = channel_list[channel]["topic"]

      print(f"Channel: {channel_name} is being created in Category: {category}")
      await category.create_text_channel(name=channel_name, position=channel_position, topic=channel_topic)
    else:
      print(f"Channel: {channel_list[channel]['name']} exists in Category: {channel_list[channel]['category']}")


async def send_squad_lists(squad_lists, squad_list_message, mission_name):
  '''
  Function to adjust the squad list message with the signed up users.

  PARAMS
  - squad_lists
  - squad_lists_message
  - mission_name
  '''
  message_content = [
    '**Squad list for Mission: **'  + mission_name + "\n\n"
    ]
  total_player_count = 0
  for reaction in squad_lists:
    name = reaction.split("_")[0]
    if len(squad_lists[reaction]) >= 1:
      total_player_count = total_player_count + len(squad_lists[reaction])
      message_content.append(
        f'**{name}**: ' + ' '.join(squad_lists[reaction]) + "." + "\n"
        )

  message_content.append(
    '\n**Total attendance**: ' + str(total_player_count)
    )

  message_content = ''.join(tuple(message_content))

  await asyncio.sleep(1)
  await squad_list_message.edit(content=message_content)


async def get_channel(guild, category_name, channel_name):
  '''
  Function to get the channel from a channel name

  PARAMS
  - guild
  - category_name
  - channel_name
  '''
  try:
    category = discord.utils.get(guild.categories, name=category_name)
    channel = discord.utils.get(category.channels, name=channel_name)
  except AttributeError:
    channel = guild.get_channel(channel_name)

  return channel


async def get_message(guild, category_name, channel_name, message_id):
  '''
  Function to get a message from a message id

  PARAMS
  - guild
  - category_name
  - channel_name
  - message_id
  '''
  channel = await get_channel(guild, category_name, channel_name)
  message = await channel.fetch_message(message_id)

  return message


async def reaction_added(guild, emoji_list, event, information, squad_list_message):
  '''
  Function to check what emoji got added and adjust the reacted lists

  PARAMS
  - guild
  - emoji_list
  - event
  - information
  - squad_list_message
  '''
  emoji_filter = (":"+str(event.emoji.name)+":"+str(event.emoji.id))
  message = await get_message(guild, "", event.channel_id, event.message_id)

  for emoji in emoji_list:
    if emoji_filter == emoji_list[emoji]:
      emoji_reacted = emoji + "_reacted"
      member_exists = False
      for _, members in information["squad_list"].items():
        if event.member.name in members:
          member_exists = True

      if member_exists == False:
        try:
          information["squad_list"][emoji_reacted].append(event.member.name)
        except KeyError:
          information["squad_list"][emoji_reacted] = []
          information["squad_list"][emoji_reacted].append(event.member.name)
      
        print(f"Added {event.member.name} to the {emoji_reacted} list for mission: {information['mission_name']}.")
        await send_squad_lists(
          information["squad_list"],
          squad_list_message,
          information['mission_name']
          )
      else:
        await message.remove_reaction(emoji_filter, event.member)

  return information


async def reaction_deleted(emoji_list, event, information, squad_list_message, reposted_message):
  '''
  Function to check what emoji got removed and adjust the reacted lists

  PARAMS
  - emoji_list
  - emoji_filter
  - information
  - squad_list_message
  - reposted_message
  '''

  emoji_filter = (":"+str(event.emoji.name)+":"+str(event.emoji.id))

  for emoji in emoji_list:
    for reaction in reposted_message.reactions:
      reaction_emoji = (":"+str(reaction.emoji.name)+":"+str(reaction.emoji.id))
      if emoji_filter == emoji_list[emoji] and emoji_filter == reaction_emoji:
        emoji_reacted = emoji+"_reacted"
        async for user in reaction.users():

          try:
            information["squad_list"][emoji_reacted]
          except KeyError:
            break

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


async def old_missions(attendance_channel, squad_list_channel, mission_list, emoji_list, current_time, contract_keywords, bot_name):
  '''
  Function to check old messages on startup.
  If the mission time < 3 weeks before current time then the mission is saved in the mission_list.
  
  PARAMS
  - attendance_channel
  - squad_list_channel
  - mission_list
  - emoji_list
  - current_time
  - contract_keywords
  - bot_name
  '''
  mission_count = 0
  async for reposted_message in attendance_channel.history(limit=50, oldest_first=True):
    reposted_message_created = round(datetime.datetime.timestamp(reposted_message.created_at))
    if reposted_message.author.name == bot_name:
      for keyword in contract_keywords:
        if reposted_message.content.startswith(keyword):
          mission_name = regex_compiler(reposted_message, contract_keywords[keyword])
          mission_date = regex_compiler(reposted_message, contract_keywords["date"])
          async for squad_list_message in squad_list_channel.history(limit=50, oldest_first=True):
            squad_list_message_created = round(datetime.datetime.timestamp(squad_list_message.created_at))
            if (reposted_message_created <= squad_list_message_created) and (reposted_message_created + 10 > squad_list_message_created):
              if int(mission_date) < (current_time - 1814400):
                await squad_list_message.delete()
              else:
                mission_messages = {
                  "mission_name": mission_name,
                  "mission_date": mission_date,
                  "reposted_message": reposted_message,
                  "squad_list_message": squad_list_message,
                  "squad_list": {}
                  }

                for emoji in emoji_list:
                  for reaction in reposted_message.reactions:
                    reaction_emoji = (":"+str(reaction.emoji.name)+":"+str(reaction.emoji.id))
                    if reaction_emoji == emoji_list[emoji]:
                      emoji_reacted = emoji+"_reacted"
                      async for user in reaction.users():
                        if not (user.name == bot_name):
                          try:
                            mission_messages["squad_list"][emoji_reacted].append(user.name)
                          except KeyError:
                            mission_messages["squad_list"][emoji_reacted] = []
                            mission_messages["squad_list"][emoji_reacted].append(user.name)

                mission_list += [{mission_count:mission_messages}]
                await send_squad_lists(mission_messages["squad_list"], squad_list_message, mission_name)
                mission_count += 1

  return mission_list


async def reply_message(message, ttl, content):
  '''
  Function to save mission file to the correct folder on the server with !add_mission command.

  PARAMS
  - message
  - time to live (in seconds)
  - content
  '''
  reply = await message.reply(content)
  await asyncio.sleep(ttl)
  await reply.delete()
  await asyncio.sleep(1)
  await message.delete()


async def save_attachements(message, command_messages, mission_folder_path, bot_messages):
  '''
  Function to save mission file to the correct folder on the server with !add_mission command.

  PARAMS
  - message
  - command_messages
  - mission_folder_path
  - bot_messages
  '''
  if len(message.attachments) > 0:
    for role in message.author.roles:
      role_found = False
      if role.name == "Mission_Upload":
        role_found = True
        break
      
    if role_found == True:
      for attachment in message.attachments:
        if attachment.url.endswith('.pbo'):
          path = f"{mission_folder_path}\\{attachment.filename}"         
          try:
            with open(path, "r") as file:
              await reply_message(message, 30, bot_messages["file_exists"])
          except FileNotFoundError:
            await attachment.save(path)
            await reply_message(message, 20, bot_messages["attachement_saved"])
        else:
          await reply_message(message, 30, bot_messages["incorrect_format"])
    else:
      await reply_message(message, 30, bot_messages["insufficient_rights"])
  else:
    await reply_message(message, 30, bot_messages["no_attachments"])


async def purge_channel_messages(guild, message, channel_list):
  '''
  Function to purge all the messages from the 3 predefined channels for testing.

  PARAMS
  - guild
  - message
  - channel_list
  '''
  for role in message.author.roles:
    if role.name == "Admin":
      for channel in channel_list:
        if not (channel_list[channel]["name"] == channel_list["announcements"]["name"]):
          channel_to_purge = await get_channel(
            guild,
            channel_list[channel]["category"],
            channel_list[channel]["name"],
            )
          await channel_to_purge.purge()

  print("All channels purged.")


async def bot_shutdown(client, message, bot_messages, bot_startup):
  '''
  Function to shutdown the bot upon a message.
  
  PARAMS:
  - client
  - message
  - bot_messages
  - bot_startup
  '''
  print("Shutdown command executed by: " + message.author.name)
  try:
    await bot_startup.edit(content=bot_messages["shutdown_message"])
    await message.delete()
    print(bot_messages["shutdown_message"])
    await asyncio.sleep(4)
    await bot_startup.delete()
    await asyncio.sleep(1)
    await client.close()
  except discord.errors.NotFound:
    await message.delete()
    await asyncio.sleep(1)
    exit()


async def create_contract(guild, message, channel_list, bot_messages, mission_list, emoji_list, mission_name, mission_date, extra_mods, pilot_role):
  '''
  Function to reply a help message to a ?help request.

  PARAMS:
  - guild
  - message
  - channel_list
  - bot_messages
  - mission_list
  - emoji_list
  - mission_name
  - mission_date
  '''  
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
  if extra_mods == []:
    announcements_message = bot_messages["announcements_template"].format(mission_name, mission_date)
  else:
    mod_list = []
    for index in range(len(extra_mods)):
      mod_list.append(f"<{extra_mods[index]}>")
    
    announcements_message = bot_messages["announcements_template_mods"].format(mission_name, mission_date, "\n".join(mod_list))

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
    if pilot_role:
      await reposted_message.add_reaction(emoji_list[emoji])
    else:
      if emoji != "Pilot":
        await reposted_message.add_reaction(emoji_list[emoji])

  await announcements_channel.send(announcements_message)

  if mission_list[mission_count] != {}:
    await reply_message(message, 10, bot_messages["contract_accepted"])

