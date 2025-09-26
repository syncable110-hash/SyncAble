import random
import copy
import math
import json
import os
from colorama import Fore, Style, init
from datetime import date, timedelta, datetime

# NEW: Import libraries for holiday detection
import holidays
from dateutil.parser import parse

# Initialize colorama
init(autoreset=True)

# --- Global Configuration (will be overridden by the config from the server) ---
DAYS = []
TIMESLOTS = []
SEMESTER_WEEKS = 15
CONTRACTED_HOURS = {}
COURSE_LOAD = {}
SUBJECTS = {}
TEACHERS = {}
TEACHER_AVAILABILITY = {}
ROOMS = {}
BATCHES = []

# ==============================================================================
#                               MAIN BACKEND FUNCTION (HEAVILY MODIFIED)
# ==============================================================================
def generate_timetable_from_config(config: dict, day_dates: dict, remaining_hours: dict = None, dynamic_constraints: dict = None):
    """
    High-level function called by the server. It's now stateless and robust.
    It takes a configuration, specific dates, and remaining hours, runs the
    generation process, and returns a dictionary with both raw and formatted results.
    """
    # Override global variables with the provided config.
    global DAYS, TIMESLOTS, SEMESTER_WEEKS, CONTRACTED_HOURS, COURSE_LOAD, SUBJECTS, TEACHERS, TEACHER_AVAILABILITY, ROOMS, BATCHES

    DAYS = config.get("DAYS", [])
    TIMESLOTS = config.get("TIMESLOTS", [])
    SEMESTER_WEEKS = config.get("SEMESTER_WEEKS", 15)
    CONTRACTED_HOURS = config.get("CONTRACTED_HOURS", {})
    COURSE_LOAD = config.get("COURSE_LOAD", {})
    SUBJECTS = config.get("SUBJECTS", {})
    TEACHERS = config.get("TEACHERS", {})
    TEACHER_AVAILABILITY = config.get("TEACHER_AVAILABILITY", {})
    ROOMS = config.get("ROOMS", {})
    BATCHES = config.get("BATCHES", [])

    # --- Start of generation logic ---
    monday_date_str = day_dates.get("Monday")
    if not monday_date_str:
        return None # Cannot proceed without a start date
    start_of_week = date.fromisoformat(monday_date_str)

    dynamic_constraints = check_for_holidays(start_of_week, country_code='IN')

    if remaining_hours is None:
        current_remaining_hours = copy.deepcopy(CONTRACTED_HOURS)
    else:
        current_remaining_hours = copy.deepcopy(remaining_hours)

    week_number = 1

    final_timetable_raw = run_genetic_algorithm(current_remaining_hours, week_number, dynamic_constraints)

    if final_timetable_raw:
        # ### FIX ###
        # Firestore cannot save dictionaries that have tuples as keys.
        # To fix this, we convert the tuple keys e.g., ('Monday', '9-10', 'Batch_A')
        # into a single string e.g., "Monday|9-10|Batch_A".
        firestore_safe_raw = {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in final_timetable_raw.items()}

        return {
            # IMPORTANT: The 'raw' key now contains string keys to be Firestore-compatible.
            # The HourTracker class in 'agent.py' MUST be updated to handle this.
            # The line in `update_after_week`:
            #   _, _, batch = key
            # MUST be changed to:
            #   day, timeslot, batch = key.split('|')
            "raw": firestore_safe_raw,
            "batches": format_timetable_for_json(final_timetable_raw, day_dates)["batches"]
        }
    else:
        return None

def format_timetable_for_json(timetable: dict, day_dates: dict):
    """Converts the timetable from its internal format to a clean, nested JSON structure."""
    json_output = {
        "weekOf": day_dates.get("Monday"),
        "batches": {batch: {day: {} for day in DAYS} for batch in BATCHES}
    }

    for key, value in timetable.items():
        day, timeslot, batch = key
        subject, teacher, room = value

        if batch in json_output["batches"] and day in json_output["batches"][batch]:
            json_output["batches"][batch][day][timeslot] = {
                "subject": subject,
                "teacher": teacher,
                "room": room
            }
    return json_output

