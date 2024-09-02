from requests_oauthlib import OAuth1Session
import os
import json
import random
from dotenv import load_dotenv
from openai import OpenAI
import base64
import logging
import requests
from requests.auth import AuthBase
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
import ast

# Load environment variables from .env file
load_dotenv()

# Debug: Print .env file contents (sensitive data masked)
print("Debug: .env file contents:")
try:
    with open(".env", "r") as env_file:
        for line_number, line in enumerate(env_file, 1):
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                print(f"Line {line_number}: {key}={'*' * len(value)}")
            else:
                print(f"Line {line_number}: {line} (Invalid format)")
except FileNotFoundError:
    print("Debug: .env file not found")
except Exception as e:
    print(f"Debug: Error reading .env file: {str(e)}")

# # Initialize OpenAI client with API key
# client = OpenAI()

# # Set up logging configuration
# logging.basicConfig(
#     filename="twitter_bot.log",
#     level=logging.INFO,
#     format="%(asctime)s - %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
# )


# def encode_image(image_path):
#     # Function to encode an image file to base64
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode("utf-8")


# def clean_tweet(tweet):
#     # Function to clean and format the tweet text
#     # (This function is currently not used in the main loop)
#     tweet = tweet.lower()
#     tweet = tweet.replace('"', "").replace('"', "").replace('"', "")
#     for punct in [".", ",", "!", "?", ":"]:
#         tweet = tweet.replace(f"{punct}", f"{punct} ")
#     lines = tweet.split("\n")
#     cleaned_lines = [" ".join(line.split()) for line in lines]
#     tweet = "\n".join(cleaned_lines)
#     return tweet.strip()


# def generate_tweet_content():
#     # Define the system message for the AI model
#     system_message = """You are Sanchay Thalnerkar, a brilliant 23-year-old AI engineer with a knack for blending deep technical insights with practical applications. Your tweets are concise, impactful, and reflective of your background in AI, entrepreneurship, and productivity.

#     Guidelines:
#     1. Focus on one key insight, tip, or thought per tweet.
#     2. Ensure the tweet is between 60-100 characters, concise but full of depth.
#     3. Start directly with the main content, avoiding phrases like "book_takeaway" or similar.
#     4. Maintain clarity, and avoid unnecessary context or complex jargon.
#     5. Use lowercase for everything except acronyms like 'AI' or 'ML'.
#     6. Avoid emojis, hashtags, and filler words.

#     Your goal: Inspire and provoke thought with a brief, yet powerful message that leaves a lasting impression."""

#     # Define categories and formats for tweets
#     tweet_categories = [
#         "Neural Network Architectures",
#         "Reinforcement Learning Breakthroughs",
#         "Natural Language Processing Techniques",
#         "Computer Vision Advancements",
#         "Data Preprocessing Strategies",
#         "Model Interpretability Methods",
#         "AI in Scientific Research",
#         "Machine Learning for Climate Science",
#         "Robotics and AI Integration",
#         "Quantum Computing and ML",
#         "Federated Learning Developments",
#         "AI in Healthcare Diagnostics",
#         "Generative AI Techniques",
#         "Graph Neural Networks",
#         "Time Series Forecasting Methods",
#         "AutoML Advancements",
#         "Edge AI and IoT",
#         "Adversarial Machine Learning",
#         "Transfer Learning Strategies",
#         "Productivity Techniques",
#         "Interesting Scientific Facts",
#         "Self-Improvement Strategies",
#         "Entrepreneurship Lessons",
#         "Book Recommendations",
#         "Time Management Tips",
#         "Startup Experiences",
#         "Tech Industry Trends",
#         "Personal Growth Reflections",
#     ]

#     tweet_formats = [
#         "technical_insight",
#         "research_finding",
#         "code_snippet",
#         "analogy",
#         "question",
#         "personal_experience",
#         "productivity_tip",
#         "interesting_fact",
#         "entrepreneurial_lesson",
#     ]

#     # Randomly select a category and format
#     selected_format = random.choice(tweet_formats)
#     selected_category = random.choice(tweet_categories)

#     # Create the prompt for the AI model
#     prompt = f"""Craft a concise tweet about: {selected_category} in this format {selected_format}

#     Focus:
#     - One key insight, tip, or thought.
#     - Depth with brevity: 60-100 characters max.
#     - Start directly with the main content; do not use introductory phrases like "book_takeaway."
#     - Clarity without jargon.

#     Your tweet should immediately convey the main message, leaving readers with a strong impression of your expertise and unique perspective, fitting the character limit while reflecting your persona."""

#     # Generate the tweet using OpenAI's GPT-4 model
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": system_message},
#             {"role": "user", "content": prompt},
#         ],
#         max_tokens=60,
#         temperature=0.8,
#     )

#     # Extract and return the generated tweet
#     tweet = response.choices[0].message.content.strip()
#     return tweet


# <-------------------------------------------------------->


client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)

