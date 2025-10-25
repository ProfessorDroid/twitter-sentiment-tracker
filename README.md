# Twitter Sentiment Tracker

A web application built with Python and Streamlit to analyze the real-time public sentiment of any topic, keyword, or hashtag from Twitter (X).

This project fetches live tweets, performs Natural Language Processing (NLP) to determine sentiment, and displays the results in an interactive dashboard.



## Features
* **Real-Time Data:** Fetches the latest tweets using the X API (v2).
* **Sentiment Analysis:** Classifies each tweet as Positive, Negative, or Neutral using `TextBlob`.
* **Interactive Dashboard:** Built with `Streamlit` for a clean, responsive UI.
* **Data Visualization:** Includes a bar chart of the overall sentiment distribution.
* **Dynamic Search:** Users can analyze any topic or hashtag they want.

## Tech Stack
* **Backend:** Python
* **Frontend:** Streamlit
* **Twitter API:** Tweepy (for X API v2)
* **Data Handling:** Pandas

## How to Run This Project Locally

### 1. Prerequisites
* Python 3.8+
* A Twitter (X) Developer Account with "Free" tier access.
* Your Bearer Token from the X Developer Portal.

### 2. Clone the Repository
```bash
git clone [https://github.com/ProfessorDroid/twitter-sentiment-tracker.git](https://github.com/ProfessorDroid/twitter-sentiment-tracker.git)
cd twitter-sentiment-tracker