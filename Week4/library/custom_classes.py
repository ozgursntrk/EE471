"""Library media classes: generic items, books, DVDs and a collection."""


class MediaItem:
    """A generic item that can be checked out from a library."""

    def __init__(self, title, author, is_available=True):
        """Create an item with its title and author; is_available defaults to True."""
        self.title = title
        self.author = author
        self.is_available = is_available

    def checkout(self):
        """Check the item out if available. Return 'Successful checkout' on success, otherwise 'Already out'."""
        if self.is_available:
            self.is_available = False
            return "Successful checkout"
        return "Already out"

    def return_item(self):
        """Mark the item as available."""
        self.is_available = True

    def __str__(self):
        """Return the item as 'Title by Author [Status]'."""
        status = "Available" if self.is_available else "Checked Out"
        return f"{self.title} by {self.author} [{status}]"


class Book(MediaItem):
    """A media item that also stores its page count."""

    def __init__(self, title, author, page_count, is_available=True):
        """Create a book with its page count."""
        super().__init__(title, author, is_available)
        self.page_count = page_count

    def __str__(self):
        """Return the base description followed by the page count."""
        return f"{super().__str__()} - {self.page_count} pages"


class DVD(MediaItem):
    """A media item that stores its duration and needs careful handling."""

    def __init__(self, title, author, duration_minutes, is_available=True):
        """Create a DVD with its duration in minutes."""
        super().__init__(title, author, is_available)
        self.duration_minutes = duration_minutes

    def checkout(self):
        """Check out the DVD and remind the borrower to handle it carefully."""
        # Reuse the parent logic so any future change to MediaItem applies here too
        result = super().checkout()
        # The reminder only makes sense when the disc actually leaves the library
        if result == "Successful checkout":
            print("Handle with care: Do not scratch the disc.")
        return result


class LibraryCollection:
    """A container that holds the library's media items."""

    def __init__(self):
        """Start with an empty collection."""
        self.items = []

    def add_item(self, item):
        """Add a MediaItem or any of its subclasses to the collection."""
        self.items.append(item)

    def list_available(self):
        """Return the titles of the items that are currently available."""
        return [item.title for item in self.items if item.is_available]