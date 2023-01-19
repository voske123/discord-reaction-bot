# npe-eindopdracht-voske123
This is a discordbot created for Network Programming Essentials course Examn.


The main idea behind the bot is to get an output of usernames based on reactions on a Contract message.



## Files needed to run this bot:

`.env = file with the environment variables`

`discord-reaction-bot.py = python script with functionalities of the bot`

`emoji's = folder with the necesary emoji's saved as .png file with the correct name`

`requirements.txt = file with the needed packages to be installed`



## Environmental variables needed in .env file

`DISCORD_TOKEN=<Bot discord Token here>`

`DISCORD_BOT_NAME=<Bot name here>`

`DISCORD_SERVER=<Discord server name here>`



## Discription of the functionality of the bot:
1) Check if the guild has the necesary emoji's, if not then they will be created.
2) The bot will check if the requested category and subchannels exists, if not they will be created.
3) Listen to a message that is not originated by the bot in the channel: "Attendance-Setup" that starts with "Contract " or "Operation ".
4) Repost the content of that message in the channel "Attendance" and add the 6 emoji's as a reaction.
5) Post a custom message in the channel "Squad-list".
5) On a reaction added by a user that is not the bot it will save the username and adjust the message in the channel "Squad-list".
6) On a reaction deleted by a user that is not the bot and already reacted before it will delete the username from the list
   and adjust the message in the channel "Squad-list".

## Extra's

If you post `?help` in any channel you get a DM from the bot with information on how the bot works.

For this functionality to work you need to be able to recieve messages from members of the discord you are a member of.
