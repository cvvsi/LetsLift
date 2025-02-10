from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import sqlite3
from contextlib import contextmanager
import json

app = Flask(__name__)
app.secret_key = 'dev'
app.config['SESSION_TYPE'] = 'filesystem'
app.debug = True

# database connection manager
@contextmanager
def get_db():
   db = sqlite3.connect('workouts.db')
   db.row_factory = sqlite3.Row
   try:
       yield db
   finally:
       db.close()

# create database tables if they don't exist
def init_db():
   with get_db() as db:
       # create workouts table
       db.execute('''
       CREATE TABLE IF NOT EXISTS workouts (
           id INTEGER PRIMARY KEY,
           start_time TEXT,
           end_time TEXT,
           notes TEXT
       )''')
       
       # create exercises table with foreign key to workouts
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

# save completed workout to database
def save_workout(workout):
   with get_db() as db:
       cursor = db.cursor()
       # save workout details
       cursor.execute(
           'INSERT INTO workouts (start_time, end_time, notes) VALUES (?, ?, ?)',
           (workout['start_time'], workout['end_time'], workout.get('notes', ''))
       )
       workout_id = cursor.lastrowid
       
       # save each exercise for this workout
       for exercise in workout['exercises']:
           cursor.execute(
               'INSERT INTO exercises (workout_id, name, weight, sets, reps) VALUES (?, ?, ?, ?, ?)',
               (workout_id, exercise['name'], exercise['weight'], exercise['sets'], exercise['reps'])
           )
       db.commit()

# get all workouts with their exercises
def get_workouts():
   with get_db() as db:
       workouts = []
       # get workouts in reverse chronological order
       for row in db.execute('SELECT * FROM workouts ORDER BY id DESC'):
           workout = dict(row)
           workout['exercises'] = []
           # get all exercises for each workout
           for ex in db.execute('SELECT * FROM exercises WHERE workout_id = ?', (row['id'],)):
               workout['exercises'].append(dict(ex))
           workouts.append(workout)
       return workouts

# save current workout to a temporary file
def save_current_workout(workout):
   with open('current_workout.json', 'w') as f:
       json.dump(workout, f)

# load current workout from a temporary file
def load_current_workout():
   try:
       with open('current_workout.json', 'r') as f:
           return json.load(f)
   except:
       return {'exercises': []}

# home page route - shows benefits and disclaimers
@app.route('/')
def home():
    # disclaimer messages about data privacy and auto-saving
    disclaimers = {
        'data_privacy': 'workouts will be stored locally on your device',
        'time_cost': 'each workout session takes about 30-60 minutes to log properly',
        'auto_save': 'progress auto-saves every 5 minutes'
    }
    return render_template('home.html', 
        workout_count=len(get_workouts()),
        disclaimers=disclaimers,
        benefits=[...])

# start new workout with a timer
@app.route('/workout/start', methods=['GET'])
def start_workout():
   session['workout_in_progress'] = True
   session['start_timestamp'] = datetime.now().timestamp()
   session['workout_timer'] = '00:00:00'
   session['last_set_time'] = None

   # initialize a new workout session
   current_workout = {
       'exercises': [],
       'start_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
       'notes': '',
       'step': 1,
       'total_steps': 3
   }
   save_current_workout(current_workout)
   return redirect(url_for('add_exercise'))

# add an exercise to the workout
@app.route('/workout/add-exercise', methods=['GET', 'POST'])
def add_exercise():
   if not session.get('workout_in_progress'):
       return redirect(url_for('home'))

   # update workout timer based on elapsed time
   if session.get('start_timestamp'):
       elapsed = int(datetime.now().timestamp() - session['start_timestamp'])
       hours = elapsed // 3600
       minutes = (elapsed % 3600) // 60
       seconds = elapsed % 60
       session['workout_timer'] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

   if request.method == 'POST':
       current_workout = load_current_workout()
       # create an exercise dictionary from form input
       exercise = {
           'name': request.form.get('exercise_name', 'custom exercise'),
           'weight': request.form.get('weight', 'bodyweight'),
           'sets': int(request.form.get('sets', 3)),
           'reps': int(request.form.get('reps', 10))
       }
       session['last_set_time'] = datetime.now().strftime("%H:%M:%S")
       current_workout['exercises'].append(exercise)
       current_workout['step'] = 2
       save_current_workout(current_workout)
       flash('exercise added! add another or finish when ready.')
       return redirect(url_for('add_exercise'))

   return render_template('add_exercise.html',
       current_exercises=load_current_workout().get('exercises', []),
       step=load_current_workout().get('step', 1),
       total_steps=load_current_workout().get('total_steps', 3),
       workout_start=session.get('workout_start_time'),
       last_set=session.get('last_set_time'),
       example_exercises=[
           {'name': 'chair squats', 'mod': 'seated-friendly'},
           {'name': 'wall push-ups', 'mod': 'low-impact'}
       ])

# undo last exercise added
@app.route('/workout/undo-last', methods=['POST'])
def undo_last_exercise():
   current_workout = load_current_workout()
   if current_workout.get('exercises'):
       removed = current_workout['exercises'].pop()
       save_current_workout(current_workout)
       flash(f'removed {removed["name"]}. try again or continue.')
   return redirect(url_for('add_exercise'))

# complete and save workout
@app.route('/workout/finish', methods=['POST'])
def finish_workout():
   current_workout = load_current_workout()
   if not current_workout.get('exercises'):
       flash('add at least one exercise to save your workout!')
       return redirect(url_for('add_exercise'))

   # record end time and save workout
   current_workout['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M")
   current_workout['notes'] = request.form.get('workout_notes', '')
   
   save_workout(current_workout)
   import os
   if os.path.exists('current_workout.json'):
       os.remove('current_workout.json')
   session.pop('workout_in_progress', None)
   
   flash('great job! workout saved.')
   return redirect(url_for('view_history'))

# view workout history
@app.route('/history')
def view_history():
   workouts = get_workouts()
   return render_template('history.html', 
       workouts=workouts,
       modifications_enabled=True)

# initialize database and start app
if __name__ == '__main__':
   init_db()
   app.run(debug=True)
