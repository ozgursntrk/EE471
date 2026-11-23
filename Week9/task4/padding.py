"""3) Padding: make sentences of different lengths the same length, so they fit in one tensor."""
from transformers import AutoTokenizer

from common import CHECKPOINT, title

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
sentences = ["I love this course.", "Padding makes all sentences in a batch equally long."]

title("Without padding")
for ids in tokenizer(sentences)["input_ids"]:
    print(f"  length {len(ids):>2}: {ids}")

title("padding=True (to the longest sentence)")
batch = tokenizer(sentences, padding=True)
for ids, mask in zip(batch["input_ids"], batch["attention_mask"]):
    print(f"  ids : {ids}\n  mask: {mask}")
print(f"Padding token: {tokenizer.pad_token} = {tokenizer.pad_token_id}; attention mask 0 = ignore it")