# --- Priority System Functions (Made More Robust) ---
def calculate_subject_priorities(batch):
    """Calculates priority scores for subjects, safely handling non-numeric data."""
    batch_subjects = CONTRACTED_HOURS.get(batch, {})
    if not batch_subjects:
        return {}

    # Ensure all values are numeric before processing to prevent TypeErrors.
    numeric_values = [v for v in batch_subjects.values() if isinstance(v, (int, float))]
    if not numeric_values:
        return {} # Return if no valid numbers are found

    max_hours = max(numeric_values)
    min_hours = min(numeric_values)

    priorities = {}
    for subject, hours in batch_subjects.items():
        if not isinstance(hours, (int, float)):
            continue

        if max_hours == min_hours:
            priorities[subject] = 1.0
        else:
            # This calculation is now safe from TypeErrors and ZeroDivisionErrors
            normalized_priority = 0.3 + 0.7 * (hours - min_hours) / (max_hours - min_hours)
            priorities[subject] = normalized_priority
    return priorities


def get_priority_ordered_subjects(batch, remaining_hours):
    priorities = calculate_subject_priorities(batch)
    batch_remaining = remaining_hours.get(batch, {})

    subject_info = []
    for subject in COURSE_LOAD.get(batch, {}):
        priority = priorities.get(subject, 0.5)
        contracted_total = CONTRACTED_HOURS.get(batch, {}).get(subject, 0)
        remaining = batch_remaining.get(subject, contracted_total)

        adjusted_priority = priority * (1 + remaining / 100)
        subject_info.append((subject, adjusted_priority, remaining))

    subject_info.sort(key=lambda x: (-x[1], -x[2]))
    return subject_info

# --- State Management (No longer used by the main API function, but kept for standalone runs) ---
STATE_FILE = "timetable_state.json"
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_state(start_of_week_date):
    state = {'last_monday_date': start_of_week_date.strftime('%Y-%m-%d')}
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)
    except IOError:
        pass

# --- Holiday Detection ---
def check_for_holidays(start_of_week, country_code='IN'):
    holiday_days = []
    country_holidays = holidays.country_holidays(country_code)
    for i in range(5):
        current_date = start_of_week + timedelta(days=i)
        if current_date in country_holidays:
            holiday_days.append(current_date.strftime('%A'))
    return {"holiday_days": holiday_days}

# --- Genetic Algorithm Core (Made More Robust) ---
def is_teacher_available(teacher, timeslot):
    return timeslot in TEACHER_AVAILABILITY.get(teacher, [])

