from transformers import pipeline

print("Loading summarizer model (BART-large-CNN)...")

summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

def summarize(text):
    return summarizer(
        text,
        max_length=300,
        min_length=120,
        do_sample=False
    )[0]["summary_text"]