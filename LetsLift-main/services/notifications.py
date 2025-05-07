import json
import time
import os
from datetime import datetime

def create_notification(data):
    try:
        notifications_file = 'data/notifications.json'
        if os.path.exists(notifications_file):
            with open(notifications_file, 'r') as f:
                notifications = json.load(f)
        else:
            notifications = []
        
        new_notification = {
            "user_id": data.get('user_id', 'default_user'),
            "message": "Workout completed! 💪",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "read": False
        }
        
        notifications.insert(0, new_notification)
        
        with open(notifications_file, 'w') as f:
            json.dump(notifications, f, indent=2)
            
        print(f"Notification Service: Created notification for {new_notification['user_id']}")
        
    except Exception as e:
        print(f"Notification Service Error: {e}")

def run_notification_service():
    print("Notification Service: Running...")
    os.makedirs('data', exist_ok=True)
    
    while True:
        try:
            if os.path.exists('data/notification_input.txt'):
                with open('data/notification_input.txt', 'r') as f:
                    data = json.load(f)
                
                create_notification(data)
                os.remove('data/notification_input.txt')
                
        except Exception as e:
            print(f"Notification Service Error: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    run_notification_service() 