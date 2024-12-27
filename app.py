from flask import Flask, render_template, jsonify, request
import pandas as pd
from datetime import datetime, timedelta
from test_tweet import tweet_message
import sqlite3
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import random
import atexit  # Add this import
import os

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("tweets.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tweets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet TEXT NOT NULL,
            status TEXT,
            created_at DATETIME,
            scheduled_time DATETIME,
            posted_time DATETIME
        )
    """
    )

    # Add posted_time column if it doesn't exist
    cursor.execute("PRAGMA table_info(tweets)")
    columns = [col[1] for col in cursor.fetchall()]
    if "posted_time" not in columns:
        cursor.execute("ALTER TABLE tweets ADD COLUMN posted_time DATETIME")

    conn.commit()
    conn.close()


def post_scheduled_tweets():
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get current time
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # Check tweets posted in the last hour
        cursor.execute(
            """
            SELECT COUNT(*) FROM tweets
            WHERE status = 'posted'
              AND posted_time >= datetime('now', '-1 hour')
        """
        )
        posted_count_last_hour = cursor.fetchone()[0]
        max_per_hour = 3
        remaining_slots = max_per_hour - posted_count_last_hour

        if remaining_slots > 0:
            # Fetch only the number of tweets we can post
            cursor.execute(
                """
                SELECT id, tweet
                FROM tweets
                WHERE status = 'approved'
                  AND scheduled_time <= ?
                LIMIT ?
            """,
                (now_str, remaining_slots),
            )

            due_tweets = cursor.fetchall()

            for row in due_tweets:
                response = tweet_message(row["tweet"])
                logging.debug(f"Twitter API response: {response}")

                cursor.execute(
                    """
                    UPDATE tweets
                    SET status = 'posted',
                        scheduled_time = NULL,
                        posted_time = ?
                    WHERE id = ?
                """,
                    (now_str, row["id"]),
                )
        else:
            # Fetch all due tweets that need rescheduling
            cursor.execute(
                """
                SELECT id
                FROM tweets
                WHERE status = 'approved'
                  AND scheduled_time <= ?
            """,
                (now_str,),
            )

            due_tweets = cursor.fetchall()

            # Reschedule with better distribution
            for i, row in enumerate(due_tweets):
                # Distribute tweets across next 2 hours to avoid bunching
                random_minute = random.randint(1, 60)
                delay_hour = 1 + (
                    i // max_per_hour
                )  # Spreads tweets across hours if many
                new_time = now + timedelta(hours=delay_hour, minutes=random_minute)

                cursor.execute(
                    """
                    UPDATE tweets 
                    SET scheduled_time = ?
                    WHERE id = ?
                """,
                    (new_time.strftime("%Y-%m-%d %H:%M:%S"), row["id"]),
                )

        conn.commit()
        conn.close()


def restore_scheduled_tweets():
    """Restore scheduled tweets from database on server startup"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all approved tweets with scheduled times
        cursor.execute(
            """
            SELECT id, tweet, scheduled_time
            FROM tweets
            WHERE status = 'approved'
            AND scheduled_time IS NOT NULL
            ORDER BY scheduled_time ASC
        """
        )

        scheduled_tweets = cursor.fetchall()
        now = datetime.now()

        for tweet in scheduled_tweets:
            scheduled_time = datetime.strptime(
                tweet["scheduled_time"], "%Y-%m-%d %H:%M:%S"
            )
            if scheduled_time <= now:
                # If tweet was supposed to be posted while server was down,
                # reschedule it with proper distribution
                random_minute = random.randint(1, 60)
                new_time = now + timedelta(minutes=random_minute)

                cursor.execute(
                    """
                    UPDATE tweets 
                    SET scheduled_time = ?
                    WHERE id = ?
                """,
                    (new_time.strftime("%Y-%m-%d %H:%M:%S"), tweet["id"]),
                )

                logging.info(f"Rescheduled missed tweet {tweet['id']} to {new_time}")

        conn.commit()
        conn.close()

        logging.info(f"Restored {len(scheduled_tweets)} scheduled tweets from database")
    except Exception as e:
        logging.error("Error restoring scheduled tweets", exc_info=e)


@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tweet, status FROM tweets")
    rows = cursor.fetchall()
    conn.close()
    return render_template("index.html", tweets=rows)


