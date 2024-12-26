from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime, timedelta
from test_tweet import tweet_message
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('tweets.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tweets")
def get_tweets():
    try:
        logging.debug("Fetching tweets from DB.")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tweet, status, created_at FROM tweets WHERE status IS NULL")
        rows = cursor.fetchall()
        conn.close()
        clean_tweets = []
        for row in rows:
            clean_tweets.append({
                "id": row["id"],
                "tweet": row["tweet"],
                "status": row["status"],
                "created_at": row["created_at"]
            })
        logging.debug(f"Found {len(clean_tweets)} tweets pending review.")
        return jsonify(clean_tweets)
    except Exception as e:
        logging.error("Error in get_tweets", exc_info=e)
        print("[ERROR get_tweets]:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/approve", methods=["POST"])
def approve_tweet():
    try:
        logging.debug("Approve tweet endpoint called.")
        data = request.json
        tweet_id = data["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        current_time = datetime.now()

        cursor.execute("SELECT COUNT(*) FROM tweets WHERE status = 'approved'")
        approved_count = cursor.fetchone()[0]
        scheduled_time = current_time + timedelta(minutes=18 * approved_count)

        cursor.execute(
            "UPDATE tweets SET status = 'approved', scheduled_time = ? WHERE id = ?",
            (scheduled_time.strftime('%Y-%m-%d %H:%M:%S'), tweet_id)
        )
        conn.commit()
        conn.close()
        logging.debug(f"Tweet {tweet_id} approved, scheduled at {scheduled_time}.")
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error("Error in approve_tweet", exc_info=e)
        print("[ERROR approve_tweet]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/reject", methods=["POST"])
def reject_tweet():
    try:
        logging.debug("Reject tweet endpoint called.")
        data = request.json
        tweet_id = data["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE tweets SET status = 'rejected' WHERE id = ?", (tweet_id,))
        conn.commit()
        conn.close()
        logging.debug(f"Tweet {tweet_id} rejected.")
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error("Error in reject_tweet", exc_info=e)
        print("[ERROR reject_tweet]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/post_tweet", methods=["POST"])
def post_tweet():
    try:
        logging.debug("Post tweet endpoint called.")
        data = request.json
        tweet_text = data["tweet"]
        response = tweet_message(tweet_text)
        logging.debug(f"Tweeted: {tweet_text}")
        return jsonify({"status": "success", "response": response})
    except Exception as e:
        logging.error("Error in post_tweet", exc_info=e)
        print("[ERROR post_tweet]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/schedule")
def get_schedule():
    try:
        logging.debug("Fetching approved tweet schedule.")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, tweet, status, created_at, scheduled_time 
            FROM tweets 
            WHERE status = 'approved'
            ORDER BY scheduled_time ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to list of dicts
        schedule = []
        for row in rows:
            schedule.append({
                'id': row['id'],
                'tweet': row['tweet'],
                'status': row['status'],
                'created_at': row['created_at'],
                'scheduled_time': row['scheduled_time']
            })
        
        logging.debug(f"Schedule has {len(schedule)} tweets.")
        # Return just the array of tweets, not wrapped in another object
        return jsonify(schedule)
    except Exception as e:
        logging.error("Error in get_schedule", exc_info=e)
        print("[ERROR get_schedule]:", e)
        return jsonify([]), 500


if __name__ == "__main__":
    app.run(debug=True)
