"""2) Text -> tokens -> numbers (encoding), and numbers -> text (decoding)."""
from transformers import AutoTokenizer

from common import CHECKPOINT, title

tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT)
text = "Using a Transformer network is simple"

tokens = tokenizer.tokenize(text)              # split into tokens (sub-words)
ids = tokenizer.convert_tokens_to_ids(tokens)  # tokens -> vocabulary numbers
decoded = tokenizer.decode(ids)                # numbers -> text again

title("Encoding and decoding")
print(f"Text    : {text}")
print(f"Tokens  : {tokens}")
print(f"IDs     : {ids}")
print(f"Decoded : {decoded}")
