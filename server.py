from flask import Flask, request, render_template_string, redirect
import csv, os
from twitter_utils import tweet_message

app = Flask(__name__)

HTML_TEMPLATE = """
<html>
<head>
<style>
  .tweet-table {
    border-collapse: collapse;
    width: 80%%;
    margin: 20px auto;
  }
  .tweet-table th, .tweet-table td {
    border: 1px solid #ccc;
    padding: 8px;
    text-align: left;
  }
  .tweet-table tr:nth-child(even) {
    background-color: #f2f2f2;
  }
  .tweet-table th {
    background-color: #4CAF50;
    color: white;
  }
  textarea[name="tweet"] {
    width: 300px;
    height: 80px;
  }
</style>
</head>
<body>
<h2 style="text-align:center;">Tweet Manager</h2>
<form style="text-align:center;" method="POST" action="/add">
  <label for="tweet">New Tweet:</label><br>
  <textarea name="tweet"></textarea><br><br>
  <input type="submit" value="Add Tweet">
</form>
<hr/>
<table class="tweet-table">
  <tr><th>Tweet</th><th>Approved</th><th>Action</th></tr>
  <!-- ...existing code for table rows... -->
  {% for row in tweets %}
    <tr>
      <td>{{row['tweets']}}</td>
      <td>{{row['approved']}}</td>
      <td>
        <a href="/toggle/{{loop.index0}}">Toggle</a>
      </td>
    </tr>
  {% endfor %}
</table>
</body>
</html>
"""

CSV_FILE = "tweets.csv"

def read_tweets():
    rows = []
    if not os.path.exists(CSV_FILE):
        return rows
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure 'approved' key exists
            if "approved" not in row:
                row["approved"] = "No"
            rows.append(row)
    return rows

def write_tweets(rows):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tweets","approved"])
        writer.writeheader()
        writer.writerows(rows)

@app.route("/", methods=["GET"])
def home():
    tweets = read_tweets()
    return render_template_string(HTML_TEMPLATE, tweets=tweets)

@app.route("/add", methods=["POST"])
def add():
    new_tweet = request.form.get("tweet","").strip()
    if new_tweet:
        tweets = read_tweets()
        tweets.append({"tweets": new_tweet, "approved": "No"})
        write_tweets(tweets)
    return redirect("/")

@app.route("/toggle/<int:index>", methods=["GET"])
def toggle(index):
    tweets = read_tweets()
    if 0 <= index < len(tweets):
        tweets[index]["approved"] = ("No" if tweets[index]["approved"] == "Yes" else "Yes")
        if tweets[index]["approved"] == "Yes":
            resp = tweet_message(tweets[index]["tweets"])
            app.logger.info(f"Debug: tweet_message response: {resp}")
        write_tweets(tweets)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
