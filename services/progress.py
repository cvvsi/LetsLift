import json
import time
import os
from datetime import datetime, timedelta
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'data')

def calculate_stats(workout_data):
    print("\n=== Processing Progress Stats ===")
    print(f"Received data: {json.dumps(workout_data, indent=2)}")
    
    try:
        # Load workout history
        workouts = workout_data.get('workouts', [])
        print(f"Processing {len(workouts)} workouts")
        
        if not workouts:
            print("No workouts found in data!")
            return {}
            
        stats = {
            'total_workouts': len(workouts),
            'time_periods': {
                'week': 0,
                'two_weeks': 0,
                'month': 0
            },
            'exercise_frequency': {
                'top_exercises': []
            },
            'total_volume': 0
        }
        
        print("Calculating time-based stats...")
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        month_ago = now - timedelta(days=30)
        
        all_exercises = []
        
        for workout in workouts:
            try:
                workout_time = datetime.strptime(workout['start_time'], "%Y-%m-%d %H:%M")
                print(f"Processing workout from {workout_time}")
                
                if workout_time >= week_ago:
                    stats['time_periods']['week'] += 1
                if workout_time >= two_weeks_ago:
                    stats['time_periods']['two_weeks'] += 1
                if workout_time >= month_ago:
                    stats['time_periods']['month'] += 1
                
                for exercise in workout.get('exercises', []):
                    all_exercises.append(exercise['name'])
                    try:
                        weight = float(exercise['weight'])
                        volume = weight * exercise['sets'] * exercise['reps']
                        stats['total_volume'] += volume
                        print(f"Added volume for {exercise['name']}: {volume}")
                    except (ValueError, TypeError):
                        print(f"Skipping volume calculation for {exercise['name']}")
            except Exception as e:
                print(f"Error processing workout: {e}")
                continue
        
        print("\nCalculating exercise frequency...")
        exercise_counter = Counter(all_exercises)
        top_exercises = exercise_counter.most_common(3)
        stats['exercise_frequency']['top_exercises'] = [
            {'name': name, 'count': count}
            for name, count in top_exercises
        ]
        
        print("\n=== Final Stats ===")
        print(json.dumps(stats, indent=2))
        
        print("\nWriting to output file...")
        output_file = os.path.join(DATA_DIR, 'progress_output.txt')
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        print("Stats written successfully!")
        
        return stats
        
    except Exception as e:
        print(f"Error calculating stats: {e}")
        import traceback
        print(traceback.format_exc())
        return {}

def run_progress_service():
    print("\n=== Progress Service Starting ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Looking for data in: {os.path.abspath(DATA_DIR)}")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    print("Data directory ensured")
    
    print("Progress Service: Running and waiting for input...")
    print("Press Ctrl+C to stop\n")
    
    while True:
        try:
            input_file = os.path.join(DATA_DIR, 'progress_input.txt')
            if os.path.exists(input_file):
                print("\nFound new input file!")
                with open(input_file, 'r') as f:
                    data = json.load(f)
                
                calculate_stats(data)
                os.remove(input_file)
                print("Processed and removed input file")
                
        except Exception as e:
            print(f"Progress Service Error: {e}")
            import traceback
            print(traceback.format_exc())
            
        time.sleep(1)

if __name__ == "__main__":
    run_progress_service() 