from requests_oauthlib import OAuth1Session
import json

def tweet_message(message):
    # Hardcoded Twitter API credentials
    consumer_key = "F7eW6cO1qAR4H1yFpS7VgsdHA"
    consumer_secret = "IIzgyLIeN4HrVRCUt7pviuAEFFc3qhZlq9qGaJQ51bvTYqXgOG"
    access_token = "1371134018582843393-JJADl79N3t8CSmPVqHfgeiHrdMheKp"
    access_token_secret = "BBZZDWVyedO0bWK6uRoEBxEyyP3Y1aT3vgLF74mSlxGU1"

    # Create OAuth1Session
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Post tweet
    payload = {"text": message}
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        return f"Error: Request returned an error: {response.status_code} {response.text}"

    return json.dumps(response.json(), indent=4, sort_keys=True)

if __name__ == "__main__":
    tweet_text = input("Enter a tweet to post: ")
    response = tweet_message(tweet_text)
    print("Twitter API response:", response)
