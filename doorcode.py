from base64 import b64decode
import datetime
import os
import time

import asana
import boto3

PAT = os.environ['ASANA_PAT']
PROJECT_ID = 68058660785829
MULTI_USE = "Multi Use:"
SINGLE_USE = "Single Use:"
SINGLE_USE_REUSABLE_WINDOW_S = 300
DIGITS = "Digits"

WRAPPER = '<?xml version="1.0" encoding="UTF-8"?><Response><Pause length="2"/>{}</Response>'

def timestamp_from_string(utc_time_str):
  """
  >>> timestamp_from_string("2015-11-22T08:27:33.684Z")
  1448180853.684
  """
  task_completion_datetime = datetime.datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
  # This is a UTC timestamp. Instead of dealing with timezones, we'll just get seconds since epoch.
  # Note that what we're subtracting is also a naive timestamp.
  return (task_completion_datetime - datetime.datetime(1970, 1, 1)).total_seconds()

def is_single_use(task):
  """
  >>> is_single_use({u'name': u'12345', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Single Use:'}}], u'completed_at': None})
  True
  >>> is_single_use({u'name': u'12345', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Multi Use:'}}], u'completed_at': None})
  False
  """
  section_names = [membership["section"]["name"] for membership in task["memberships"]]
  return SINGLE_USE in section_names

def represents_valid_code(task, code, now_for_testing=None):
  """
  >>> now = 1448261901.005712
  >>> past_datetime_str = u'2015-11-23T01:22:33.000Z'
  >>> recent_datetime_str = u'2015-11-24T06:58:00.000Z'
  >>> represents_valid_code({u'name': u'', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Single Use:'}}], u'completed_at': None}, "", now)
  False
  >>> represents_valid_code({u'name': u'Single Use:', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Single Use:'}}], u'completed_at': None}, "Single Use:", now)
  False
  >>> represents_valid_code({u'name': u'12345', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Single Use:'}}], u'completed_at': None}, "12345", now)
  True
  >>> represents_valid_code({u'name': u'12345', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Single Use:'}}], u'completed_at': None}, "4567", now)
  False
  >>> represents_valid_code({u'name': u'12345', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Single Use:'}}], u'completed_at': past_datetime_str}, "12345", now)
  False
  >>> represents_valid_code({u'name': u'12345', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Single Use:'}}], u'completed_at': recent_datetime_str}, "12345", now)
  True
  >>> represents_valid_code({u'name': u'12345', u'id': 68058660785836, u'memberships': [{u'section': {u'id': 68058660785832, u'name': u'Multi Use:'}}], u'completed_at': recent_datetime_str}, "12345", now)
  False
  """
  now = time.time()
  if now_for_testing is not None:
    now = now_for_testing
  if task["name"].endswith(":") or task["name"] == "":
    return False
  if task["name"] != code:
    return False
  if task["completed_at"] is None:
    return True
  elif not is_single_use(task):
    # multi-use codes should die as soon as completed, since they must have been completed in the app.
    return False
  else:
    completion_age = now - timestamp_from_string(task["completed_at"])
    return completion_age <= SINGLE_USE_REUSABLE_WINDOW_S

def main(event, context):
  print("Starting processing")
  digits = event.get(DIGITS)
  if not digits:
    return WRAPPER.format('<Gather timeout="10" finishOnKey="#"><Say>Please enter a door code, followed by pound.</Say></Gather>')

  client = asana.client.Client(access_token=PAT)
  # Unclear what to do for due at vs due on. In particular, if a code is due on Monday, the code should expire at the end
  # of Monday; but if it's due at Monday at midnight, then it should expire immediately after that.
  code_tasks = client.projects.tasks(PROJECT_ID, fields=["id", "name", "memberships.section.name", "completed_at"])
  for task in code_tasks:
    if represents_valid_code(task, digits):
      break
  else:
    return WRAPPER.format(
        "<Say>Sorry, no matching code found. Got {}.</Say>".format(digits)
    )

  if is_single_use(task) and task["completed_at"] is None:
    client.tasks.update(task["id"], completed=True)
  return WRAPPER.format('<Play digits="9999"/>')

if __name__ == "__main__":
  import doctest
  doctest.testmod()
