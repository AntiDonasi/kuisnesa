import os
import io
import base64
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask

# ==========================
# Lokasi folder static
# ==========================
BASE_DIR = os.path.join(os.path.dirname(__file__), "static")


# ==========================
# Export jawaban ke CSV
# ==========================
def export_responses(responses, filename: str):
    # Ambil semua pertanyaan unik
    questions = list({r.question.text for r in responses})

    # Buat mapping user → jawaban per pertanyaan
    data = {}
    for r in responses:
        uid = r.user.email
        if uid not in data:
            data[uid] = {
                "Nama": r.user.nama,
                "Email": r.user.email
            }
        data[uid][r.question.text] = r.answer

    df = pd.DataFrame(list(data.values()))
    cols = ["Nama", "Email"] + questions
    df = df.reindex(columns=cols)

    dir_path = os.path.join(BASE_DIR, "exports")
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, filename)
    df.to_csv(file_path, index=False)

    print(f"[EXPORT] Saved CSV: {file_path}")
    return file_path   # ⬅️ Kembalikan path asli, bukan "/static/..."


# ==========================
# Generate grafik distribusi jawaban
# ==========================
def chart_distribution(responses, filename: str):
    counts = {}
    for r in responses:
        key = f"{r.question.text} - {r.answer}"
        counts[key] = counts.get(key, 0) + 1

    if not counts:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(list(counts.keys()), list(counts.values()), color="#2563eb")
    ax.set_xlabel("Jumlah Jawaban")
    ax.set_ylabel("Pertanyaan - Jawaban")
    plt.tight_layout()

    dir_path = os.path.join(BASE_DIR, "charts")
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, filename)
    plt.savefig(file_path)
    plt.close()

    print(f"[CHART] Saved chart: {file_path}")
    return f"/static/charts/{filename}"  # ✅ ini URL, dipakai di template


# ==========================
# Generate Wordcloud
# ==========================
def generate_wordcloud(responses, filename: str):
    text = " ".join([r.answer for r in responses if r.answer])
    if not text.strip():
        return None

    wc = WordCloud(width=800, height=400, background_color="white").generate(text)

    dir_path = os.path.join(BASE_DIR, "charts")
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, filename)
    wc.to_file(file_path)

    print(f"[WORDCLOUD] Saved wordcloud: {file_path}")
    return f"/static/charts/{filename}"  # ✅ return URL untuk template


# ==========================
# Generate QR dengan hiasan (base64 inline)
# ==========================
def generate_qr_base64(url: str):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=RadialGradiantColorMask()
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    base64_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    print("[QR] Generated QR base64")
    return f"data:image/png;base64,{base64_str}"
