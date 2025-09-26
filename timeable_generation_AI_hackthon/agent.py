import json
import os
import holidays
from collections import defaultdict
from dateutil.parser import parse
from datetime import date, datetime

# Import data and functions from run.py
# MODIFICATION: We only need the main generation function now.
from run import generate_timetable_from_config, CONTRACTED_HOURS

# The HourTracker Agent
class HourTracker:
    def __init__(self, filepath='hour_tracker.json'):
        """Manages the state of remaining contracted hours."""
        self.filepath = filepath
        self.remaining_hours = self._load_data()

    def _load_data(self):
        """Loads remaining hours, handling in-memory or file-based storage."""
        if self.filepath is None:
            # When running in-memory, start with a fresh copy of the hours
            return {k: v.copy() for k, v in CONTRACTED_HOURS.items()} if CONTRACTED_HOURS else {}

        if not os.path.exists(self.filepath):
            print("Tracker file not found. Initializing with full contracted hours.")
            return {k: v.copy() for k, v in CONTRACTED_HOURS.items()} if CONTRACTED_HOURS else {}
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Could not read tracker file. Re-initializing.")
            return {k: v.copy() for k, v in CONTRACTED_HOURS.items()} if CONTRACTED_HOURS else {}

    def _save_data(self):
        """Saves the current state of remaining hours to the file."""
        if self.filepath is not None:
            with open(self.filepath, 'w') as f:
                json.dump(self.remaining_hours, f, indent=4)

    def get_remaining_hours(self):
        """Returns the current dictionary of remaining hours."""
        return self.remaining_hours

    def update_after_week(self, timetable: dict):
        """Counts hours in the timetable and subtracts them from the remaining total."""
        hours_this_week = defaultdict(lambda: defaultdict(int))
        for key, value in timetable.items():
            try:
                # This correctly parses the string key format from run.py
                _, _, batch = key.split('|')
            except ValueError:
                print(f"Warning: Skipping malformed key in timetable: {key}")
                continue

            subject, _, _ = value
            hours_this_week[batch][subject] += 1

        for batch, subjects in hours_this_week.items():
            for subject, hours in subjects.items():
                if subject in self.remaining_hours.get(batch, {}):
                    self.remaining_hours[batch][subject] -= hours

        self._save_data()
        print("\n✅ Tracker updated with hours from the weekly schedule.")


    def print_status(self):
        """Prints a report of the remaining hours."""
        print("\n--- Remaining Contracted Hours ---")
        for batch, subjects in self.remaining_hours.items():
            print(f"\nBatch: {batch}")
            for subject, hours in sorted(subjects.items()):
                print(f"  - {subject:<15}: {hours} hours left")

# --- Core GA Execution & Dynamic Request Functions ---

### THIS IS THE FIX ###
# The function signature is updated to accept the 'config' dictionary.
# This resolves the "unexpected keyword argument" TypeError.
def process_dynamic_request(remaining_hours, week_num, teacher_name: str, unavailable_days: list, day_dates: dict, config: dict):
    """Processes a structured request for a teacher's leave using the provided configuration."""
    print(f"\n🚀 Processing dynamic request for teacher: \"{teacher_name}\" on days: {unavailable_days}")

    # Validation is now performed against the config object passed for this specific request.
    teachers_config = config.get("TEACHERS", {})
    if teacher_name not in teachers_config:
        print(f"🔴 ERROR: Teacher '{teacher_name}' not found in the provided configuration.")
        return None

    if not isinstance(unavailable_days, list) or not unavailable_days:
        print(f"🔴 ERROR: 'unavailable_days' must be a non-empty list.")
        return None

    # Directly create the constraints object from the structured input.
    constraints = {
        "unavailable_teachers": [{
            "teacher": teacher_name,
            "days": unavailable_days
        }]
    }
    
    # This requires that the main generation function can accept dynamic constraints
    return generate_timetable_from_config(
        config=config,
        day_dates=day_dates,
        remaining_hours=remaining_hours,
        dynamic_constraints=constraints
    )

# This function is kept for potential future use but is not part of the primary fix.
def process_holiday_request(remaining_hours, week_num, request: str, country_code: str = 'IN'):
    """
    Detects dates in a request, checks if they are public holidays, and regenerates the timetable.
    """
    print(f"\n🚀 Processing holiday request: \"{request}\"")
    try:
        parsed_result = parse(request, fuzzy=True, default=date.today())
        holiday_date = parsed_result.date() if isinstance(parsed_result, datetime) else parsed_result
        print(f"🔍 Date detected in request: {holiday_date}")
    except (ValueError, TypeError):
        print("🔴 ERROR: Could not detect a valid date in the request.")
        return None

    country_holidays = holidays.country_holidays(country_code)
    holiday_name = country_holidays.get(holiday_date)

    if holiday_name:
        weekday = holiday_date.strftime('%A')
        print(f"✅ Holiday Confirmed: {holiday_date} is '{holiday_name}' ({weekday}).")

        if weekday not in ["Saturday", "Sunday"]:
             # NOTE: This part would need updating to use the config-passing pattern
            pass
    else:
        print(f"INFO: The date {holiday_date} is not a recognized public holiday in {country_code}.")
        return None

