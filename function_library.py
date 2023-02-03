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


def create_custom_emoji(base_api_url, headers, server_name, bot_token):
  '''
  Function to create the custom emoji's if necesary
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
  '''
  regex = re.compile(key)
  text = re.findall(regex, message.content)[0]

  return text


async def check_category(guild, channel_list):
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


async def check_channels(guild, channel_list):
  '''
  Function to check if the necesary channels are on the server
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


async def reaction_added(emoji_list, emoji_filter, information, squad_list_message, event_member_name):
  '''
  Function to check what emoji got added and adjust the reacted lists
  '''
  for emoji in emoji_list:
    if emoji_filter == emoji_list[emoji]:
      emoji_reacted = emoji + "_reacted"
      try:
        information["squad_list"][emoji_reacted].append(event_member_name)
      except KeyError:
        information["squad_list"][emoji_reacted] = []
        information["squad_list"][emoji_reacted].append(event_member_name)
    
      print(f"Added {event_member_name} to the {emoji_reacted} list for mission: {information['mission_name']}.")
      await send_squad_lists(
        information["squad_list"],
        squad_list_message,
        information['mission_name']
        )

  return information


async def reaction_deleted(emoji_list, emoji_filter, information, squad_list_message, reposted_message):
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


async def old_missions(attendance_channel, squad_list_channel, mission_list, emoji_list, current_time, contract_keywords, bot_name):
  '''
  Function to check old messages on startup.
  If the mission time < 3 weeks before current time then the mission is saved in the mission_list.
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
                          mission_messages["squad_list"][emoji_reacted].append(user.name)
                mission_list += [{mission_count:mission_messages}]
                await send_squad_lists(mission_messages["squad_list"], squad_list_message, mission_name)
                mission_count += 1

  return mission_list


async def save_attachements(message, command_messages, mission_folder_path, bot_messages):
  '''
  Function to save mission file to the correct folder on the server with !add_mission command.
  '''
  if len(message.attachments) > 0:
    if message.content.lower() == command_messages["add_mission"]:
      for role in message.author.roles:
        if role.name == "Mission_Upload":
          for attachment in message.attachments:
            if attachment.url.endswith('.pbo'):
              path = f"{mission_folder_path}\\{attachment.filename}"         
              try:
                with open(path, "r") as file:
                  reply = await message.reply(content=bot_messages["file_exists"])
                  await asyncio.sleep(20)
                  await reply.delete()
                  await message.delete()
              except FileNotFoundError:
                await attachment.save(path)
                reply = await message.reply(content=bot_messages["attachement_saved"])
                await asyncio.sleep(5)
                await reply.delete()
                await message.delete()
            else:
              reply = await message.reply(content=bot_messages["incorrect_format"])
              await asyncio.sleep(20)
              await reply.delete()
              await message.delete()
        else:
          reply = await message.reply(content=bot_messages["insufficient_rights"])
          await asyncio.sleep(20)
          await reply.delete()
          await message.delete()
  else:
    reply = await message.reply(content=bot_messages["no_attachments"])
    await asyncio.sleep(20)
    await reply.delete()
    await message.delete()


async def purge_channel_messages(guild, message, channel_list):
  '''
  Function to purge all the messages from the 3 predefined channels for testing.
  '''
  for role in message.author.roles:
    if role.name == "Admin":
      for channel in channel_list:
        if channel.name != channel_list["announcements"]["name"]:
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
  '''
  print("Shutdown command executed by: " + message.author.name)
  await bot_startup.edit(content=bot_messages["shutdown_message"])
  await message.delete()
  print(bot_messages["shutdown_message"])
  await asyncio.sleep(4)
  await bot_startup.delete()
  await asyncio.sleep(1)
  await client.close()


async def reply_help_message(message, help_message_template, channel_list, bot_name, server_name):
  '''
  Function to reply a help message to a ?help request.
  '''
  help_message_content = help_message_template.format(
    bot_name,
    server_name,
    channel_list['zeus-setup']['name'],
    channel_list['squad-list']['name']
  )

  reply = await message.reply(help_message_content)
  await asyncio.sleep(30)
  await reply.delete()
  await message.delete()

