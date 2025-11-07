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

plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#f8fafc'
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.size'] = 11
sns.set_palette("husl")

def clean_text(text: str) -> str:
    return [clean_text(r.answer) for r in responses if r.answer]

def lda_topic_modeling(responses, n_topics=3, n_words=5):
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

def analyze_sentiment(responses):
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

def export_responses(responses, filename: str):
    data = [{"Nama": r.user.nama, "Email": r.user.email,
             "Pertanyaan": r.question.text, "Jawaban": r.answer} for r in responses]
    df = pd.DataFrame(data)
    path = os.path.join(BASE_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    return path


def chart_distribution(responses, filename: str):
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
    sentiment_data = analyze_sentiment(responses)

    if not sentiment_data['details']:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'Tidak ada data sentimen', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        sentiments = sentiment_data['summary']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

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
    if not responses:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Tidak ada data', ha='center', va='center',
                fontsize=24, color='#94a3b8', weight='bold')
        ax.axis('off')
    else:
        word_counts = [len(r.answer.split()) for r in responses if r.answer]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        ax1.hist(word_counts, bins=20, color='#3b82f6', edgecolor='white',
                linewidth=1.5, alpha=0.8)
        ax1.set_xlabel('Jumlah Kata', fontsize=12, weight='bold')
        ax1.set_ylabel('Frekuensi', fontsize=12, weight='bold')
        ax1.set_title('📏 Distribusi Panjang Jawaban', fontsize=14, weight='bold', pad=15)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

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
    import qrcode

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    path = os.path.join(BASE_DIR, "qr", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)

    return path
