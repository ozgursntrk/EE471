from custom_classes import MediaItem, Book, DVD, LibraryCollection

library = LibraryCollection()

dune = Book("Dune", "Frank Herbert", 412)
interstellar = DVD("Interstellar", "Christopher Nolan", 169)
magazine = MediaItem("National Geographic", "Various")
orwell = Book("1984", "George Orwell", 328)

library.add_item(dune)
library.add_item(interstellar)
library.add_item(magazine)
library.add_item(orwell)

print("--- All items ---")
for item in library.items:
    print(item)

print("\nAvailable before checkout:", library.list_available())

print("\n--- Checking out 2 items ---")
print(dune.checkout())
print(interstellar.checkout())

print("\nAvailable after checkout:", library.list_available())