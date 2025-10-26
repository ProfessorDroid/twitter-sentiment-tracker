import tweepy
import pandas as pd
from dotenv import load_dotenv
import os
import re
from textblob import TextBlob
import json

def clean_tweet(tweet):
    return ' '.join(re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

def get_tweet_sentiment(tweet):
    analysis = TextBlob(clean_tweet(tweet))
    if analysis.sentiment.polarity > 0: return 'Positive'
    elif analysis.sentiment.polarity == 0: return 'Neutral'
    else: return 'Negative'

def get_sentiment_polarity(tweet):
    analysis = TextBlob(clean_tweet(tweet))
    return analysis.sentiment.polarity

def fetch_one_batch():
    load_dotenv()
    BEARER_TOKEN = os.getenv("BEARER_TOKEN")
    
    if not BEARER_TOKEN:
        print("Error: BEARER_TOKEN not found in .env file.")
        return None

    try:
        client = tweepy.Client(BEARER_TOKEN, wait_on_rate_limit=False) 
        print("Authenticated successfully...")
    except Exception as e:
        print(f"Error authenticating: {e}")
        return None

    topic = "#Python"
    full_query = f"{topic} lang:en -is:retweet"
    all_tweets_data = []

    print(f"Attempting to fetch 50 tweets for: {topic}...")
    try:
        response = client.search_recent_tweets(
            query=full_query, 
            max_results=50, 
            expansions=['author_id'],
            user_fields=['username'],
            tweet_fields=['created_at']
        )
        
        if response.data:
            print(f"Success! Found {len(response.data)} tweets.")
            users = {}
            if 'users' in response.includes:
                 users = {user.id: user for user in response.includes['users']}
            
            for tweet in response.data:
                parsed_tweet = {}
                user = users.get(tweet.author_id)
                
                parsed_tweet['topic'] = topic 
                parsed_tweet['text'] = tweet.text
                parsed_tweet['sentiment'] = get_tweet_sentiment(tweet.text)
                parsed_tweet['polarity'] = get_sentiment_polarity(tweet.text)
                parsed_tweet['user'] = user.username if user else "UnknownUser"
                parsed_tweet['url'] = f"https://twitter.com/{user.username if user else 'i'}/status/{tweet.id}"
                
                all_tweets_data.append(parsed_tweet)
            return all_tweets_data
            
        else:
            print("No tweets found.")
            return None

    except tweepy.errors.TooManyRequests:
        print("\n--- RATE LIMIT HIT ---")
        print("The API is on cooldown. Please wait 15 minutes and try running this script again.")
        return None
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return None

if __name__ == "__main__":
    tweet_list = fetch_one_batch()
    
    if tweet_list:
        df = pd.DataFrame(tweet_list)
        df.to_csv("tweets.csv", index=False)
        print(f"\nSuccessfully saved {len(df)} tweets to tweets.csv")
    else:
        print("\nScript finished without saving data.")
