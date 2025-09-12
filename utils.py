import os, pandas as pd, matplotlib.pyplot as plt
from wordcloud import WordCloud

BASE_DIR = "static"

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
    text = " ".join([r.answer for r in responses])
    wc = WordCloud(width=800, height=400, background_color="white").generate(text)
    path = os.path.join(BASE_DIR, "charts", filename)
    wc.to_file(path)
    return path
