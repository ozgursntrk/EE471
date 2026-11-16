"""Image Embedder: turns an image into a vector; similar images give similar vectors.

    python image_embedder.py
Compares burger.jpg with a cropped burger (similar) and with cat_and_dog.jpg (different).
"""
import cv2
import mediapipe as mp

from common import BaseOptions, model, sample, save, title, vision

burger = cv2.imread(sample("burger.jpg"))
h, w = burger.shape[:2]
crop = burger[h // 6: h * 5 // 6, w // 6: w * 5 // 6]      # the middle of the burger image
save(crop, "burger_crop.jpg")


def to_mp(bgr):
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


options = vision.ImageEmbedderOptions(
    base_options=BaseOptions(model_asset_path=model("mobilenet_v3_small.tflite")),
    l2_normalize=True,
)
with vision.ImageEmbedder.create_from_options(options) as embedder:
    e_burger = embedder.embed(to_mp(burger)).embeddings[0]
    e_crop = embedder.embed(to_mp(crop)).embeddings[0]
    e_pets = embedder.embed(mp.Image.create_from_file(sample("cat_and_dog.jpg"))).embeddings[0]

title("Image Embedder")
print(f"Embedding size: {len(e_burger.embedding)} numbers")
print(f"burger vs cropped burger : {vision.ImageEmbedder.cosine_similarity(e_burger, e_crop):.3f}")
print(f"burger vs cat and dog    : {vision.ImageEmbedder.cosine_similarity(e_burger, e_pets):.3f}")
print("(1.0 = identical, close to 0 = unrelated)")
