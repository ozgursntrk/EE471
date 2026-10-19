from custom_classes import (
    Book, DVD, LibraryCollection, ItemNotFoundError, ItemStateError
)

library = LibraryCollection()

# --- add_item: id verir ve döndürür ---
dune_id = library.add_item(Book("Dune", "Frank Herbert", 412))
inter_id = library.add_item(DVD("Interstellar", "Christopher Nolan", 169))
orwell_id = library.add_item(Book("1984", "George Orwell", 328))
print("Added ids:", dune_id, inter_id, orwell_id)

# --- to_dict ---
print("\n--- to_dict ---")
for item in library.items:
    print(item.to_dict())

# --- get_item ---
print("\n--- get_item ---")
print(library.get_item(dune_id))
try:
    library.get_item(999)
except ItemNotFoundError as e:
    print("ItemNotFoundError:", e)

# --- checkout / return_item ---
print("\n--- checkout / return ---")
print(library.get_item(dune_id).checkout())
print(library.get_item(inter_id).checkout())   # DVD hatırlatması mesajda
try:
    library.get_item(dune_id).checkout()       # ikinci kez -> hata
except ItemStateError as e:
    print("ItemStateError:", e)

print(library.get_item(dune_id).return_item())
try:
    library.get_item(orwell_id).return_item()  # zaten rafta -> hata
except ItemStateError as e:
    print("ItemStateError:", e)

# --- list_items ---
print("\n--- list_items ---")
print("All:", [i.title for i in library.list_items()])
print("Available:", [i.title for i in library.list_items(available=True)])
print("Books:", [i.title for i in library.list_items(item_type="book")])
try:
    library.list_items(item_type="cd")
except ValueError as e:
    print("ValueError:", e)

# --- update_item ---
print("\n--- update_item ---")
library.update_item(orwell_id, title="Nineteen Eighty-Four", page_count=330)
print(library.get_item(orwell_id).to_dict())
try:
    library.update_item(orwell_id, id=50)      # id değiştirilemez
except ValueError as e:
    print("ValueError:", e)

# --- remove_item ---
print("\n--- remove_item ---")
try:
    library.remove_item(inter_id)              # DVD hâlâ dışarıda -> hata
except ItemStateError as e:
    print("ItemStateError:", e)

library.remove_item(dune_id)
print("Removed Dune. Left:", [i.title for i in library.list_items()])

# --- id'ler tekrar kullanılmıyor ---
new_id = library.add_item(Book("Hamlet", "William Shakespeare", 150))
print("New item id:", new_id, "(1 tekrar kullanılmadı)")