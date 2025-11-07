import os, pandas as pd, matplotlib.pyplot as plt, re
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from textblob import TextBlob
import numpy as np
from collections import Counter
import seaborn as sns
from datetime import datetime

BASE_DIR = "static"

# Set modern style for all plots
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#f8fafc'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.size'] = 11
sns.set_palette("husl")

# ============= TEXT CLEANING & PREPROCESSING =============
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text.strip()

def preprocess_responses(responses):
    """Clean all response texts"""
    return [clean_text(r.answer) for r in responses if r.answer]

# ============= LDA TOPIC MODELING =============
def lda_topic_modeling(responses, n_topics=3, n_words=5):
    """Perform LDA topic modeling on responses"""
    texts = preprocess_responses(responses)

    if len(texts) < n_topics:
        return {"error": "Not enough responses for topic modeling"}

    vectorizer = CountVectorizer(max_df=0.95, min_df=2, stop_words='english')
    doc_term_matrix = vectorizer.fit_transform(texts)

    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(doc_term_matrix)

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

    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = np.asarray(tfidf_matrix.sum(axis=0)).ravel()

    top_indices = tfidf_scores.argsort()[-top_n:][::-1]
    keywords = [{"word": feature_names[i], "score": float(tfidf_scores[i])}
                for i in top_indices]

    return {"keywords": keywords}

# ============= SENTIMENT ANALYSIS =============
def analyze_sentiment(responses):
    """Analyze sentiment of responses"""
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
        "total_words": sum(word_counts),
        "median_words": round(np.median(word_counts), 2),
        "std_words": round(np.std(word_counts), 2)
    }

# ============= EXPORT FUNCTION =============
def export_responses(responses, filename: str):
    data = [{"Nama": r.user.nama, "Email": r.user.email,
             "Pertanyaan": r.question.text, "Jawaban": r.answer} for r in responses]
    df = pd.DataFrame(data)
    path = os.path.join(BASE_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path

# ============= ENHANCED VISUALIZATIONS =============

def chart_distribution(responses, filename: str):
    """Create modern bar chart for response distribution"""
    if not responses:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Tidak ada data', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        counts = {}
        for r in responses:
            answer = str(r.answer) if r.answer else "Tidak ada jawaban"
            counts[answer] = counts.get(answer, 0) + 1

        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:20])

        fig, ax = plt.subplots(figsize=(14, 7))
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(sorted_counts)))
        bars = ax.bar(range(len(sorted_counts)), list(sorted_counts.values()),
                      color=colors, edgecolor='white', linewidth=2, alpha=0.85)

        ax.set_xticks(range(len(sorted_counts)))
        ax.set_xticklabels([k[:35] + '...' if len(k) > 35 else k for k in sorted_counts.keys()],
                          rotation=45, ha='right', fontsize=11, weight='medium')
        ax.set_ylabel('Jumlah Respons', fontsize=13, weight='bold', color='#1e293b')
        ax.set_title('📊 Distribusi Jawaban Responden', fontsize=16, weight='bold',
                    pad=20, color='#0f172a')
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom',
                   fontsize=10, weight='bold', color='#334155')

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def create_pie_chart(responses, filename: str):
    """Create modern donut chart for response distribution"""
    if not responses:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, 'Tidak ada data', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        counts = {}
        for r in responses:
            answer = str(r.answer) if r.answer else "Tidak ada jawaban"
            counts[answer] = counts.get(answer, 0) + 1

        sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:8])

        fig, ax = plt.subplots(figsize=(12, 9))
        colors = sns.color_palette("Set2", len(sorted_counts))

        wedges, texts, autotexts = ax.pie(
            sorted_counts.values(),
            labels=[k[:25] + '...' if len(k) > 25 else k for k in sorted_counts.keys()],
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 11, 'weight': 'bold'},
            pctdistance=0.85,
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')

        ax.set_title('🍩 Proporsi Jawaban', fontsize=16, weight='bold',
                    pad=20, color='#0f172a')

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def generate_wordcloud(responses, filename: str):
    """Generate modern word cloud"""
    texts = preprocess_responses(responses)
    text = " ".join(texts) if texts else "tidak ada data tersedia"

    if len(text.strip()) < 10:
        text = "tidak ada data yang cukup untuk visualisasi"

    wc = WordCloud(
        width=1400,
        height=700,
        background_color="white",
        colormap='plasma',
        max_words=120,
        relative_scaling=0.6,
        min_font_size=12,
        contour_width=2,
        contour_color='#cbd5e1'
    ).generate(text)

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('☁️ Word Cloud - Kata Populer', fontsize=16, weight='bold',
                pad=20, color='#0f172a')
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()

    return path