@app.route("/tweets")
def get_tweets():
    try:
        logging.debug("Fetching tweets from DB.")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Modified query to ensure proper ordering
        cursor.execute(
            """
            SELECT id, tweet, status, created_at 
            FROM tweets 
            WHERE status IS NULL
            ORDER BY created_at ASC
        """
        )

        rows = cursor.fetchall()
        conn.close()

        clean_tweets = []
        for row in rows:
            clean_tweets.append(
                {
                    "id": row["id"],
                    "tweet": row["tweet"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                }
            )

        logging.debug(f"Found {len(clean_tweets)} tweets pending review.")
        return jsonify(clean_tweets)
    except Exception as e:
        logging.error("Error in get_tweets", exc_info=e)
        return jsonify({"error": str(e)}), 500


@app.route("/approve", methods=["POST"])
def approve_tweet():
    try:
        logging.debug("Approve tweet endpoint called.")
        data = request.json
        tweet_id = data["id"]
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the latest scheduled tweet time
        cursor.execute(
            """
            SELECT MAX(scheduled_time) as last_scheduled
            FROM tweets 
            WHERE status = 'approved'
        """
        )
        last_scheduled = cursor.fetchone()["last_scheduled"]

        # Calculate the next available slot
        current_time = datetime.now()
        base_time = current_time
        if last_scheduled:
            last_scheduled_dt = datetime.strptime(last_scheduled, "%Y-%m-%d %H:%M:%S")
            base_time = max(current_time, last_scheduled_dt)

        # Add minimum 12 minutes plus random additional 0-8 minutes
        min_delay = timedelta(minutes=12)
        random_additional_delay = timedelta(minutes=random.randint(0, 8))
        scheduled_time = base_time + min_delay + random_additional_delay

        cursor.execute(
            "UPDATE tweets SET status = 'approved', scheduled_time = ? WHERE id = ?",
            (scheduled_time.strftime("%Y-%m-%d %H:%M:%S"), tweet_id),
        )
        conn.commit()

        # Format times for display
        ist_time = scheduled_time.strftime("%I:%M %p")  # Format: HH:MM AM/PM
        ist_date = scheduled_time.strftime("%b %d, %Y")  # Format: Mon DD, YYYY

        conn.close()
        logging.debug(f"Tweet {tweet_id} approved, scheduled at {scheduled_time} IST")
        return jsonify(
            {
                "status": "success",
                "scheduled_time": scheduled_time.strftime("%Y-%m-%d %H:%M:%S"),
                "display_time": f"{ist_date} at {ist_time} IST",
            }
        )
    except Exception as e:
        logging.error("Error in approve_tweet", exc_info=e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/reject", methods=["POST"])
def reject_tweet():
    try:
        logging.debug("Reject tweet endpoint called.")
        data = request.json
        tweet_id = data["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE tweets SET status = 'rejected' WHERE id = ?", (tweet_id,)
        )
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

        # 1) Find and post any approved tweets that are past due
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            SELECT id, tweet, scheduled_time
            FROM tweets
            WHERE status = 'approved'
                  AND scheduled_time IS NOT NULL
                  AND scheduled_time <= ?
            """,
            (now_str,),
        )
        due_tweets = cursor.fetchall()
        for row in due_tweets:
            logging.debug(f"Scheduled time: {row['scheduled_time']} vs now: {now_str}")
            tweet_message(row["tweet"])  # Post immediately
            cursor.execute(
                "UPDATE tweets SET status = 'posted', scheduled_time = NULL WHERE id = ?",
                (row["id"],),
            )

        conn.commit()

        # 2) Fetch the updated schedule (still approved and future-scheduled)
        cursor.execute(
            """
            SELECT id, tweet, status, created_at, scheduled_time 
            FROM tweets 
            WHERE status = 'approved'
            AND scheduled_time > datetime('now')
            ORDER BY scheduled_time ASC
        """
        )
        rows = cursor.fetchall()
        conn.close()

        # Convert rows to list of dicts
        schedule = []
        for row in rows:
            schedule.append(
                {
                    "id": row["id"],
                    "tweet": row["tweet"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "scheduled_time": row["scheduled_time"],
                }
            )

        logging.debug(f"Schedule has {len(schedule)} tweets.")
        # Return just the array of tweets, not wrapped in another object
        return jsonify(schedule)
    except Exception as e:
        logging.error("Error in get_schedule", exc_info=e)
        print("[ERROR get_schedule]:", e)
        return jsonify([]), 500


@app.route("/upload_tweets", methods=["POST"])
def upload_tweets():
    try:
        logging.debug("Upload tweets endpoint called.")
        data = request.json
        tweets = data.get("tweets", [])
        if not tweets:
            return jsonify({"status": "error", "message": "No tweets provided."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        for tweet in tweets:
            cursor.execute(
                "INSERT INTO tweets (tweet, status, created_at) VALUES (?, NULL, ?)",
                (tweet, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            )
        conn.commit()
        conn.close()
        logging.debug(f"Uploaded {len(tweets)} tweets.")
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error("Error in upload_tweets", exc_info=e)
        print("[ERROR upload_tweets]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/delete_tweet", methods=["POST"])
def delete_tweet():
    try:
        logging.debug("Delete tweet endpoint called.")
        data = request.json
        tweet_id = data["id"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tweets WHERE id = ?", (tweet_id,))
        conn.commit()
        conn.close()
        logging.debug(f"Tweet {tweet_id} deleted.")
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error("Error in delete_tweet", exc_info=e)
        print("[ERROR delete_tweet]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/post_now_tweet", methods=["POST"])
def post_now_tweet():
    try:
        logging.debug("Post now tweet endpoint called.")
        data = request.json
        tweet_id = data["id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve the tweet content
        cursor.execute("SELECT tweet FROM tweets WHERE id = ?", (tweet_id,))
        row = cursor.fetchone()
        if row is None:
            conn.close()
            logging.error(f"Tweet with ID {tweet_id} not found.")
            return jsonify({"status": "error", "message": "Tweet not found."}), 404

        tweet_text = row["tweet"]

        # Post the tweet using tweet_message
        response = tweet_message(tweet_text)

        # Check if the tweet was posted successfully
        if "errors" in response:
            conn.close()
            logging.error(f"Twitter API error: {response}")
            return jsonify({"status": "error", "message": "Failed to post tweet."}), 500

        # Update the tweet status to 'posted' and remove scheduled_time
        cursor.execute(
            "UPDATE tweets SET status = 'posted', scheduled_time = NULL WHERE id = ?",
            (tweet_id,),
        )
        conn.commit()
        conn.close()
        logging.debug(f"Tweet {tweet_id} posted immediately.")
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error("Error in post_now_tweet", exc_info=e)
        print("[ERROR post_now_tweet]:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/update_schedule", methods=["POST"])
def update_schedule():
    try:
        logging.debug("Update schedule endpoint called.")
        data = request.json
        tweet_id = data.get("id")
        new_scheduled_time_str = data.get("scheduled_time")

        if not tweet_id or not new_scheduled_time_str:
            logging.error("Invalid data received for update_schedule.")
            return (
                jsonify({"status": "error", "message": "Invalid data provided."}),
                400,
            )

        # Try multiple datetime formats
        formats_to_try = [
            "%Y-%m-%dT%H:%M",  # Standard ISO format
            "%Y-%m-%d %H:%M",  # Space-separated format
            "%Y-%m-%d %H:%M:%S",  # With seconds
        ]

        new_scheduled_time = None
        for date_format in formats_to_try:
            try:
                new_scheduled_time = datetime.strptime(
                    new_scheduled_time_str, date_format
                )
                break
            except ValueError:
                continue

        if new_scheduled_time is None:
            logging.error(f"Could not parse date: {new_scheduled_time_str}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Invalid date format. Expected format: YYYY-MM-DD HH:MM",
                    }
                ),
                400,
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        # Rest of your existing code...
        cursor.execute("SELECT status FROM tweets WHERE id = ?", (tweet_id,))
        row = cursor.fetchone()
        if row is None:
            conn.close()
            return jsonify({"status": "error", "message": "Tweet not found."}), 404

        if row["status"] != "approved":
            conn.close()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Only approved tweets can be rescheduled.",
                    }
                ),
                400,
            )

        cursor.execute(
            "UPDATE tweets SET scheduled_time = ? WHERE id = ?",
            (new_scheduled_time.strftime("%Y-%m-%d %H:%M:%S"), tweet_id),
        )
        conn.commit()
        conn.close()

        logging.debug(f"Tweet {tweet_id} rescheduled to {new_scheduled_time}.")
        return jsonify(
            {
                "status": "success",
                "scheduled_time": new_scheduled_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    except Exception as e:
        logging.error("Error in update_schedule", exc_info=e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    init_db()
    restore_scheduled_tweets()

    scheduler = BackgroundScheduler()
    random_interval = random.randint(720, 1200)
    logging.info(f"Setting scheduler interval to {random_interval} seconds")

    scheduler.add_job(
        post_scheduled_tweets, "interval", seconds=random_interval, jitter=120
    )
    scheduler.start()

    # Register the cleanup handler
    atexit.register(lambda: scheduler.shutdown() if scheduler.running else None)

    # Let Digital Ocean set the port
    port = int(os.getenv("PORT", "8080"))
    if os.getenv("FLASK_ENV") == "development":
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        app.run(host="0.0.0.0", port=port)
