from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
from contextlib import contextmanager
import json
import os

app = Flask(__name__)
app.secret_key = 'dev'
app.config['SESSION_TYPE'] = 'filesystem'
app.debug = True

WORKOUT_TEMPLATES = {
    'Beginner Upper Body': [
        {'name': 'Bench Press', 'weight': 45, 'sets': 3, 'reps': 10},
        {'name': 'Push Ups', 'weight': 0, 'sets': 3, 'reps': 10},
        {'name': 'Dumbbell Rows', 'weight': 20, 'sets': 3, 'reps': 10}
    ],
    'Beginner Lower Body': [
        {'name': 'Squats', 'weight': 45, 'sets': 3, 'reps': 10},
        {'name': 'Lunges', 'weight': 0, 'sets': 3, 'reps': 10},
        {'name': 'Calf Raises', 'weight': 0, 'sets': 3, 'reps': 15}
    ]
}

# Simplified service communication
def write_to_service(service_name, data):
    """Write data to a service's input file"""
    try:
        filename = f'data/{service_name}_input.txt'
        with open(filename, 'w') as f:
            json.dump(data, f)
        print(f"Data sent to {service_name} service")
    except Exception as e:
        print(f"Error writing to {service_name} service: {e}")

def read_from_service(service_name):
    """Read data from a service's output file"""
    try:
        filename = f'data/{service_name}_output.txt'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading from {service_name} service: {e}")
    return None

@contextmanager
def get_db():
    db = sqlite3.connect('workouts.db')
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

def init_db():
    with get_db() as db:
        db.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY,
            start_time TEXT,
            end_time TEXT,
            notes TEXT
        )''')
        
        db.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY,
            workout_id INTEGER,
            name TEXT,
            weight TEXT,
            sets INTEGER,
            reps INTEGER,
            FOREIGN KEY (workout_id) REFERENCES workouts (id)
        )''')
        db.commit()

def save_workout(workout):
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO workouts (start_time, end_time, notes) VALUES (?, ?, ?)',
            (workout['start_time'], workout['end_time'], workout.get('notes', ''))
        )
        workout_id = cursor.lastrowid
        
        for exercise in workout['exercises']:
            cursor.execute(
                'INSERT INTO exercises (workout_id, name, weight, sets, reps) VALUES (?, ?, ?, ?, ?)',
                (workout_id, exercise['name'], exercise['weight'], exercise['sets'], exercise['reps'])
            )
        db.commit()

def get_workouts():
    with get_db() as db:
        workouts = []
        for row in db.execute('SELECT * FROM workouts ORDER BY id DESC'):
            workout = dict(row)
            workout['exercises'] = []
            for ex in db.execute('SELECT * FROM exercises WHERE workout_id = ?', (row['id'],)):
                workout['exercises'].append(dict(ex))
            workouts.append(workout)
        return workouts

def save_current_workout(workout):
    with open('current_workout.json', 'w') as f:
        json.dump(workout, f)

def load_current_workout():
    try:
        with open('current_workout.json', 'r') as f:
            return json.load(f)
    except:
        return {'exercises': []}

@app.route('/')
def home():
    disclaimers = {
        'data_privacy': 'workouts will be stored locally on your device',
        'time_cost': 'each workout session takes about 30-60 minutes to log properly',
        'auto_save': 'progress auto-saves every 5 minutes'
    }
    return render_template('home.html', 
        workout_count=len(get_workouts()),
        disclaimers=disclaimers)

@app.route('/workout/start', methods=['GET'])
def start_workout():
    session['workout_in_progress'] = True
    session['start_timestamp'] = datetime.now().timestamp()
    session['workout_timer'] = '00:00:00'
    session['last_set_time'] = None

    current_workout = {
        'exercises': [],
        'start_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'notes': '',
        'step': 1,
        'total_steps': 3
    }
    save_current_workout(current_workout)
    return redirect(url_for('add_exercise'))

