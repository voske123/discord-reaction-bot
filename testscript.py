import datetime


async def mission_date_check(*weekdays):
  days_of_week = {
    'monday': 0,
    'tuesday': 1,
    'wednesday': 2,
    'thursday': 3,
    'friday': 4,
    'saturday': 5,
    'sunday': 6
  }

  weekday_numbers = [days_of_week[d.lower()] for d in weekdays]

  today = datetime.date.today()
  missions = []
  day = 0
  count = 0
  while len(missions) < 10:
    date = today + datetime.timedelta(days=day)
    mission_date = datetime.time(hour=20, minute=0, second=0)
    mission_date = datetime.datetime.combine(date, mission_date)
    mission_time = int(mission_date.timestamp())
    if date.weekday() in weekday_numbers:
      if date == today and datetime.datetime.utcnow().time() >= datetime.time(hour=20, minute=0, second=0):
        pass
      else:
        count +=1
        missions.append({
          "key": count,
          "time": mission_time,
          "zeus": "FREE"
        })
    day += 1
  return missions


async def update_mission_dates(mission_list):
  new_date_list = await mission_date_check("Wednesday", "Friday")
  count = 0
  for missions in mission_list:
    for _,value in missions.items():
      for i in range(len(value)-1, -1, -1):
        if value[i]["time"] < new_date_list[0]["time"]:
          del value[i]
          count += 1
  
      for i in range(len(value)):
        value[i]["key"] -= count

      for new_date in new_date_list:
        found = False
        for mission in value:
          if mission["time"] == new_date["time"]:
            found = True
            break
        if not found:
          value.append({
            "key": len(value) + 1,
            "time": new_date["time"],
            "zeus": "FREE"
          })
  

mission_list = [{
  0: [
  {"key": 1, "time": 1677092400, "zeus": "Voske_123"},
  {"key": 2, "time": 1677265200, "zeus": "FREE"},
  {"key": 3, "time": 1677697200, "zeus": "FREE"},
  {"key": 4, "time": 1677870000, "zeus": "Voske_123"},
  {"key": 5, "time": 1678302000, "zeus": "FREE"},
  {"key": 6, "time": 1678474800, "zeus": "FREE"},
  {"key": 7, "time": 1678906800, "zeus": "Voske_123"},
  {"key": 8, "time": 1679079600, "zeus": "FREE"},
  {"key": 9, "time": 1679511600, "zeus": "FREE"},
  {"key": 10, "time": 1679684400, "zeus": "FREE"}
  ]
}]





update_mission_dates(mission_list)
print(mission_list)