def create_sentiment_chart(responses, filename: str):
    """Create sentiment analysis visualization"""
    sentiment_data = analyze_sentiment(responses)

    if not sentiment_data['details']:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Tidak ada data sentimen', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        sentiments = sentiment_data['summary']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Bar chart
        colors_map = {'positive': '#22c55e', 'neutral': '#eab308', 'negative': '#ef4444'}
        colors = [colors_map[s] for s in sentiments.keys()]
        labels = ['😊 Positif', '😐 Netral', '😞 Negatif']

        bars = ax1.bar(range(len(sentiments)), sentiments.values(),
                      color=colors, edgecolor='white', linewidth=2, alpha=0.9)
        ax1.set_xticks(range(len(sentiments)))
        ax1.set_xticklabels(labels, fontsize=12, weight='bold')
        ax1.set_ylabel('Jumlah Respons', fontsize=12, weight='bold')
        ax1.set_title('📈 Distribusi Sentimen', fontsize=14, weight='bold', pad=15)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom',
                    fontsize=11, weight='bold')

        # Donut chart
        wedges, texts, autotexts = ax2.pie(
            sentiments.values(),
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 11, 'weight': 'bold'},
            wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')

        ax2.set_title('🎯 Proporsi Sentimen', fontsize=14, weight='bold', pad=15)

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def create_word_frequency_chart(responses, filename: str, top_n=15):
    """Create word frequency histogram"""
    texts = preprocess_responses(responses)

    if not texts:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Tidak ada data', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        all_words = ' '.join(texts).split()
        word_freq = Counter(all_words)

        # Remove common stopwords manually
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                    'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'tidak',
                    'yang', 'di', 'ke', 'dari', 'dan', 'atau', 'untuk', 'dengan', 'ini', 'itu'}
        word_freq = {k: v for k, v in word_freq.items() if k not in stopwords and len(k) > 2}

        top_words = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n])

        fig, ax = plt.subplots(figsize=(14, 7))
        colors = plt.cm.coolwarm(np.linspace(0.2, 0.8, len(top_words)))
        bars = ax.barh(range(len(top_words)), list(top_words.values()),
                       color=colors, edgecolor='white', linewidth=2, alpha=0.9)

        ax.set_yticks(range(len(top_words)))
        ax.set_yticklabels(list(top_words.keys()), fontsize=11, weight='medium')
        ax.set_xlabel('Frekuensi', fontsize=12, weight='bold')
        ax.set_title('📝 Kata Paling Sering Muncul', fontsize=16, weight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {int(width)}', ha='left', va='center',
                   fontsize=10, weight='bold', color='#334155')

        ax.invert_yaxis()

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def create_response_length_chart(responses, filename: str):
    """Create response length distribution"""
    if not responses:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Tidak ada data', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        word_counts = [len(r.answer.split()) for r in responses if r.answer]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Histogram
        ax1.hist(word_counts, bins=20, color='#3b82f6', edgecolor='white',
                linewidth=1.5, alpha=0.8)
        ax1.set_xlabel('Jumlah Kata', fontsize=12, weight='bold')
        ax1.set_ylabel('Frekuensi', fontsize=12, weight='bold')
        ax1.set_title('📏 Distribusi Panjang Jawaban', fontsize=14, weight='bold', pad=15)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # Box plot
        box = ax2.boxplot(word_counts, vert=True, patch_artist=True,
                         boxprops=dict(facecolor='#8b5cf6', alpha=0.7, linewidth=2),
                         whiskerprops=dict(linewidth=2, color='#6d28d9'),
                         capprops=dict(linewidth=2, color='#6d28d9'),
                         medianprops=dict(linewidth=2.5, color='#fbbf24'),
                         flierprops=dict(marker='o', markerfacecolor='#ef4444',
                                       markersize=8, alpha=0.6))

        ax2.set_ylabel('Jumlah Kata', fontsize=12, weight='bold')
        ax2.set_title('📊 Statistik Panjang Jawaban', fontsize=14, weight='bold', pad=15)
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.set_xticklabels(['Jawaban'])

        # Add statistics text
        stats_text = f"Min: {min(word_counts)}\nMaks: {max(word_counts)}\n"
        stats_text += f"Rata-rata: {np.mean(word_counts):.1f}\nMedian: {np.median(word_counts):.1f}"
        ax2.text(1.15, np.median(word_counts), stats_text, fontsize=10,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def create_top_contributors_chart(responses, filename: str, top_n=10):
    """Create chart showing top contributors by response count"""
    if not responses:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Tidak ada data', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        user_counts = {}
        for r in responses:
            user_name = r.user.nama if r.user.nama else r.user.email
            user_counts[user_name] = user_counts.get(user_name, 0) + 1

        top_users = dict(sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:top_n])

        fig, ax = plt.subplots(figsize=(14, 7))
        colors = plt.cm.Spectral(np.linspace(0.2, 0.8, len(top_users)))
        bars = ax.barh(range(len(top_users)), list(top_users.values()),
                       color=colors, edgecolor='white', linewidth=2, alpha=0.9)

        ax.set_yticks(range(len(top_users)))
        ax.set_yticklabels([k[:30] + '...' if len(k) > 30 else k for k in top_users.keys()],
                          fontsize=11, weight='medium')
        ax.set_xlabel('Jumlah Jawaban', fontsize=12, weight='bold')
        ax.set_title('👥 Kontributor Teratas', fontsize=16, weight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {int(width)}', ha='left', va='center',
                   fontsize=10, weight='bold', color='#334155')

        ax.invert_yaxis()

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def create_keyword_comparison_chart(responses, filename: str):
    """Create comparison chart of top keywords with scores"""
    keyword_data = extract_keywords(responses, top_n=12)

    if not keyword_data['keywords']:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Tidak ada data keyword', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        keywords = keyword_data['keywords']
        words = [k['word'] for k in keywords]
        scores = [k['score'] for k in keywords]

        fig, ax = plt.subplots(figsize=(14, 8))
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(words)))
        bars = ax.barh(range(len(words)), scores, color=colors,
                      edgecolor='white', linewidth=2, alpha=0.9)

        ax.set_yticks(range(len(words)))
        ax.set_yticklabels(words, fontsize=12, weight='medium')
        ax.set_xlabel('TF-IDF Score', fontsize=12, weight='bold')
        ax.set_title('🔑 Kata Kunci Penting (TF-IDF)', fontsize=16, weight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {width:.2f}', ha='left', va='center',
                   fontsize=10, weight='bold', color='#334155')

        ax.invert_yaxis()

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path