@app.route('/workout/add-exercise', methods=['GET', 'POST'])
def add_exercise():
    if not session.get('workout_in_progress'):
        return redirect(url_for('home'))

    if session.get('start_timestamp'):
        elapsed = int(datetime.now().timestamp() - session['start_timestamp'])
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        session['workout_timer'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    if request.method == 'POST':
        current_workout = load_current_workout()
        
        template_name = request.form.get('template_select')
        if template_name and template_name in WORKOUT_TEMPLATES:
            current_workout['exercises'].extend(WORKOUT_TEMPLATES[template_name])
            flash(f'Template "{template_name}" loaded!')
            save_current_workout(current_workout)
            return redirect(url_for('add_exercise'))

        if session.get('last_set_time'):
            last_set = datetime.strptime(session['last_set_time'], "%H:%M:%S")
            now = datetime.now()
            rest_time = (now - last_set).seconds
            if rest_time < 90:
                flash(f'Warning: Only {rest_time} seconds rest. Recommended: 90 seconds')

        exercise = {
            'name': request.form.get('exercise_name', 'Custom Exercise'),
            'weight': request.form.get('weight', 'Bodyweight'),
            'sets': int(request.form.get('sets', 3)),
            'reps': int(request.form.get('reps', 10))
        }
        session['last_set_time'] = datetime.now().strftime("%H:%M:%S")
        current_workout['exercises'].append(exercise)
        save_current_workout(current_workout)
        flash('Exercise added! Add another or finish when ready.')
        return redirect(url_for('add_exercise'))

    return render_template('add_exercise.html',
        current_exercises=load_current_workout().get('exercises', []),
        workout_templates=WORKOUT_TEMPLATES,
        workout_start=session.get('workout_start_time'),
        last_set=session.get('last_set_time'))

@app.route('/workout/undo-last', methods=['POST'])
def undo_last_exercise():
    current_workout = load_current_workout()
    if current_workout.get('exercises'):
        removed = current_workout['exercises'].pop()
        save_current_workout(current_workout)
        flash(f'removed {removed["name"]}. try again or continue.')
    return redirect(url_for('add_exercise'))

@app.route('/workout/finish', methods=['POST'])
def finish_workout():
    current_workout = load_current_workout()
    if not current_workout.get('exercises'):
        flash('Add at least one exercise to save your workout!')
        return redirect(url_for('add_exercise'))

    # Get custom date if provided, otherwise use current date
    workout_date = request.form.get('workout_date')
    if workout_date:
        try:
            # Validate date format
            workout_datetime = datetime.strptime(workout_date, '%Y-%m-%d')
            current_workout['start_time'] = workout_datetime.strftime("%Y-%m-%d %H:%M")
            current_workout['end_time'] = workout_datetime.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            flash('Invalid date format. Using current date.')
            current_workout['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    else:
        current_workout['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    current_workout['notes'] = request.form.get('workout_notes', '')
    save_workout(current_workout)
    
    user_id = session.get('user_id', 'default_user')
    
    # 1. Update Streak (Microservice A)
    streak_date = workout_datetime.strftime("%m-%d-%Y") if workout_date else datetime.now().strftime("%m-%d-%Y")
    with open('data/workout_date.txt', 'w') as f:
        f.write(streak_date)
    print(f"Streak Service: Workout date recorded: {streak_date}")
    
    # 2. Create Social Post (Microservice B)
    exercises_summary = ", ".join([ex['name'] for ex in current_workout['exercises']])
    write_to_service('social', {
        'user_id': user_id,
        'content': f'Completed a workout! 💪 Exercises: {exercises_summary}'
    })
    
    # 3. Update Progress Stats (Microservice C)
    write_to_service('progress', {
        'workouts': get_workouts(),
        'current_workout': current_workout
    })
    
    # 4. Create Notification (Microservice D)
    write_to_service('notification', {
        'user_id': user_id,
        'type': 'workout_complete'
    })
    
    if os.path.exists('current_workout.json'):
        os.remove('current_workout.json')
    session.pop('workout_in_progress', None)
    
    flash('Great job! Workout saved. 💪')
    return redirect(url_for('view_history'))

@app.route('/history')
def view_history():
    workouts = get_workouts()
    
    # Send all workouts to progress service
    write_to_service('progress', {
        'workouts': workouts,
        'current_workout': None
    })
    
    # Get progress stats and debug print
    progress_stats = read_from_service('progress') or {}
    print("DEBUG - Progress Stats:", json.dumps(progress_stats, indent=2))
    
    # Get streak from Microservice A
    current_streak = 0
    try:
        with open('data/streak.txt', 'r') as f:
            current_streak = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        pass
    
    # Get social posts from Microservice B
    social_posts = []
    try:
        with open('data/social_posts.json', 'r') as f:
            social_posts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # Get notifications from Microservice D
    notifications = []
    try:
        with open('data/notifications.json', 'r') as f:
            notifications = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
        
    return render_template('history.html', 
        workouts=workouts,
        current_streak=current_streak,
        progress_stats=progress_stats,
        social_posts=social_posts,
        notifications=notifications)

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    init_db()
    app.run(debug=True)
