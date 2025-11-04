import os, pandas as pd, matplotlib.pyplot as plt, re
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from textblob import TextBlob
import numpy as np

BASE_DIR = "static"

# ============= TEXT CLEANING & PREPROCESSING =============
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters (keep Indonesian letters)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text.strip()

def preprocess_responses(responses):
    """Clean all response texts"""
    return [clean_text(r.answer) for r in responses if r.answer]

# ============= LDA TOPIC MODELING =============
def lda_topic_modeling(responses, n_topics=3, n_words=5):
    """
    Perform LDA topic modeling on responses
    Returns: list of topics with top words
    """
    texts = preprocess_responses(responses)

    if len(texts) < n_topics:
        return {"error": "Not enough responses for topic modeling"}

    # Create document-term matrix
    vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
    doc_term_matrix = vectorizer.fit_transform(texts)

    # Fit LDA model
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(doc_term_matrix)

    # Extract topics
    feature_names = vectorizer.get_feature_names_out()
    topics = []

    for topic_idx, topic in enumerate(lda.components_):
        top_words_idx = topic.argsort()[-n_words:][::-1]
        top_words = [feature_names[i] for i in top_words_idx]
        topics.append({
            "topic_id": topic_idx + 1,
            "words": top_words,
            "weights": [float(topic[i]) for i in top_words_idx]
        })

    return {"topics": topics, "n_responses": len(texts)}

# ============= KEYWORD EXTRACTION =============
def extract_keywords(responses, top_n=10):
    """Extract top keywords using TF-IDF"""
    texts = preprocess_responses(responses)

    if len(texts) == 0:
        return {"keywords": []}

    vectorizer = TfidfVectorizer(max_df=0.8, min_df=1, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)

    # Get feature names and their scores
    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()

    # Sort by score
    top_indices = tfidf_scores.argsort()[-top_n:][::-1]
    keywords = [{"word": feature_names[i], "score": float(tfidf_scores[i])}
                for i in top_indices]

    return {"keywords": keywords}

# ============= SENTIMENT ANALYSIS =============
def analyze_sentiment(responses):
    """Analyze sentiment of responses (positive/neutral/negative)"""
    sentiments = {"positive": 0, "neutral": 0, "negative": 0}
    details = []

    for r in responses:
        if not r.answer:
            continue

        blob = TextBlob(r.answer)
        polarity = blob.sentiment.polarity

        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        sentiments[sentiment] += 1
        details.append({
            "answer": r.answer,
            "sentiment": sentiment,
            "polarity": round(polarity, 3)
        })

    return {
        "summary": sentiments,
        "details": details,
        "total": len(details)
    }

# ============= TEXT STATISTICS =============
def text_statistics(responses):
    """Calculate text statistics from responses"""
    texts = [r.answer for r in responses if r.answer]

    if not texts:
        return {"error": "No text data available"}

    word_counts = [len(text.split()) for text in texts]
    char_counts = [len(text) for text in texts]

    return {
        "total_responses": len(texts),
        "avg_words": round(np.mean(word_counts), 2),
        "avg_chars": round(np.mean(char_counts), 2),
        "min_words": min(word_counts),
        "max_words": max(word_counts),
        "total_words": sum(word_counts)
    }

# ============= ORIGINAL FUNCTIONS (UPDATED) =============
def export_responses(responses, filename: str):
    data = [{"Nama": r.user.nama, "Email": r.user.email, "Pertanyaan": r.question.text, "Jawaban": r.answer} for r in responses]
    df = pd.DataFrame(data)
    path = os.path.join(BASE_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path

def chart_distribution(responses, filename: str):
    counts = {}
    for r in responses:
        counts[r.answer] = counts.get(r.answer, 0) + 1
    fig, ax = plt.subplots()
    ax.bar(counts.keys(), counts.values())
    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path

def generate_wordcloud(responses, filename: str):
    texts = preprocess_responses(responses)
    text = " ".join(texts) if texts else "no data"
    wc = WordCloud(width=800, height=400, background_color="white").generate(text)
    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wc.to_file(path)
    return path