def create_comprehensive_stats_chart(responses, filename: str):
    """Create comprehensive statistics dashboard"""
    stats = text_statistics(responses)

    if 'error' in stats:
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.text(0.5, 0.5, 'Tidak ada data statistik', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Title
        fig.suptitle('📊 Dashboard Statistik Komprehensif', fontsize=18, weight='bold', y=0.98)

        # Total responses
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.text(0.5, 0.5, f"{stats['total_responses']}", ha='center', va='center',
                fontsize=48, weight='bold', color='#3b82f6')
        ax1.text(0.5, 0.15, 'Total Respons', ha='center', va='center',
                fontsize=14, weight='bold', color='#64748b')
        ax1.axis('off')
        ax1.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False,
                                    edgecolor='#3b82f6', linewidth=3, transform=ax1.transAxes))

        # Avg words
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.text(0.5, 0.5, f"{stats['avg_words']:.1f}", ha='center', va='center',
                fontsize=48, weight='bold', color='#8b5cf6')
        ax2.text(0.5, 0.15, 'Rata-rata Kata', ha='center', va='center',
                fontsize=14, weight='bold', color='#64748b')
        ax2.axis('off')
        ax2.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False,
                                    edgecolor='#8b5cf6', linewidth=3, transform=ax2.transAxes))

        # Total words
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.text(0.5, 0.5, f"{stats['total_words']}", ha='center', va='center',
                fontsize=48, weight='bold', color='#f59e0b')
        ax3.text(0.5, 0.15, 'Total Kata', ha='center', va='center',
                fontsize=14, weight='bold', color='#64748b')
        ax3.axis('off')
        ax3.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False,
                                    edgecolor='#f59e0b', linewidth=3, transform=ax3.transAxes))

        # Word length distribution
        ax4 = fig.add_subplot(gs[1, :])
        word_stats = {
            'Min': stats['min_words'],
            'Median': stats['median_words'],
            'Rata-rata': stats['avg_words'],
            'Maks': stats['max_words']
        }
        colors = ['#ef4444', '#eab308', '#22c55e', '#3b82f6']
        bars = ax4.bar(range(len(word_stats)), list(word_stats.values()),
                      color=colors, edgecolor='white', linewidth=2, alpha=0.9)
        ax4.set_xticks(range(len(word_stats)))
        ax4.set_xticklabels(list(word_stats.keys()), fontsize=12, weight='bold')
        ax4.set_ylabel('Jumlah Kata', fontsize=12, weight='bold')
        ax4.set_title('Distribusi Panjang Jawaban', fontsize=14, weight='bold', pad=15)
        ax4.grid(axis='y', alpha=0.3, linestyle='--')
        ax4.spines['top'].set_visible(False)
        ax4.spines['right'].set_visible(False)

        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom',
                    fontsize=11, weight='bold')

        # Character stats
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.text(0.5, 0.5, f"{stats['avg_chars']:.0f}", ha='center', va='center',
                fontsize=40, weight='bold', color='#10b981')
        ax5.text(0.5, 0.15, 'Rata-rata Karakter', ha='center', va='center',
                fontsize=12, weight='bold', color='#64748b')
        ax5.axis('off')
        ax5.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False,
                                    edgecolor='#10b981', linewidth=3, transform=ax5.transAxes))

        # Std deviation
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.text(0.5, 0.5, f"{stats['std_words']:.1f}", ha='center', va='center',
                fontsize=40, weight='bold', color='#ec4899')
        ax6.text(0.5, 0.15, 'Std Deviasi Kata', ha='center', va='center',
                fontsize=12, weight='bold', color='#64748b')
        ax6.axis('off')
        ax6.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False,
                                    edgecolor='#ec4899', linewidth=3, transform=ax6.transAxes))

        # Info box
        ax7 = fig.add_subplot(gs[2, 2])
        info_text = "📈 Statistik Ringkas\n\n"
        info_text += f"• Jawaban terpendek: {stats['min_words']} kata\n"
        info_text += f"• Jawaban terpanjang: {stats['max_words']} kata\n"
        info_text += f"• Median: {stats['median_words']:.1f} kata\n"
        info_text += f"• Total karakter: {stats['avg_chars'] * stats['total_responses']:.0f}"
        ax7.text(0.1, 0.5, info_text, ha='left', va='center',
                fontsize=10, weight='medium', color='#1e293b',
                bbox=dict(boxstyle='round', facecolor='#f1f5f9', alpha=0.8, pad=1))
        ax7.axis('off')

    path = os.path.join(BASE_DIR, "charts", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return path
