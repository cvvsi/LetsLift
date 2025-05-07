# Workout Streak Microservice

## Communication Contract

This microservice calculates the workout streaks of the user. The main program will write into `workout_date.txt`, where the microservice will read and calculate if the user has a streak. It will then write the streak into `streak_results.txt`.

## Files

- `workout_date.txt`: Contains the dates of the user's workouts.
- `streak_results.txt`: Contains the calculated workout streaks.

## How It Works

1. The main program writes workout dates into `workout_date.txt`.
2. The microservice reads the dates from `workout_date.txt`.
3. The microservice calculates the user's workout streak.
4. The microservice writes the streak result into `streak_results.txt`.

## Usage

1. Ensure `workout_date.txt` is populated with workout dates.
2. Run the microservice to calculate the streak.
3. Check `streak_results.txt` for the streak information.

## Example

- `workout_date.txt`:

  ```
  10-01-2023  # make sure date is formated as month-day-year
  10-02-2023  # make sure new date rewrites the date above
  10-03-2023
  ```

- `streak_results.txt`:
  ```
  3
  ```

## UML Diagram

![DIAGRAM](./UML%20Diagram.jpg)

## Dependencies

- Python 3.x (or any other language used)
- Any required libraries (e.g., `datetime` for date handling)

## License

This project is licensed under the MIT License.
