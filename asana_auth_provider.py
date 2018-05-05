import collections
import datetime
import logging
import os
import time

import asana

logger = logging.getLogger()

def timestamp_from_string(utc_time_str):
    """
    >>> timestamp_from_string("2015-11-22T08:27:33.684Z")
    1448180853.684
    """
    task_completion_datetime = datetime.datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    # This is a UTC timestamp. Instead of dealing with timezones, we'll just get seconds since epoch.
    # Note that what we're subtracting is also a naive timestamp.
    return (task_completion_datetime - datetime.datetime(1970, 1, 1)).total_seconds()

AsanaAuthenticationProviderConfig = collections.namedtuple(
    'AsanaAuthenticationProviderConfig',
    ['pat', 'project_id', 'single_use_cf_id', 'single_use_reusable_window_s']
)

def config_from_env(env=os.environ):
    return AsanaAuthenticationProviderConfig(
        pat=env['ASANA_PAT'],
        project_id=int(env['PROJECT_ID']),
        single_use_cf_id=int(env['SINGLE_USE_CF_ID']),
        single_use_reusable_window_s=300
    )

class AsanaAuthenticationProvider(object):
    name = "AsanaAuthenticationProvider"

    def __init__(self, config):
        self._config = config
        self._client = asana.Client.access_token(self._config.pat)

    def _is_single_use(self, task):
        return any(
            cf['id'] == self._config.single_use_cf_id and cf['enum_value'] is not None
            for cf in task['custom_fields']
        )

    def _represents_valid_code(self, task, code):
        now = time.time()
        if task["name"].endswith(":") or task["name"] == "":
            return False
        if task["name"] != code:
            return False
        if task["completed_at"] is None:
            return True
        elif not self._is_single_use(task):
            # multi-use codes should die as soon as completed, since they must have been completed in the app.
            return False
        else:
            completion_age = now - timestamp_from_string(task["completed_at"])
            return completion_age <= self._config.single_use_reusable_window_s

    def _find_task(self, code):
        # Unclear what to do for due at vs due on. In particular, if a code is due on Monday, the code should expire at the end
        # of Monday; but if it's due at Monday at midnight, then it should expire immediately after that.
        code_tasks = self._client.projects.tasks(self._config.project_id, fields=["id", "name", "custom_fields", "completed_at"])
        for task in code_tasks:
            if self._represents_valid_code(task, code):
                logger.info("Matching task found: {}".format(task))
                return task
        logger.info("No matching task found.")

    def _record_usage(self, task):
        if self._is_single_use(task) and task["completed_at"] is None:
            logger.info("Marking {} complete.".format(task["id"]))
            self._client.tasks.update(task["id"], completed=True)

    def use_code(self, code):
        task = self._find_task(code)
        if task:
            self._record_usage(task)
            return True
        return False

if __name__ == "__main__":
    import doctest
    doctest.testmod()
