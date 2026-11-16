"""Universal Embedder: puts texts AND images into the same vector space (EmbeddingGemma 440M).

    python universal_embedder.py
A text and an image with the same meaning get a high similarity.
"""
from common import BaseOptions, model, sample, title
import mediapipe as mp

UniversalEmbedder = mp.tasks.retrieval.UniversalEmbedder
options = mp.tasks.retrieval.UniversalEmbedderOptions(
    base_options=BaseOptions(model_asset_path=model("embeddinggemma-2-text-vision-440m.litertlm")),
    l2_normalize=True,
)
texts = ["a cheeseburger with fries", "a cat and a dog sitting together"]
images = ["burger.jpg", "cat_and_dog.jpg"]

with UniversalEmbedder.create_from_options(options) as embedder:
    text_vectors = [embedder.embed_text(t).embeddings[0] for t in texts]
    image_vectors = []
    for name in images:
        with open(sample(name), "rb") as f:
            image_vectors.append(embedder.embed_image(f.read()).embeddings[0])

title("Universal Embedder (text <-> image)")
print(f"Vector size: {len(text_vectors[0].embedding)}")
print(f"{'':36}" + "".join(f"{n:>18}" for n in images))
for t, tv in zip(texts, text_vectors):
    scores = [UniversalEmbedder.cosine_similarity(tv, iv) for iv in image_vectors]
    print(f"{t:36}" + "".join(f"{s:18.3f}" for s in scores))
