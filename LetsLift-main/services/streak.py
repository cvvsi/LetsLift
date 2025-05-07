import time
from datetime import datetime
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'data')

def read_stored_date():
    try:
        with open(os.path.join(DATA_DIR, 'stored_date.txt'), 'r') as file:
            return datetime.strptime(file.read().strip(), '%m-%d-%Y').date()
    except (FileNotFoundError, ValueError):
        return None

def save_stored_date(date):
    with open(os.path.join(DATA_DIR, 'stored_date.txt'), 'w') as file:
        file.write(date.strftime('%m-%d-%Y'))

def run_streak_service():
    print("Streak Service: Running...")
    os.makedirs(DATA_DIR, exist_ok=True)
    stored_date = read_stored_date()
    current_streak = 0

    while True:
        try:
            workout_date_file = os.path.join(DATA_DIR, 'workout_date.txt')
            if os.path.exists(workout_date_file):
                with open(workout_date_file, 'r') as f:
                    date_str = f.read().strip()
                    new_date = datetime.strptime(date_str, '%m-%d-%Y').date()
                
                print(f"Processing workout date: {new_date}")
                
                if stored_date:
                    date_diff = (new_date - stored_date).days
                    if date_diff == 1:  # Next day
                        current_streak += 1
                        print(f"Streak increased to {current_streak}")
                    elif date_diff == 0:  # Same day
                        print("Same day, maintaining streak")
                    else:  # Streak broken
                        current_streak = 1
                        print("Streak reset to 1")
                else:
                    current_streak = 1
                    print("First workout, streak set to 1")
                
                stored_date = new_date
                save_stored_date(stored_date)
                
                # Write streak to file that app.py will read
                with open(os.path.join(DATA_DIR, 'streak.txt'), 'w') as f:
                    f.write(str(current_streak))
                
                print(f"Current streak: {current_streak} days")
                os.remove(workout_date_file)
                
        except Exception as e:
            print(f"Streak Service Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    run_streak_service() 