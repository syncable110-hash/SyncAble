# Save this as main.py
from datetime import date, timedelta
# MODIFIED: Import the new 'check_for_holidays' function
from run import run_genetic_algorithm, display_console_timetable, export_grid_timetables, export_detailed_timetables, check_for_holidays
from agent import HourTracker, process_dynamic_request

def create_weekly_schedule(tracker: HourTracker, week_num: int, dynamic_constraints: dict = None):
    """Generates a weekly schedule using the tracker's current data and any dynamic constraints."""
    print(f"--- Generating schedule for Week {week_num} ---")
    remaining_hours = tracker.get_remaining_hours()
    # Pass dynamic constraints to the algorithm
    timetable = run_genetic_algorithm(remaining_hours, week_num, dynamic_constraints)
    return timetable

if __name__ == "__main__":
    tracker = HourTracker()
    print("Initial State:")
    tracker.print_status()

    # --- Set the starting point for the simulation (current week's Monday) ---
    today = date.today()
    start_of_simulation_week = today - timedelta(days=today.weekday())

    # --- Simulate the first few weeks of the semester ---
    for week in range(1, 5): # Simulate 4 weeks
        print(f"\n{'='*30} PLANNING FOR WEEK {week} {'='*30}")

        # Calculate the specific dates for the current simulated week
        current_week_start_date = start_of_simulation_week + timedelta(weeks=week-1)
        DAY_DATES = {
            day: (current_week_start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        }
        
        # --- Handle Dynamic Events BEFORE generating the final schedule ---
        
        # MODIFIED: Automatically check for holidays for the simulated week
        # This function will print its findings and return a constraints dictionary
        dynamic_constraints = check_for_holidays(current_week_start_date)

        # You can still add other dynamic requests, like a teacher's leave
        if week == 2:
            leave_request = "Dr. Gamma has a conference on Wednesday."
            print(f"Processing manual request: {leave_request}")
            # In a full implementation, you would merge constraints from this request
            # with the holiday constraints. For now, we'll just print it.
            # Example: teacher_constraints = process_dynamic_request(leave_request)
            # Example: dynamic_constraints.update(teacher_constraints)


        # --- Generate the schedule with any constraints found ---
        schedule = create_weekly_schedule(tracker, week, dynamic_constraints)
        
        # --- Finalize and Update ---
        if schedule:
            print(f"\n--- Final Timetable for Week {week} ---")

            # Pass the calculated DAY_DATES to the display and export functions
            display_console_timetable(schedule, DAY_DATES)
            export_grid_timetables(schedule, DAY_DATES)
            export_detailed_timetables(schedule, DAY_DATES)

            tracker.update_after_week(schedule)
            tracker.print_status()
        else:
            print(f"🔴 FAILED to generate a schedule for Week {week}.")
            break
        
        input("\nPress Enter to proceed to the next week...")