def create_random_timetable(remaining_hours: dict, week_num: int, dynamic_constraints: dict = None):
    dynamic_constraints = dynamic_constraints or {}
    holiday_days = dynamic_constraints.get("holiday_days", [])
    unavailable_teachers = dynamic_constraints.get("unavailable_teachers", []) # For agent requests

    teacher_assignments = {}
    for batch in BATCHES:
        for subject in COURSE_LOAD.get(batch, {}):
            possible_teachers = [t for t, subs in TEACHERS.items() if subject in subs]
            if not possible_teachers:
                print(f"Error: No teacher found for subject: {subject}")
                continue
            teacher_assignments[(batch, subject)] = random.choice(possible_teachers)

    timetable = {}
    for batch in BATCHES:
        priority_subjects = get_priority_ordered_subjects(batch, remaining_hours)
        for subject, _, remaining in priority_subjects:
            is_lab = SUBJECTS.get(subject, {}).get("is_lab", False)
            num_slots_per_session = 2 if is_lab else 1

            min_hours = COURSE_LOAD.get(batch, {}).get(subject, 1)
            rem_hrs = remaining_hours.get(batch, {}).get(subject, 0)
            weeks_left = max(1, SEMESTER_WEEKS - week_num + 1)
            target_hours = math.ceil(rem_hrs / weeks_left)
            hours_to_schedule = max(min_hours, target_hours)
            sessions_to_schedule = (hours_to_schedule + num_slots_per_session - 1) // num_slots_per_session

            scheduled_sessions = 0
            for _ in range(300): # Attempts to schedule
                if scheduled_sessions >= sessions_to_schedule:
                    break

                teacher_key = (batch, subject)
                if teacher_key not in teacher_assignments:
                    continue
                teacher = teacher_assignments[teacher_key]

                room_type = "Lab" if is_lab else "Lecture"
                possible_rooms = [r for r, d in ROOMS.items() if d["type"] == room_type]
                if not possible_rooms: continue

                day = random.choice(DAYS)
                # Apply constraints
                if day in holiday_days: continue
                is_teacher_unavailable = any(
                    entry["teacher"] == teacher and day in entry["days"] for entry in unavailable_teachers
                )
                if is_teacher_unavailable: continue

                max_slot_index = len(TIMESLOTS) - num_slots_per_session
                if max_slot_index < 0: continue

                start_slot_index = random.randint(0, max_slot_index)
                if not is_teacher_available(teacher, TIMESLOTS[start_slot_index]):
                    continue

                slots_are_free = all((day, TIMESLOTS[start_slot_index + i], batch) not in timetable for i in range(num_slots_per_session))

                if slots_are_free:
                    room = random.choice(possible_rooms)
                    for i in range(num_slots_per_session):
                        ts = TIMESLOTS[start_slot_index + i]
                        timetable[(day, ts, batch)] = (subject, teacher, room)
                    scheduled_sessions += 1
    return timetable


def calculate_fitness(timetable: dict, dynamic_constraints: dict = None):
    conflicts = 0
    occupied = {}
    teacher_gaps = {}

    for key, value in timetable.items():
        if not (isinstance(key, tuple) and len(key) == 3 and isinstance(value, tuple) and len(value) == 3):
            conflicts += 10; continue

        day, timeslot, batch = key
        _, teacher, room = value
        slot_key = (day, timeslot)

        occupied.setdefault(slot_key, {"teachers": set(), "rooms": set(), "batches": set()})

        if teacher in occupied[slot_key]["teachers"]: conflicts += 1
        if room in occupied[slot_key]["rooms"]: conflicts += 1
        if batch in occupied[slot_key]["batches"]: conflicts += 1

        occupied[slot_key]["teachers"].add(teacher)
        occupied[slot_key]["rooms"].add(room)
        occupied[slot_key]["batches"].add(batch)

        teacher_gaps.setdefault(teacher, {}).setdefault(day, []).append(TIMESLOTS.index(timeslot))

    for _, days_data in teacher_gaps.items():
        for _, slot_indices in days_data.items():
            slot_indices.sort()
            for i in range(len(slot_indices) - 1):
                if slot_indices[i+1] - slot_indices[i] > 1:
                    conflicts += 0.5

    return 1 / (1 + conflicts)

def select_parents(population_with_fitness):
    # Tournament selection
    return max(random.sample(population_with_fitness, 5), key=lambda x: x[1])[0]

def crossover(parent1, parent2):
    child = {}
    keys1 = set(parent1.keys())
    keys2 = set(parent2.keys())
    # Inherit common slots from a random parent
    for key in keys1.intersection(keys2):
        child[key] = random.choice([parent1[key], parent2[key]])
    # Inherit unique slots
    for key in keys1.difference(keys2):
        child[key] = parent1[key]
    for key in keys2.difference(keys1):
        child[key] = parent2[key]
    return child

