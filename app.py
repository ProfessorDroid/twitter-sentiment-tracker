import streamlit as st
import tweepy
import pandas as pd
from textblob import TextBlob
from dotenv import load_dotenv
import os
import re

# This function creates the client and caches it as a "resource".
# It will only run ONCE, and all users will share this one client.
@st.cache_resource
def get_tweepy_client():
    load_dotenv()
    BEARER_TOKEN = os.getenv("BEARER_TOKEN")
    
    if not BEARER_TOKEN:
        st.error("BEARER_TOKEN not found. Please check your Streamlit Secrets.")
        st.stop()
    
    try:
        # We pass wait_on_rate_limit=True
        client = tweepy.Client(BEARER_TOKEN, wait_on_rate_limit=True)
        return client
    except Exception as e:
        st.error(f"Error authenticating with Twitter: {e}")
        st.stop()

# --- Text processing functions ---

def clean_tweet(tweet):
    # Using a raw string (r"...") fixes the SyntaxWarning
    return ' '.join(re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

def get_tweet_sentiment(tweet):
    analysis = TextBlob(clean_tweet(tweet))
    if analysis.sentiment.polarity > 0:
        return 'Positive'
    elif analysis.sentiment.polarity == 0:
        return 'Neutral'
    else:
        return 'Negative'

def get_sentiment_polarity(tweet):
    analysis = TextBlob(clean_tweet(tweet))
    return analysis.sentiment.polarity

# --- Data fetching function ---

# This function is cached for 10 minutes (600 seconds)
# It now works because the '_client' it receives is the *same* cached object every time
@st.cache_data(ttl=600)
def fetch_tweets(_client, query, count=50):
    tweets = []
    try:
        response = _client.search_recent_tweets(
            query=query, 
            max_results=count, 
            expansions=['author_id'],
            user_fields=['username'],
            tweet_fields=['created_at']
        )
        
        if response.data:
            users = {user.id: user for user in response.includes['users']}
            
            for tweet in response.data:
                parsed_tweet = {}
                user = users[tweet.author_id]
                
                parsed_tweet['text'] = tweet.text
                parsed_tweet['sentiment'] = get_tweet_sentiment(tweet.text)
                parsed_tweet['polarity'] = get_sentiment_polarity(tweet.text)
                parsed_tweet['user'] = user.username
                parsed_tweet['url'] = f"https://twitter.com/{user.username}/status/{tweet.id}"
                
                tweets.append(parsed_tweet)
        
        return tweets

    except Exception as e:
        st.error(f"Error fetching tweets: {e}")
        return None

# --- Main app logic ---

def main():
    st.set_page_config(page_title="Twitter Sentiment Tracker", layout="wide")
    st.title("🐦 Twitter Sentiment Tracker (v2 API)")
    st.markdown("A real-time dashboard to analyze public sentiment on any topic.")

    # Get the ONE, cached client
    client = get_tweepy_client()

    st.sidebar.header("Search Parameters")
    query = st.sidebar.text_input("Enter a topic or hashtag (e.g., #Python)", "#Python")
    count = st.sidebar.slider("Number of Tweets to Analyze (10-100)", 10, 100, 50)
    
    if st.sidebar.button("Analyze Sentiment"):
        if query:
            full_query = f"{query} lang:en -is:retweet"
            
            with st.spinner(f"Fetching and analyzing {count} tweets for '{query}'..."):
                # Pass the cached client to the cached data function
                tweets = fetch_tweets(client, full_query, count)
                
                if tweets:
                    df = pd.DataFrame(tweets)
                    
                    st.subheader(f"Overall Sentiment Analysis")
                    sentiment_counts = df['sentiment'].value_counts()
                    sentiment_df = pd.DataFrame({'Sentiment': sentiment_counts.index, 'Tweets': sentiment_counts.values})
                    
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.metric(label="Total Tweets Analyzed", value=len(df))
                        st.dataframe(sentiment_counts)
                    
                    with col2:
                        if not sentiment_df.empty:
                            st.bar_chart(sentiment_df.set_index('Sentiment'))
                        else:
                            st.warning("No sentiments to plot.")

                    st.subheader("Raw Tweet Data")
                    st.dataframe(df[['user', 'text', 'sentiment', 'polarity', 'url']], use_container_width=True)

                    st.subheader("Random Positive Tweets")
                    positive_tweets_series = df[df['sentiment'] == 'Positive']['text']
                    if not positive_tweets_series.empty:
                        for t in positive_tweets_series.sample(min(5, len(positive_tweets_series))).tolist():
                            st.markdown(f"> {t}")
                    else:
                        st.info("No positive tweets found in this batch.")

                    st.subheader("Random Negative Tweets")
                    negative_tweets_series = df[df['sentiment'] == 'Negative']['text']
                    if not negative_tweets_series.empty:
                        for t in negative_tweets_series.sample(min(5, len(negative_tweets_series))).tolist():
                            st.markdown(f"> {t}")
                    else:
                        st.info("No negative tweets found in this batch.")
                
                else:
                    st.warning("No tweets found for that query. Try another term.")
        else:
            st.sidebar.warning("Please enter a search term.")

if __name__ == "__main__":
    main()