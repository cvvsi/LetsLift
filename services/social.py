import json
import time
import os
from datetime import datetime

def process_social_post(data):
    try:
        # Load existing posts
        posts_file = 'data/social_posts.json'
        if os.path.exists(posts_file):
            with open(posts_file, 'r') as f:
                posts = json.load(f)
        else:
            posts = []
        
        # Add new post
        new_post = {
            "user_id": data.get('user_id', 'default_user'),
            "content": data.get('content', ''),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        posts.insert(0, new_post)
        
        # Save updated posts
        with open(posts_file, 'w') as f:
            json.dump(posts, f, indent=2)
            
        print(f"Social Service: Added new post - {new_post['content']}")
        
    except Exception as e:
        print(f"Social Service Error: {e}")

def run_social_service():
    print("Social Service: Running...")
    os.makedirs('data', exist_ok=True)
    
    while True:
        try:
            if os.path.exists('data/social_input.txt'):
                with open('data/social_input.txt', 'r') as f:
                    data = json.load(f)
                
                process_social_post(data)
                os.remove('data/social_input.txt')
                
        except Exception as e:
            print(f"Social Service Error: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    run_social_service() 