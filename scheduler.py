import pandas as pd
import time
import random
from datetime import datetime
from test_tweet import tweet_message

def get_approved_tweets():
    df = pd.read_csv('tweets.csv')
    return df[df['status'] == 'approved'].to_dict('records')

def process_tweet_queue():
    while True:
        tweets = get_approved_tweets()
        
        for tweet in tweets:
            if not tweet.get('created_at'):
                # Random delay between 0 and 18 minutes
                delay = random.randint(0, 18 * 60)
                print(f"Waiting {delay} seconds before next tweet...")
                time.sleep(delay)
                
                # Post tweet
                response = tweet_message(tweet['tweet'])
                print(f"Posted tweet: {tweet['tweet']}")
                print(f"Response: {response}")
                
                # Update status
                df = pd.read_csv('tweets.csv')
                df.loc[df['id'] == tweet['id'], 'created_at'] = datetime.now().isoformat()
                df.to_csv('tweets.csv', index=False)
        
        # Wait before checking for new tweets
        time.sleep(60)

if __name__ == '__main__':
    process_tweet_queue()
