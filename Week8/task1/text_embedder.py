"""Text Embedder: sentence -> vector; sentences with similar meaning get similar vectors.

    python text_embedder.py
"""
from common import BaseOptions, model, title
import mediapipe as mp

SENTENCES = [
    "The cat is sleeping on the sofa.",
    "A kitten is napping on the couch.",
    "The stock market fell sharply today.",
]

TextEmbedder = mp.tasks.text.TextEmbedder
options = mp.tasks.text.TextEmbedderOptions(
    base_options=BaseOptions(model_asset_path=model("universal_sentence_encoder.tflite")),
    l2_normalize=True,
)
with TextEmbedder.create_from_options(options) as embedder:
    vectors = [embedder.embed(s).embeddings[0] for s in SENTENCES]

title("Text Embedder (Universal Sentence Encoder)")
print(f"Vector size: {len(vectors[0].embedding)}")
for i in range(len(SENTENCES)):
    for j in range(i + 1, len(SENTENCES)):
        score = TextEmbedder.cosine_similarity(vectors[i], vectors[j])
        print(f"  {score:.3f}  '{SENTENCES[i]}'  vs  '{SENTENCES[j]}'")
