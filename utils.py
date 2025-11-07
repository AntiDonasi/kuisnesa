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
    """Create distribution chart from responses"""
    if not responses:
        # Create empty chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=20, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
    else:
        counts = {}
        for r in responses:
            answer = str(r.answer) if r.answer else "No answer"
            counts[answer] = counts.get(answer, 0) + 1

        # Sort by count
        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:20])  # Top 20

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(range(len(sorted_counts)), list(sorted_counts.values()),
                      color='#3b82f6', edgecolor='#1e40af', linewidth=1.5)

        # Styling
        ax.set_xticks(range(len(sorted_counts)))
        ax.set_xticklabels([k[:30] + '...' if len(k) > 30 else k for k in sorted_counts.keys()],
                          rotation=45, ha='right', fontsize=10)
        ax.set_ylabel('Jumlah Respons', fontsize=12, fontweight='bold')
        ax.set_title('Distribusi Jawaban Responden', fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def generate_wordcloud(responses, filename: str):
    """Generate word cloud from text responses"""
    texts = preprocess_responses(responses)
    text = " ".join(texts) if texts else "no data available"

    if len(text.strip()) < 10:
        text = "no sufficient data for wordcloud generation"

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        colormap='viridis',
        max_words=100,
        relative_scaling=0.5,
        min_font_size=10
    ).generate(text)

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # Save with matplotlib for better quality
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Word Cloud - Kata Populer dalam Jawaban', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    return path

# ============= ADDITIONAL VISUALIZATIONS =============
def create_pie_chart(responses, filename: str):
    """Create pie chart for response distribution"""
    if not responses:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=20, color='gray')
        ax.axis('off')
    else:
        counts = {}
        for r in responses:
            answer = str(r.answer) if r.answer else "No answer"
            counts[answer] = counts.get(answer, 0) + 1

        # Limit to top 10 for readability
        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Set3(range(len(sorted_counts)))
        wedges, texts, autotexts = ax.pie(
            sorted_counts.values(),
            labels=[k[:20] + '...' if len(k) > 20 else k for k in sorted_counts.keys()],
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10, 'weight': 'bold'}
        )

        ax.set_title('Distribusi Jawaban (Pie Chart)', fontsize=14, fontweight='bold', pad=20)

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def create_response_timeline(responses, filename: str):
    """Create timeline of responses (if response has timestamp)"""
    # This is a placeholder - would need timestamp field in Response model
    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.text(0.5, 0.5, 'Timeline visualization\n(requires timestamp data)',
            ha='center', va='center', fontsize=16, color='gray')
    ax.axis('off')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    return path
