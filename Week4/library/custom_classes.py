"""Library media classes: generic items, books, DVDs and a collection."""


# ---------- Madde 1: Özel hata sınıfları ----------
class ItemNotFoundError(Exception):
    """Raised when no item exists with the given id."""


class ItemStateError(Exception):
    """Raised when an item is in the wrong state for an action."""


class MediaItem:
    """A generic item that can be checked out from a library."""

    item_type = "item"  # Book ve DVD bunu kendi türleriyle değiştirir

    def __init__(self, title, author, is_available=True):
        """Create an item with its title and author; is_available defaults to True."""
        self.id = None  # Madde 2: id'yi LibraryCollection.add_item() verir
        self.title = title
        self.author = author
        self.is_available = is_available

    # ---------- Madde 4: yazı yerine hata fırlat ----------
    def checkout(self):
        """Check the item out. Raise ItemStateError if it is already out."""
        if not self.is_available:
            raise ItemStateError(f"'{self.title}' is already checked out")
        self.is_available = False
        return "Successful checkout"

    def return_item(self):
        """Return the item. Raise ItemStateError if it is not checked out."""
        if self.is_available:
            raise ItemStateError(f"'{self.title}' is not checked out")
        self.is_available = True
        return "Successful return"

    # ---------- Madde 3: sözlüğe çevir ----------
    def to_dict(self):
        """Return the item's data as a dictionary (ready for JSON)."""
        return {
            "id": self.id,
            "type": self.item_type,
            "title": self.title,
            "author": self.author,
            "is_available": self.is_available,
        }

    def __str__(self):
        """Return the item as 'Title by Author [Status]'."""
        status = "Available" if self.is_available else "Checked Out"
        return f"{self.title} by {self.author} [{status}]"


class Book(MediaItem):
    """A media item that also stores its page count."""

    item_type = "book"

    def __init__(self, title, author, page_count, is_available=True):
        """Create a book with its page count."""
        super().__init__(title, author, is_available)
        self.page_count = page_count

    def to_dict(self):
        """Add page_count to the parent's dictionary."""
        data = super().to_dict()
        data["page_count"] = self.page_count
        return data

    def __str__(self):
        """Return the base description followed by the page count."""
        return f"{super().__str__()} - {self.page_count} pages"


class DVD(MediaItem):
    """A media item that stores its duration and needs careful handling."""

    item_type = "dvd"

    def __init__(self, title, author, duration_minutes, is_available=True):
        """Create a DVD with its duration in minutes."""
        super().__init__(title, author, is_available)
        self.duration_minutes = duration_minutes

    # ---------- Madde 5: print yok, mesajın içinde döndür ----------
    def checkout(self):
        """Check out the DVD and include the care reminder in the message."""
        result = super().checkout()  # zaten dışarıdaysa burada hata fırlar
        return f"{result}. Handle with care: Do not scratch the disc."

    def to_dict(self):
        """Add duration (in minutes) to the parent's dictionary."""
        data = super().to_dict()
        data["duration"] = self.duration_minutes
        return data


class LibraryCollection:
    """A container that holds the library's media items."""

    EDITABLE_FIELDS = {"title", "author", "page_count", "duration"}
    PROTECTED_FIELDS = {"id", "type", "is_available"}
    VALID_TYPES = {"book", "dvd"}

    def __init__(self):
        """Start with an empty collection."""
        self.items = []
        self._next_id = 1  # Madde 2: silinse bile geri sayılmayan sayaç

    def add_item(self, item):
        """Give the item a new unique id, add it, and return the id."""
        item.id = self._next_id
        self._next_id += 1
        self.items.append(item)
        return item.id

    def list_available(self):
        """Return the titles of the items that are currently available."""
        return [item.title for item in self.items if item.is_available]

    # ---------- Madde 6: yeni metotlar ----------
    def get_item(self, item_id):
        """Return the item with this id, or raise ItemNotFoundError."""
        for item in self.items:
            if item.id == item_id:
                return item
        raise ItemNotFoundError(f"Item {item_id} not found")

    def list_items(self, available=None, item_type=None):
        """Return all items, optionally filtered by availability and/or type."""
        if item_type is not None and item_type not in self.VALID_TYPES:
            raise ValueError(f"Unknown type '{item_type}'. Use 'book' or 'dvd'.")
        result = self.items
        if available is not None:
            result = [item for item in result if item.is_available == available]
        if item_type is not None:
            result = [item for item in result if item.item_type == item_type]
        return list(result)

    def update_item(self, item_id, **fields):
        """Update only editable fields. Raise ValueError for forbidden or invalid fields."""
        item = self.get_item(item_id)

        # 1) Önce hepsini kontrol et (biri hatalıysa hiçbirini değiştirme)
        for name, value in fields.items():
            if name in self.PROTECTED_FIELDS:
                raise ValueError(f"Field '{name}' cannot be changed")
            if name not in self.EDITABLE_FIELDS:
                raise ValueError(f"Unknown field '{name}'")
            if name == "page_count" and not isinstance(item, Book):
                raise ValueError("Only books have a page_count")
            if name == "duration" and not isinstance(item, DVD):
                raise ValueError("Only DVDs have a duration")
            if name in ("title", "author"):
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"'{name}' must be non-empty text")
            if name in ("page_count", "duration"):
                if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                    raise ValueError(f"'{name}' must be a positive whole number")

        # 2) Hepsi geçerliyse uygula
        for name, value in fields.items():
            if name == "duration":
                item.duration_minutes = value
            else:
                setattr(item, name, value)
        return item

    def remove_item(self, item_id):
        """Remove the item. Raise ItemStateError if it is checked out."""
        item = self.get_item(item_id)  # yoksa ItemNotFoundError fırlar
        if not item.is_available:
            raise ItemStateError("Cannot delete a checked-out item")
        self.items.remove(item)