from requests_oauthlib import OAuth1Session
import json
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_twitter_credentials():
    """Load and validate Twitter credentials from environment variables."""
    load_dotenv()
    
    required_vars = [
        'TWITTER_CONSUMER_KEY',
        'TWITTER_CONSUMER_SECRET',
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return {
        'consumer_key': os.getenv('TWITTER_CONSUMER_KEY'),
        'consumer_secret': os.getenv('TWITTER_CONSUMER_SECRET'),
        'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
        'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    }

def tweet_message(message):
    try:
        # Load credentials
        credentials = load_twitter_credentials()
        
        # Create OAuth1Session
        oauth = OAuth1Session(
            credentials['consumer_key'],
            client_secret=credentials['consumer_secret'],
            resource_owner_key=credentials['access_token'],
            resource_owner_secret=credentials['access_token_secret'],
        )

        # Post tweet
        payload = {"text": message}
        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
        )

        if response.status_code != 201:
            logger.error(f"Twitter API error: {response.status_code} - {response.text}")
            return f"Error: Request returned an error: {response.status_code} {response.text}"

        logger.info("Tweet posted successfully")
        return json.dumps(response.json(), indent=4, sort_keys=True)

    except Exception as e:
        logger.error(f"Error posting tweet: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        tweet_text = input("Enter a tweet to post: ")
        response = tweet_message(tweet_text)
        print("Twitter API response:", response)
    except Exception as e:
        print(f"Error: {str(e)}")
