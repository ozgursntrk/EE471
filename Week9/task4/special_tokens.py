"""5) Special tokens: [CLS] at the start and [SEP] at the end, plus adding our own token."""
from transformers import AutoTokenizer

from common import CHECKPOINT, title

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
text = "I love EE471"

with_special = tokenizer(text)["input_ids"]
without = tokenizer(text, add_special_tokens=False)["input_ids"]

title("Special tokens")
print(f"Without: {without} -> {tokenizer.decode(without)}")
print(f"With   : {with_special} -> {tokenizer.decode(with_special)}")
print(f"All special tokens: {tokenizer.all_special_tokens}")

# add our own special token: it is never split into pieces
print(f"\nBefore adding: {tokenizer.tokenize(text)}")
tokenizer.add_special_tokens({"additional_special_tokens": ["EE471"]})
print(f"After adding : {tokenizer.tokenize(text)}  (new id {tokenizer.convert_tokens_to_ids('EE471')})")