# Set up logging configuration
logging.basicConfig(
    filename="twitter_bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def encode_image(image_path):
    # Function to encode an image file to base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def clean_tweet(tweet):
    # Function to clean and format the tweet text
    tweet = tweet.lower()
    tweet = tweet.replace('"', "").replace('"', "").replace('"', "")
    for punct in [".", ",", "!", "?", ":"]:
        tweet = tweet.replace(f"{punct}", f"{punct} ")
    lines = tweet.split("\n")
    cleaned_lines = [" ".join(line.split()) for line in lines]
    tweet = "\n".join(cleaned_lines)
    return tweet.strip()


def generate_tweet_content():
    # Define the system message for the AI model
    system_message = """You are Sanchay Thalnerkar, a brilliant 23-year-old AI engineer with a knack for blending deep technical insights with practical applications. Your tweets are concise, impactful, and reflective of your background in AI, entrepreneurship, and productivity.

    Guidelines:
    1. Focus on one key insight, tip, or thought per tweet.
    2. Ensure the tweet is between 60-100 characters, concise but full of depth.
    3. Start directly with the main content, avoiding phrases like "book_takeaway" or similar.
    4. Maintain clarity, and avoid unnecessary context or complex jargon.
    5. Use lowercase for everything except acronyms like 'AI' or 'ML'.
    6. Avoid emojis, hashtags, and filler words.

    Your goal: Inspire and provoke thought with a brief, yet powerful message that leaves a lasting impression."""

    # Define categories and formats for tweets
    tweet_categories = [
        "Neural Network Architectures",
        "Reinforcement Learning Breakthroughs",
        "Natural Language Processing Techniques",
        "Computer Vision Advancements",
        "Data Preprocessing Strategies",
        "Model Interpretability Methods",
        "AI in Scientific Research",
        "Machine Learning for Climate Science",
        "Robotics and AI Integration",
        "Quantum Computing and ML",
        "Federated Learning Developments",
        "AI in Healthcare Diagnostics",
        "Generative AI Techniques",
        "Graph Neural Networks",
        "Time Series Forecasting Methods",
        "AutoML Advancements",
        "Edge AI and IoT",
        "Adversarial Machine Learning",
        "Transfer Learning Strategies",
        "Productivity Techniques",
        "Interesting Scientific Facts",
        "Self-Improvement Strategies",
        "Entrepreneurship Lessons",
        "Book Recommendations",
        "Time Management Tips",
        "Startup Experiences",
        "Tech Industry Trends",
        "Personal Growth Reflections",
    ]

    tweet_formats = [
        "technical_insight",
        "research_finding",
        "code_snippet",
        "analogy",
        "question",
        "personal_experience",
        "productivity_tip",
        "interesting_fact",
        "entrepreneurial_lesson",
    ]

    # Randomly select a category and format
    selected_format = random.choice(tweet_formats)
    selected_category = random.choice(tweet_categories)

    # Create the prompt for the AI model
    prompt = f"""Craft a concise tweet about: {selected_category} in this format {selected_format}

    Focus:
    - One key insight, tip, or thought.
    - Depth with brevity: 60-100 characters max.
    - Start directly with the main content; do not use introductory phrases like "book_takeaway."
    - Clarity without jargon.

    Your tweet should immediately convey the main message, leaving readers with a strong impression of your expertise and unique perspective, fitting the character limit while reflecting your persona."""

    # Generate the tweet using NVIDIA's model
    response = client.chat.completions.create(
        model="meta/llama-3.1-405b-instruct",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        max_tokens=60,
        temperature=0.8,
    )

    # Extract and return the generated tweet
    tweet = response.choices[0].message.content.strip()
    print(f"Generated Tweet: {tweet}")
    return tweet


# <-------------------------------------------------------->


class BearerAuth(AuthBase):
    # Custom authentication class for Bearer token
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


def get_bearer_token():
    # Function to obtain a bearer token from Twitter API
    # (This function is currently not used in the main loop)
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    token_url = "https://api.twitter.com/2/oauth2/token"

    print(f"Debug: CLIENT_ID = {client_id}")
    print(f"Debug: CLIENT_SECRET is {'set' if client_secret else 'not set'}")

    if not client_id or not client_secret:
        raise ValueError(
            "CLIENT_ID or CLIENT_SECRET not found in environment variables"
        )

    # Encode client_id and client_secret
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "client_credentials",
        "scope": "tweet.read tweet.write users.read",
    }

    print(f"Debug: Sending request to {token_url}")
    print(f"Debug: Request headers: {headers}")
    print(f"Debug: Request data: {data}")

    response = requests.post(token_url, headers=headers, data=data)

    print(f"Debug: Response status code: {response.status_code}")
    print(f"Debug: Response content: {response.text}")

    if response.status_code != 200:
        error_message = (
            f"Error obtaining bearer token: {response.status_code} {response.text}"
        )
        logging.error(error_message)
        raise Exception(error_message)

    return response.json()["access_token"]


def tweet_message(message):
    # Function to post a tweet using Twitter API
    consumer_key = os.getenv("CONSUMER_KEY")
    consumer_secret = os.getenv("CONSUMER_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        error_message = "Missing required OAuth credentials in environment variables"
        logging.error(error_message)
        return error_message

    # Create OAuth1Session for authentication
    oauth = OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

    # Prepare the payload (tweet content)
    payload = {"text": message}

    # Make the POST request to Twitter API
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code != 201:
        error_message = (
            f"Error: Request returned an error: {response.status_code} {response.text}"
        )
        logging.error(error_message)
        return error_message

    # Return the JSON response from Twitter API
    return json.dumps(response.json(), indent=4, sort_keys=True)
