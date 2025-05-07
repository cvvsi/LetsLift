import re
from datetime import datetime, timedelta
import time

def read_date_from_file():
    try:
        with open('workout_date.txt', 'r') as file:
            date_string = file.readline().strip()
            match = re.search(r'\d+-\d+-\d{4}', date_string)
            if match:
                date = datetime.strptime(match.group(), '%m-%d-%Y').date()
                # Don't accept future dates
                if date > datetime.now().date():
                    print(f"Warning: Future date detected ({date})")
                    return None
                return date
    except (FileNotFoundError, ValueError, AttributeError):
        return None
    return None

def read_stored_date():
    try:
        with open('stored_date.txt', 'r') as file:
            date_string = file.readline().strip()
            date = datetime.strptime(date_string, '%m-%d-%Y').date()
            # Don't accept future dates
            if date > datetime.now().date():
                return None
            return date
    except (FileNotFoundError, ValueError):
        return None

def save_stored_date(date):
    with open('stored_date.txt', 'w') as file:
        file.write(date.strftime('%m-%d-%Y'))

def main():
    stored_date = read_stored_date()
    current_streak = 0

    while True:
        new_date = read_date_from_file()
        
        if new_date:
            print(f"Processing date: {new_date}")
            if stored_date:
                print(f"Comparing with stored date: {stored_date}")
                # Compare with stored date
                date_diff = (new_date - stored_date).days
                print(f"Date difference: {date_diff} days")
                if date_diff == 1:  # Next day
                    current_streak += 1
                    print(f"Streak increased to {current_streak}")
                elif date_diff == 0:  # Same day
                    print("Same day, maintaining streak")
                    pass
                else:  # Streak broken
                    current_streak = 1
                    print("Streak reset to 1")
            else:
                current_streak = 1
                print("First workout, streak set to 1")
            
            stored_date = new_date
            save_stored_date(stored_date)
            
            with open('streak_results.txt', 'w') as streak_file:
                streak_file.write(str(current_streak))
            
            print(f"Current streak: {current_streak}")
        
        time.sleep(5)

if __name__ == "__main__":
    main()