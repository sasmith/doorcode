import urlparse

import asana

PAT = "0/974dbc9aa422d2d59d5d2b1dca9df126"
PROJECT_ID = 68058660785829
PERMANENT = "Permanent:"
SINGLE_USE = "Single Use:"
DIGITS = "Digits"

WRAPPER = '<?xml version="1.0" encoding="UTF-8"?><Response><Pause length="2"/>{}</Response>'

def main(event, context):
  print("Starting processing")
  print("event", event)
  print("context", context)
  digits = urlparse.parse_qs(event["data"]).get(DIGITS)
  if not digits:
    return WRAPPER.format('<Gather timeout="10" finishOnKey="#"><Say>Please enter a door code.</Say></Gather>')

  assert len(digits) == 1
  code = digits[0]
  client = asana.client.Client(access_token=PAT)
  code_tasks = client.projects.tasks(PROJECT_ID, fields=["id", "name", "memberships.section.name", "completed"])
  single_use = []
  permanent = []
  matching_code_task = None
  for task in code_tasks:
    if task["name"].endswith(":"):
      continue
    if task["name"] == code:
      matching_code_task = task
    section_names = [membership["section"]["name"] for membership in task["memberships"]]
    if SINGLE_USE in section_names:
      single_use.append(task)
    else:
      permanent.append(task)

  if matching_code_task:
    return WRAPPER.format('<Play digits="9999"/>'.format(matching_code_task["id"]))
  else:
    return WRAPPER.format("<Say>Entered code didn't match to {} single use codes and {} permament codes.</Say>".format(
      len(single_use), len(permanent)))

if __name__ == "__main__":
  print(main({}, {}))