def mutate(timetable, mutation_rate=0.05):
    if random.random() < mutation_rate and len(timetable) > 1:
        key1, key2 = random.sample(list(timetable.keys()), 2)
        timetable[key1], timetable[key2] = timetable[key2], timetable[key1]
    return timetable

def run_genetic_algorithm(remaining_hours: dict, week_num: int, dynamic_constraints: dict = None):
    POPULATION_SIZE, NUM_GENERATIONS = 100, 200 # Reduced for faster API response

    population = [create_random_timetable(remaining_hours, week_num, dynamic_constraints) for _ in range(POPULATION_SIZE)]

    for gen in range(NUM_GENERATIONS):
        population_with_fitness = [(tt, calculate_fitness(tt, dynamic_constraints)) for tt in population]
        best_fitness = max(p[1] for p in population_with_fitness)

        if (gen + 1) % 50 == 0:
            print(f"Generation {gen+1:03} | Best Fitness: {best_fitness:.4f}")

        if best_fitness == 1.0:
            print(f"Found a perfect timetable in generation {gen+1}!")
            return max(population_with_fitness, key=lambda x: x[1])[0]

        elites_count = POPULATION_SIZE // 10
        elites = [p[0] for p in sorted(population_with_fitness, key=lambda x: x[1], reverse=True)[:elites_count]]
        next_population = elites

        while len(next_population) < POPULATION_SIZE:
            p1 = select_parents(population_with_fitness)
            p2 = select_parents(population_with_fitness)
            child = crossover(p1, p2)
            mutate(child)
            next_population.append(child)

        population = next_population

    return max(population, key=lambda tt: calculate_fitness(tt, dynamic_constraints))

# --- Main Execution Block (for standalone testing) ---
if __name__ == '__main__':
    state = load_state()
    last_monday_str = state.get('last_monday_date')

    if last_monday_str:
        start_of_week = date.fromisoformat(last_monday_str) + timedelta(days=7)
    else:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())

    DAY_DATES_main = {day: (start_of_week + timedelta(days=i)).strftime('%Y-%m-%d') for i, day in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])}

    test_config = {
        "DAYS": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        "TIMESLOTS": ["9-10", "10-11", "11-12", "12-1", "2-3", "3-4"],
        "SEMESTER_WEEKS": 15,
        "CONTRACTED_HOURS": {
             "Batch_A": {"Math": 45, "Physics": 45, "CS_Theory": 30},
             "Batch_B": {"Math": 45, "Chemistry": 45, "CS_Lab": 15},
        },
        "COURSE_LOAD": {
            "Batch_A": {"Math": 3, "Physics": 3, "CS_Theory": 2},
            "Batch_B": {"Math": 3, "Chemistry": 3, "CS_Lab": 1},
        },
        "SUBJECTS": { "Math": {"is_lab": False}, "Physics": {"is_lab": False}, "Chemistry": {"is_lab": False}, "CS_Theory": {"is_lab": False}, "CS_Lab": {"is_lab": True} },
        "TEACHERS": { "Mr. Alpha": ["Math", "Physics"], "Ms. Beta": ["Chemistry"], "Dr. Gamma": ["CS_Theory", "CS_Lab"]},
        "TEACHER_AVAILABILITY": { "Mr. Alpha": ["9-10", "10-11"], "Ms. Beta": ["9-10", "10-11"], "Dr. Gamma": ["9-10", "10-11"]},
        "ROOMS": { "R101": {"type": "Lecture"}, "L201": {"type": "Lab"}},
        "BATCHES": ["Batch_A", "Batch_B"]
    }

    # The call here will now work correctly as remaining_hours defaults to None
    final_timetable_result = generate_timetable_from_config(test_config, DAY_DATES_main)

    if final_timetable_result:
        print("Successfully generated timetable from standalone test.")
        # You could pretty-print the result for inspection
        # import json
        # print(json.dumps(final_timetable_result, indent=2))
    else:
        print("Could not generate a valid timetable from standalone test.")

