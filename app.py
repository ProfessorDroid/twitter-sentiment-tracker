import streamlit as st
import pandas as pd
import re
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
from collections import Counter
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt

analyzer = SentimentIntensityAnalyzer()

@st.cache_resource
def load_spacy_model():
    try:
        nlp = spacy.load("en_core_web_sm", disable=['parser', 'tagger', 'lemmatizer'])
        return nlp
    except OSError:
        st.error("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm' first.")
        st.stop()

nlp = load_spacy_model()

def clean_tweet_for_wordcloud(tweet):
    tweet = str(tweet)
    tweet = re.sub(r'RT[\s]+', '', tweet)
    tweet = re.sub(r'https?:\/\/\S+', '', tweet)
    tweet = re.sub(r'@[A-Za-z0-9]+', '', tweet)
    tweet = re.sub(r'[^A-Za-z\s]', '', tweet)
    tweet = tweet.lower()
    return ' '.join(tweet.split())

def clean_tweet_for_sentiment(tweet):
     tweet = str(tweet)
     return ' '.join(re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

def get_vader_sentiment_label(tweet):
    cleaned_tweet = clean_tweet_for_sentiment(tweet)
    vs = analyzer.polarity_scores(cleaned_tweet)
    if vs['compound'] >= 0.05: return 'Positive'
    elif vs['compound'] <= -0.05: return 'Negative'
    else: return 'Neutral'

def get_vader_compound_score(tweet):
    cleaned_tweet = clean_tweet_for_sentiment(tweet)
    vs = analyzer.polarity_scores(cleaned_tweet)
    return vs['compound']

def extract_entities(text):
    doc = nlp(str(text))
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

@st.cache_data
def load_data(file_path="tweets.csv"):
    try:
        df = pd.read_csv(file_path)
        if 'text' in df.columns:
            df['text'] = df['text'].fillna('')
            if 'sentiment' not in df.columns or df['sentiment'].isnull().any():
                 df['sentiment'] = df['text'].apply(get_vader_sentiment_label)
            if 'vader_score' not in df.columns or df['vader_score'].isnull().any():
                 df['vader_score'] = df['text'].apply(get_vader_compound_score)
            if 'entities' not in df.columns or not isinstance(df.get('entities', [None])[0], list):
                 df['entities'] = df['text'].apply(extract_entities)
            if 'polarity' in df.columns:
                df = df.drop(columns=['polarity'])
            if 'cleaned_text' not in df.columns:
                 df['cleaned_text'] = df['text'].apply(clean_tweet_for_wordcloud)
        else:
             st.error("CSV file must contain a 'text' column.")
             st.stop()
        return df
    except FileNotFoundError:
        st.error(f"Error: The file {file_path} was not found.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

@st.cache_data
def generate_word_cloud(texts_series):
    full_text = " ".join(texts_series.astype(str))
    custom_stopwords = set(STOPWORDS)

    if full_text.strip():
        wordcloud = WordCloud(width=800, height=400,
                            background_color='white',
                            stopwords=custom_stopwords,
                            min_font_size=10).generate(full_text)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        plt.tight_layout(pad=0)
        return fig
    else:
        return None

def main():
    st.set_page_config(page_title="Advanced Twitter Analysis", layout="wide")
    st.title("🐦 Advanced Twitter Sentiment, Entity & Word Cloud Tracker")
    st.markdown("Dashboard analyzing sentiment (VADER), extracting entities (spaCy), and visualizing word frequency from a saved dataset.")

    df_all_tweets = load_data()

    if df_all_tweets is None or df_all_tweets.empty:
        st.error("Failed to load tweet data. Cannot proceed.")
        return

    st.sidebar.header("Filter Parameters")
    available_topics = ["All Topics"] + sorted(df_all_tweets['topic'].unique().tolist())
    query_topic = st.sidebar.selectbox("Select a topic to analyze:", available_topics)

    if query_topic == "All Topics":
        df_filtered = df_all_tweets.copy()
        st.subheader("Overall Analysis (All Topics)")
    else:
        df_filtered = df_all_tweets[df_all_tweets['topic'] == query_topic].copy()
        st.subheader(f"Analysis for '{query_topic}'")

    if not df_filtered.empty:
        st.markdown("### Sentiment Analysis (VADER)")
        sentiment_counts = df_filtered['sentiment'].value_counts()
        sentiment_counts = sentiment_counts.reindex(['Positive', 'Neutral', 'Negative'], fill_value=0)
        sentiment_df = pd.DataFrame({'Sentiment': sentiment_counts.index, 'Tweets': sentiment_counts.values})
        col1_sent, col2_sent = st.columns([1, 2])
        with col1_sent:
            st.metric(label="Total Tweets Analyzed", value=len(df_filtered))
            st.dataframe(sentiment_counts)
        with col2_sent:
            st.bar_chart(sentiment_df.set_index('Sentiment'))

        st.markdown("### Named Entity Recognition (spaCy)")
        all_entities = []
        if 'entities' in df_filtered.columns and not df_filtered['entities'].isnull().all():
             for entity_list in df_filtered['entities']:
                 if isinstance(entity_list, list):
                     all_entities.extend(entity_list)
        if all_entities:
            entity_counts = Counter(all_entities)
            common_entities = entity_counts.most_common(20)
            entity_dict = {'PERSON': [], 'ORG': [], 'GPE': [], 'PRODUCT': [], 'EVENT': [], 'OTHER': []}
            for (text, label), count in common_entities:
                key = label if label in entity_dict else 'OTHER'
                entity_dict[key].append(f"{text} ({count})")
            col1_ner, col2_ner, col3_ner = st.columns(3)
            with col1_ner:
                st.markdown("**People (PERSON):**"); st.write(", ".join(entity_dict['PERSON']) if entity_dict['PERSON'] else "_None found_")
                st.markdown("**Products/Services (PRODUCT):**"); st.write(", ".join(entity_dict['PRODUCT']) if entity_dict['PRODUCT'] else "_None found_")
            with col2_ner:
                st.markdown("**Organizations (ORG):**"); st.write(", ".join(entity_dict['ORG']) if entity_dict['ORG'] else "_None found_")
                st.markdown("**Events (EVENT):**"); st.write(", ".join(entity_dict['EVENT']) if entity_dict['EVENT'] else "_None found_")
            with col3_ner:
                st.markdown("**Locations (GPE):**"); st.write(", ".join(entity_dict['GPE']) if entity_dict['GPE'] else "_None found_")
                st.markdown("**Other Common Entities:**"); st.write(", ".join(entity_dict['OTHER']) if entity_dict['OTHER'] else "_None found_")
        else:
            st.info("No named entities found in this selection.")

        st.markdown("### Common Words Cloud")
        if 'cleaned_text' in df_filtered.columns:
            wordcloud_fig = generate_word_cloud(df_filtered['cleaned_text'])
            if wordcloud_fig:
                 st.pyplot(wordcloud_fig, use_container_width=True)
            else:
                 st.info("Not enough text data to generate a word cloud for this selection.")
        else:
             st.warning("Cleaned text column not found for word cloud generation.")

        st.markdown("### Tweet Data with Scores")
        display_cols = ['user', 'text', 'sentiment', 'vader_score', 'url']
        existing_cols = [col for col in display_cols if col in df_filtered.columns]
        st.dataframe(df_filtered[existing_cols].style.format({'vader_score': "{:.2f}"}), use_container_width=True)

        st.subheader("Sample Positive Tweets")
        positive_tweets_series = df_filtered[df_filtered['sentiment'] == 'Positive']['text']
        if not positive_tweets_series.empty:
            num_samples = min(5, len(positive_tweets_series)); [st.markdown(f"> {t}") for t in positive_tweets_series.sample(num_samples).tolist()]
        else: st.info(f"No positive tweets found.")

        st.subheader("Sample Negative Tweets")
        negative_tweets_series = df_filtered[df_filtered['sentiment'] == 'Negative']['text']
        if not negative_tweets_series.empty:
             num_samples = min(5, len(negative_tweets_series)); [st.markdown(f"> {t}") for t in negative_tweets_series.sample(num_samples).tolist()]
        else: st.info(f"No negative tweets found.")

    else:
        st.warning(f"No tweets found in the dataset for the topic '{query_topic}'.")

if __name__ == "__main__":
    main()