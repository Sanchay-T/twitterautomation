# Import necessary modules and functions
from twitter_utils import generate_tweet_content, tweet_message
import time
import random
import logging
import threading
import signal
import sys
import ast

def get_tweet_interval():
    # Generate a random interval between 10 to 20 minutes (600 to 1200 seconds)
    return random.randint(600, 1200)

def should_tweet():
    # Decide whether to tweet with an 80% probability
    return random.random() < 0.8

def tweet_loop():
    while True:
        if should_tweet():
            try:
                # Generate tweet content using OpenAI's GPT model
                tweet_content = generate_tweet_content()

                # Attempt to parse the tweet content as a literal Python expression
                # This is likely done to handle any special characters or formatting
                try:
                    parsed_tweet = ast.literal_eval(tweet_content)
                except:
                    parsed_tweet = tweet_content

                # Print and log the generated tweet and its metadata
                print("\nGenerated tweet:")
                print(parsed_tweet)
                print("\nCharacter count: {}".format(len(parsed_tweet)))
                print("Line count: {}".format(parsed_tweet.count("\n") + 1))

                logging.info("Generated tweet:\n{}".format(parsed_tweet))
                logging.info("Character count: {}".format(len(parsed_tweet)))
                logging.info("Line count: {}".format(parsed_tweet.count("\n") + 1))

                # Post the tweet to Twitter
                response = tweet_message(parsed_tweet)
                print("Twitter API response:", response)
                logging.info("Twitter API response: {}".format(response))

            except Exception as e:
                # Log any errors that occur during the tweet process
                logging.exception("An error occurred during the tweet process")
                print("An error occurred: {}".format(str(e)))
        else:
            # Log when tweeting is skipped
            print("Skipped tweeting this interval")
            logging.info("Skipped tweeting this interval")

        # Wait for a random interval before the next iteration
        interval = get_tweet_interval()
        print("\nWaiting for {:.2f} minutes before next check".format(interval / 60))
        logging.info(
            "Waiting for {:.2f} minutes before next check".format(interval / 60)
        )
        time.sleep(interval)

def signal_handler(signum, frame):
    # Handle termination signals (SIGINT, SIGTERM) for graceful shutdown
    print("Received signal to terminate. Exiting gracefully...")
    sys.exit(0)

def main():
    # Initialize logging and print startup message
    logging.info("Twitter bot started")
    print("Twitter bot started")

    # Set up signal handlers for graceful termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the tweet loop in the main thread
    try:
        tweet_loop()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Exiting gracefully...")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        logging.exception("An unexpected error occurred")
    finally:
        # Log bot stoppage
        print("Twitter bot stopped")
        logging.info("Twitter bot stopped")

if __name__ == "__main__":
    main()
