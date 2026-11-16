"""Semantic Retriever: a small on-device search engine (vector database) for texts and images.

    python semantic_retriever.py ["your question"]
Searches by meaning, not by exact words.
"""
import sys

from common import BaseOptions, model, sample, title
import mediapipe as mp

R = mp.tasks.retrieval
DOCUMENTS = {
    "paris": "The capital of France is Paris. The Eiffel Tower is its most famous landmark.",
    "python": "Python is a programming language that is popular for data science and AI.",
    "iyte": "Izmir Institute of Technology is a university in Urla, near Izmir in Turkey.",
    "docker": "Docker packages an application and its dependencies into a container.",
}
QUERIES = [sys.argv[1]] if len(sys.argv) > 1 else [
    "Which city is the capital of France?",
    "How can I ship my app with all its libraries?",
    "something to eat",
]

embedder_options = R.UniversalEmbedderOptions(
    base_options=BaseOptions(model_asset_path=model("embeddinggemma-2-text-vision-440m.litertlm")),
    l2_normalize=True,
)
with R.UniversalEmbedder.create_from_options(embedder_options) as embedder:
    with R.SemanticRetriever.create_from_options(R.SemanticRetrieverOptions(embedder=embedder)) as retriever:
        for doc_id, text in DOCUMENTS.items():
            retriever.insert_document(doc_id=doc_id, text=text)
        retriever.insert_image(image_id="burger_photo", image_path=sample("burger.jpg"))

        title("Semantic Retriever")
        print(f"Records in the database: {retriever.get_all_record_ids()}")
        for query in QUERIES:
            print(f"\nQuery: {query}")
            for r in retriever.retrieve(query=query, limit=2, min_similarity=0.0):
                print(f"  {r.score:.3f}  [{r.id}] {(r.content or '')[:70]}")
