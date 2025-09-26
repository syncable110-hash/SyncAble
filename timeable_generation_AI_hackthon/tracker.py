# Save this as tracker.py
import json
import os
import math
from collections import defaultdict

class ScheduleTracker:
    """
    Manages semester-long progress of course hours against contracted hours.
    """
    def __init__(self, filepath='semester_progress.json'):
        self.filepath = filepath
        self.progress_data = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_data(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.progress_data, f, indent=4)

    def initialize_semester(self, enrollment, credits, weeks, subjects_info):
        print("--- 📝 Initializing new semester progress tracker... ---")
        self.progress_data = {}
        for batch, subjects in enrollment.items():
            self.progress_data[batch] = {}
            for subject in subjects:
                weekly_sessions = credits.get(subject, 0)
                is_lab = subjects_info.get(subject, {}).get("is_lab", False)
                hours_per_session = 2 if is_lab else 1
                contracted = weekly_sessions * weeks * hours_per_session
                self.progress_data[batch][subject] = {
                    "contracted_hours": contracted,
                    "completed_hours": 0
                }
        self._save_data()
        print(f"✅ Semester progress initialized and saved to '{self.filepath}'.")

    def get_remaining_hours(self, batch, subject):
        """Calculates the remaining contracted hours for a specific subject and batch."""
        if batch in self.progress_data and subject in self.progress_data[batch]:
            data = self.progress_data[batch][subject]
            return data['contracted_hours'] - data['completed_hours']
        return 0

    def calculate_weekly_targets(self, weeks_remaining):
        """
        Calculates the target number of hours for each subject for the upcoming week
        to stay on track for the rest of the semester.
        """
        if weeks_remaining <= 0:
            return {}
            
        targets = {}
        for batch, subjects in self.progress_data.items():
            targets[batch] = {}
            for subject, data in subjects.items():
                remaining_hours = self.get_remaining_hours(batch, subject)
                # Use ceiling division to schedule more classes if we are behind
                target_hours_this_week = math.ceil(remaining_hours / weeks_remaining)
                targets[batch][subject] = max(0, int(target_hours_this_week))
        return targets

    def update_progress_from_timetable(self, timetable):
        print(f"--- 📊 Updating progress from the latest weekly schedule... ---")
        if not self.progress_data:
            print("⚠️ Tracker is not initialized.")
            return

        weekly_hours = defaultdict(lambda: defaultdict(int))
        for key, value in timetable.items():
            _, _, batch = key
            subject, _, _ = value
            weekly_hours[batch][subject] += 1

        for batch, subjects in weekly_hours.items():
            for subject, hours in subjects.items():
                if subject in self.progress_data.get(batch, {}):
                    self.progress_data[batch][subject]["completed_hours"] += hours
        self._save_data()
        print("✅ Progress updated successfully.")

    def get_status_report(self):
        print("\n--- 📜 SEMESTER PROGRESS REPORT ---")
        if not self.progress_data:
            print("No data available.")
            return

        for batch, subjects in self.progress_data.items():
            print(f"\n{'='*20} {batch} {'='*20}")
            print(f"{'Subject':<15} | {'Completed':<10} | {'Contracted':<10} | Status")
            print("-" * 55)
            for subject, data in sorted(subjects.items()):
                completed = data['completed_hours']
                contracted = data['contracted_hours']
                status = "On Track"
                if completed > contracted:
                    status = "OVER"
                elif contracted > 0 and completed == 0:
                    status = "Not Started"
                print(f"{subject:<15} | {completed:<10} | {contracted:<10} | {status}")