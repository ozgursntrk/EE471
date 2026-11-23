"""4) Truncation: cut sentences that are longer than the maximum length."""
from transformers import AutoTokenizer

from common import CHECKPOINT, title

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
text = "This is a very long sentence that has many more tokens than the model is allowed to read at once."

full = tokenizer(text)["input_ids"]
cut = tokenizer(text, truncation=True, max_length=10)["input_ids"]

title("Truncation (max_length=10)")
print(f"Full      ({len(full)} tokens): {tokenizer.decode(full)}")
print(f"Truncated ({len(cut)} tokens): {tokenizer.decode(cut)}")
print(f"Model limit: {tokenizer.model_max_length} tokens")
