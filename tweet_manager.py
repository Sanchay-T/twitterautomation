import pandas as pd
from datetime import datetime, timedelta
from test_tweet import tweet_message

class TweetManager:
    def __init__(self, csv_file="tweets.csv"):
        self.csv_file = csv_file
        self.df = pd.read_csv(csv_file)
        
    def show_pending_tweets(self):
        pending = self.df[self.df['status'].isna()]
        if len(pending) == 0:
            print("No pending tweets")
            return
        
        print("\nPending Tweets:")
        for _, tweet in pending.iterrows():
            print(f"\nID: {tweet['id']}")
            print(f"Tweet: {tweet['tweet']}")
            
    def show_schedule(self):
        scheduled = self.df[self.df['status'] == 'approved'].sort_values('scheduled_time')
        if len(scheduled) == 0:
            print("No scheduled tweets")
            return
            
        print("\nScheduled Tweets:")
        for _, tweet in scheduled.iterrows():
            print(f"\nTweet: {tweet['tweet']}")
            print(f"Scheduled for: {tweet['scheduled_time']}")
            
    def approve_tweet(self, tweet_id):
        if tweet_id not in self.df['id'].values:
            print(f"Tweet ID {tweet_id} not found")
            return
            
        current_time = datetime.now()
        approved_count = len(self.df[self.df['status'] == 'approved'])
        scheduled_time = current_time + timedelta(minutes=18 * approved_count)
        
        self.df.loc[self.df['id'] == tweet_id, 'status'] = 'approved'
        self.df.loc[self.df['id'] == tweet_id, 'scheduled_time'] = scheduled_time
        self.df.to_csv(self.csv_file, index=False)
        print(f"Tweet {tweet_id} approved and scheduled for {scheduled_time}")
        
    def reject_tweet(self, tweet_id):
        if tweet_id not in self.df['id'].values:
            print(f"Tweet ID {tweet_id} not found")
            return
            
        self.df.loc[self.df['id'] == tweet_id, 'status'] = 'rejected'
        self.df.to_csv(self.csv_file, index=False)
        print(f"Tweet {tweet_id} rejected")
        
    def post_tweet(self, tweet_text):
        next_id = self.df['id'].max() + 1 if len(self.df) > 0 else 1
        new_tweet = pd.DataFrame({
            'id': [next_id],
            'tweet': [tweet_text],
            'status': [None],
            'created_at': [datetime.now()],
            'scheduled_time': [None]
        })
        self.df = pd.concat([self.df, new_tweet], ignore_index=True)
        self.df.to_csv(self.csv_file, index=False)
        print(f"Tweet added with ID: {next_id}")

def main():
    manager = TweetManager()
    while True:
        print("\n=== Tweet Manager ===")
        print("1. Show pending tweets")
        print("2. Show schedule")
        print("3. Approve tweet")
        print("4. Reject tweet")
        print("5. Add new tweet")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            manager.show_pending_tweets()
        elif choice == '2':
            manager.show_schedule()
        elif choice == '3':
            tweet_id = int(input("Enter tweet ID to approve: "))
            manager.approve_tweet(tweet_id)
        elif choice == '4':
            tweet_id = int(input("Enter tweet ID to reject: "))
            manager.reject_tweet(tweet_id)
        elif choice == '5':
            tweet_text = input("Enter your tweet: ")
            manager.post_tweet(tweet_text)
        elif choice == '6':
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
