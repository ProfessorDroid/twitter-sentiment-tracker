import streamlit as st
import pandas as pd
from textblob import TextBlob
import re
import os # Keep os just in case, but no dotenv needed

# --- Text processing functions (still needed) ---

def clean_tweet(tweet):
    # Make sure tweet is a string
    tweet = str(tweet)
    # Using a raw string (r"...")
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

# --- Data Loading Function ---

# We use @st.cache_data to load the CSV only once for speed
@st.cache_data
def load_data(file_path="tweets.csv"):
    try:
        df = pd.read_csv(file_path)
        # Pre-calculate sentiment if not already done (optional, but good practice)
        # Check if columns exist before creating them
        if 'sentiment' not in df.columns:
            df['sentiment'] = df['text'].apply(get_tweet_sentiment)
        if 'polarity' not in df.columns:
             df['polarity'] = df['text'].apply(get_sentiment_polarity)
        return df
    except FileNotFoundError:
        st.error(f"Error: The file {file_path} was not found. Make sure 'tweets.csv' is in the same folder as app.py.")
        st.stop() # Stop the app if data can't be loaded
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# --- Main app logic ---

def main():
    st.set_page_config(page_title="Twitter Sentiment Demo", layout="wide")
    st.title("🐦 Twitter Sentiment Tracker (Demo Version)")
    st.markdown("A dashboard analyzing sentiment from a **saved dataset** of tweets.")
    st.warning("Note: This demo uses pre-collected data and does not fetch live tweets due to API limitations.")

    # Load the data from the CSV file
    df_all_tweets = load_data()

    if df_all_tweets is None or df_all_tweets.empty:
        st.error("Failed to load tweet data. Cannot proceed.")
        return # Exit if data loading failed

    st.sidebar.header("Search Parameters")
    
    # Get unique topics from the 'topic' column for the dropdown
    available_topics = df_all_tweets['topic'].unique().tolist()
    
    # Use a selectbox instead of text input
    query_topic = st.sidebar.selectbox("Select a topic to analyze:", available_topics)
    
    # We don't need a count slider anymore, we'll show all tweets for the topic

    if st.sidebar.button("Analyze Sentiment"):
        if query_topic:
            # --- Filter the DataFrame instead of fetching ---
            df_filtered = df_all_tweets[df_all_tweets['topic'] == query_topic].copy() # Use .copy() to avoid SettingWithCopyWarning
            
            if not df_filtered.empty:
                st.subheader(f"Sentiment Analysis for '{query_topic}'")
                
                sentiment_counts = df_filtered['sentiment'].value_counts()
                sentiment_df = pd.DataFrame({'Sentiment': sentiment_counts.index, 'Tweets': sentiment_counts.values})
                
                col1, col2 = st.columns([1, 2])

                with col1:
                    st.metric(label="Total Tweets Analyzed", value=len(df_filtered))
                    st.dataframe(sentiment_counts)
                
                with col2:
                    if not sentiment_df.empty:
                        st.bar_chart(sentiment_df.set_index('Sentiment'))
                    else:
                        st.warning("No sentiments to plot.")

                st.subheader("Tweet Data")
                # Ensure columns exist before displaying
                display_cols = ['user', 'text', 'sentiment', 'polarity', 'url']
                existing_cols = [col for col in display_cols if col in df_filtered.columns]
                st.dataframe(df_filtered[existing_cols], use_container_width=True)

                st.subheader("Sample Positive Tweets")
                positive_tweets_series = df_filtered[df_filtered['sentiment'] == 'Positive']['text']
                if not positive_tweets_series.empty:
                    # Show up to 5 samples
                    num_samples = min(5, len(positive_tweets_series))
                    for t in positive_tweets_series.sample(num_samples).tolist():
                        st.markdown(f"> {t}")
                else:
                    st.info(f"No positive tweets found for {query_topic}.")

                st.subheader("Sample Negative Tweets")
                negative_tweets_series = df_filtered[df_filtered['sentiment'] == 'Negative']['text']
                if not negative_tweets_series.empty:
                    num_samples = min(5, len(negative_tweets_series))
                    for t in negative_tweets_series.sample(num_samples).tolist():
                        st.markdown(f"> {t}")
                else:
                    st.info(f"No negative tweets found for {query_topic}.")
            
            else:
                st.warning(f"No tweets found in the dataset for the topic '{query_topic}'.")
        else:
            st.sidebar.warning("Please select a topic.")

if __name__ == "__main__":
    main()