import os
import traceback
import csv
import io
import copy

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from firebase_admin import auth
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date, timedelta
from google.cloud.firestore_v1.base_query import FieldFilter

# --- Initialization ---
load_dotenv()

try:
    # IMPORTANT: Ensure your serviceAccountKey.json is in the same directory
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase Admin SDK initialized successfully.")
except Exception as e:
    db = None
    print(f"🔥 Firebase Admin SDK initialization failed: {e}")

# Import necessary components from your other files
from run import generate_timetable_from_config, CONTRACTED_HOURS
from agent import process_dynamic_request, HourTracker


app = Flask(__name__)

# --- Security & CORS Configuration ---
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173", "null"]}})


# --- Authentication Endpoints (Unchanged) ---
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or not all(k in data for k in ['email', 'password', 'role']):
        return jsonify({"error": "Missing email, password, or role"}), 400
    try:
        user = auth.create_user(email=data['email'], password=data['password'])
        profile_data = {
            "email": data['email'],
            "role": data.get('role', 'student').lower(),
            "name": data.get('name', ''),
            "created_at": firestore.SERVER_TIMESTAMP
        }
        collection_name = f"{profile_data['role']}s"
        if db:
            db.collection(collection_name).document(user.uid).set(profile_data)
        return jsonify({"message": "User created successfully", "uid": user.uid}), 201
    except auth.EmailAlreadyExistsError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ['email', 'password']):
        return jsonify({"error": "Missing email or password"}), 400
    try:
        user = auth.get_user_by_email(data['email'])
        custom_token = auth.create_custom_token(user.uid)
        return jsonify({"message": "Custom token created.", "customToken": custom_token.decode('utf-8')}), 200
    except auth.UserNotFoundError:
        return jsonify({"error": "Invalid email or user not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# --- CSV Generation Helper (Unchanged) ---
def _create_multi_week_csv(all_weekly_timetables, config):
    output = io.StringIO()
    writer = csv.writer(output)
    batches = config.get("BATCHES", [])
    days = config.get("DAYS", [])
    timeslots = config.get("TIMESLOTS", [])
    if not batches or not all_weekly_timetables: return ""
    for week_num, weekly_data in enumerate(all_weekly_timetables, 1):
        timetable = weekly_data['timetable']
        day_dates = weekly_data['dates']
        writer.writerow([])
        writer.writerow([f"====== WEEK {week_num} (Week of {day_dates.get('Monday', '')}) ======"])
        dated_headers = [f"{day} ({day_dates.get(day, '')})" for day in days]
        for batch in sorted(batches):
            writer.writerow([])
            writer.writerow([f'Timetable for {batch}'])
            writer.writerow(['TIME'] + dated_headers)
            batch_schedule = timetable.get("batches", {}).get(batch, {})
            for slot in timeslots:
                row = [slot]
                for day in days:
                    info = batch_schedule.get(day, {}).get(slot)
                    if isinstance(info, dict) and all(k in info for k in ['subject', 'teacher', 'room']):
                        cell = f"{info['subject']} | {info['teacher']} | {info['room']}"
                        row.append(cell)
                    else:
                        row.append("")
                writer.writerow(row)
    return output.getvalue()


# --- Timetable Generation Endpoint (Unchanged) ---
@app.route('/api/generate-and-download', methods=['POST'])
def generate_and_download_timetables():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response("Unauthorized: Missing or invalid token", status=401)
    try:
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
    except Exception as e:
        return Response(f"Authentication error: {e}", status=401)
    config_data = request.get_json()
    if not config_data:
        return Response("Bad Request: Missing configuration data", status=400)
    if 'TEACHERS' in config_data and isinstance(config_data['TEACHERS'], dict):
        config_data['TEACHERS'] = {key.strip(): value for key, value in config_data['TEACHERS'].items()}
    if 'TEACHER_AVAILABILITY' in config_data and isinstance(config_data['TEACHER_AVAILABILITY'], dict):
        config_data['TEACHER_AVAILABILITY'] = {key.strip(): value for key, value in config_data['TEACHER_AVAILABILITY'].items()}
    try:
        today = date.today()
        start_of_simulation = today - timedelta(days=today.weekday())
        all_weeks_data = []
        tracker = HourTracker(filepath=None)
        for week_index in range(4):
            current_week_start_date = start_of_simulation + timedelta(weeks=week_index)
            week_dates = {day: (current_week_start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i, day in enumerate(config_data.get("DAYS", []))}
            print(f"🧠 Generating timetable for Week {week_index + 1}...")
            timetable_result = generate_timetable_from_config(config_data, week_dates, tracker.get_remaining_hours())
            if not timetable_result:
                return Response(f"Failed to generate a valid timetable for Week {week_index + 1}.", status=500)
            tracker.update_after_week(timetable_result['raw'])
            all_weeks_data.append({'timetable': timetable_result, 'dates': week_dates, 'remaining_hours_after': copy.deepcopy(tracker.get_remaining_hours())})
        print("📦 Compiling all weeks into a single CSV file...")
        csv_content = _create_multi_week_csv(all_weeks_data, config_data)
        generation_id = None
        if db:
            log_entry = {'userId': uid, 'status': 'success', 'createdAt': firestore.SERVER_TIMESTAMP, 'inputConfig': config_data, 'weeklyData': all_weeks_data, 'outputCsv': csv_content}
            _, doc_ref = db.collection('generations').add(log_entry)
            generation_id = doc_ref.id
            print(f"✅ Timetable generation saved to Firestore with ID: {generation_id}")
        return Response(csv_content, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=timetable_4_weeks.csv", "X-Generation-ID": generation_id, "Access-Control-Expose-Headers": "X-Generation-ID"})
    except Exception as e:
        print(traceback.format_exc())
        return Response(f"An unexpected server error occurred: {e}", status=500)


# --- Dynamic Request Endpoint (Unchanged) ---
@app.route('/api/dynamic-request', methods=['POST'])
def handle_dynamic_request():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized: Missing or invalid token"}), 401
    try:
        id_token = auth_header.split('Bearer ')[1]
        auth.verify_id_token(id_token)
    except Exception as e:
        return jsonify({"error": f"Authentication error: {e}"}), 401
    data = request.get_json()
    if not data or not all(k in data for k in ['generationId', 'teacher_name', 'unavailable_days', 'week_num']):
        return jsonify({"error": "Missing 'generationId', 'teacher_name', 'unavailable_days', or 'week_num'"}), 400
    generation_id = data['generationId']
    teacher_name = data['teacher_name']
    unavailable_days = data['unavailable_days']
    week_num = data['week_num']
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    try:
        doc_ref = db.collection('generations').document(generation_id)
        doc = doc_ref.get()
        if not doc.exists: return jsonify({"error": "Generation record not found"}), 404
        generation_data = doc.to_dict()
        if 'inputConfig' not in generation_data or 'weeklyData' not in generation_data:
            return jsonify({"error": "This timetable was saved in an old format and cannot be modified. Please generate a new one."}), 400
        config_data = generation_data['inputConfig']
        original_weeks_data = generation_data['weeklyData']
        if 'TEACHERS' in config_data and isinstance(config_data['TEACHERS'], dict):
            config_data['TEACHERS'] = {key.strip(): value for key, value in config_data['TEACHERS'].items()}
        if 'TEACHER_AVAILABILITY' in config_data and isinstance(config_data['TEACHER_AVAILABILITY'], dict):
            config_data['TEACHER_AVAILABILITY'] = {key.strip(): value for key, value in config_data['TEACHER_AVAILABILITY'].items()}
        start_hours = copy.deepcopy(CONTRACTED_HOURS) if week_num == 1 else original_weeks_data[week_num - 2]['remaining_hours_after']
        print(f"🔄 Recalculating from Week {week_num} for request: Make {teacher_name} unavailable on {unavailable_days}")
        week_dates = original_weeks_data[week_num - 1]['dates']
        modified_week_timetable = process_dynamic_request(remaining_hours=start_hours, week_num=week_num, teacher_name=teacher_name.strip(), unavailable_days=unavailable_days, day_dates=week_dates, config=config_data)
        if not modified_week_timetable:
            return jsonify({"error": "Failed to generate a valid schedule for the given constraint."}), 500
        new_full_schedule = original_weeks_data[:week_num - 1]
        tracker = HourTracker(filepath=None)
        tracker.remaining_hours = copy.deepcopy(start_hours)
        tracker.update_after_week(modified_week_timetable['raw'])
        new_full_schedule.append({'timetable': modified_week_timetable, 'dates': original_weeks_data[week_num - 1]['dates'], 'remaining_hours_after': copy.deepcopy(tracker.get_remaining_hours())})
        for i in range(week_num, 4):
            print(f"   -> Regenerating subsequent Week {i + 1}...")
            next_week_result = generate_timetable_from_config(config_data, original_weeks_data[i]['dates'], tracker.get_remaining_hours())
            if not next_week_result:
                raise Exception(f"Failed during cascading regeneration of week {i + 1}")
            tracker.update_after_week(next_week_result['raw'])
            new_full_schedule.append({'timetable': next_week_result, 'dates': original_weeks_data[i]['dates'], 'remaining_hours_after': copy.deepcopy(tracker.get_remaining_hours())})
        new_csv_content = _create_multi_week_csv(new_full_schedule, config_data)
        update_payload = {'weeklyData': new_full_schedule, 'outputCsv': new_csv_content, 'updatedAt': firestore.SERVER_TIMESTAMP}
        doc_ref.update(update_payload)
        print(f"✅ Timetable {generation_id} successfully updated in Firestore.")
        return jsonify({"message": "Timetable updated successfully!", "generationId": generation_id}), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"An unexpected server error occurred: {e}"}), 500

# --- ENDPOINT TO GET LATEST TIMETABLE DETAILS ---
@app.route('/api/latest-timetable-details', methods=['GET'])
def get_latest_timetable_details():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
    except Exception as e:
        return jsonify({"error": f"Authentication error: {e}"}), 401

    if not db:
        return jsonify({"error": "Database not configured"}), 500

    try:
        # Query for the most recent timetable for the user
        query = db.collection('generations').where(filter=FieldFilter("userId", "==", uid)).order_by("createdAt", direction="DESCENDING").limit(1)
        docs = query.stream()
        
        latest_doc = next(docs, None)
        if not latest_doc:
            return jsonify({"error": "No timetables found for this user."}), 404
        
        timetable_data = latest_doc.to_dict()
        generation_id = latest_doc.id
        weekly_data = timetable_data.get('weeklyData', [])
        
        teacher_schedule = {}

        for week_index, week_info in enumerate(weekly_data):
            week_num = week_index + 1
            batches = week_info.get('timetable', {}).get('batches', {})

            for batch, days in batches.items():
                for day, slots in days.items():
                    for slot, details in slots.items():
                        if not isinstance(details, dict):
                            continue
                        teacher = details.get('teacher')
                        if not teacher:
                            continue

                        teacher_schedule.setdefault(teacher, {})
                        teacher_schedule[teacher].setdefault(f"Week {week_num}", set()).add(day)

        # Convert sets → lists for JSON
        for teacher, weeks in teacher_schedule.items():
            for week, days in weeks.items():
                teacher_schedule[teacher][week] = sorted(list(days))

        return jsonify({
            "generationId": generation_id,
            "schedule": teacher_schedule
        }), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": f"An unexpected server error occurred: {e}"}), 500

# --- ENDPOINT TO DOWNLOAD THE CSV FOR AN EXISTING TIMETABLE ---
@app.route('/api/download-csv/<generationId>', methods=['GET'])
def download_csv(generationId):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return Response("Unauthorized", status=401)
    try:
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
    except Exception as e:
        return Response(f"Authentication error: {e}", status=401)
    
    if not db:
        return Response("Database not configured", status=500)

    try:
        doc_ref = db.collection('generations').document(generationId)
        doc = doc_ref.get()
        if not doc.exists:
            return Response("Timetable not found", status=404)
        
        data = doc.to_dict()
        # Security check: ensure the user requesting the doc is the one who created it
        if data.get('userId') != uid:
            return Response("Forbidden", status=403)
            
        csv_content = data.get('outputCsv', '')
        
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=timetable_{generationId}.csv"}
        )

    except Exception as e:
        print(traceback.format_exc())
        return Response(f"An unexpected server error occurred: {e}", status=500)


# --- Main execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

