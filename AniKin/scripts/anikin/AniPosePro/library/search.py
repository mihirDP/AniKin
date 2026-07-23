"""
search.py — Search & Filter Engine for AniPose Pro V3.1.
"""

import datetime


class LibrarySearchEngine(object):
    """
    Filters item summaries from LibraryIndexCache.
    """

    def __init__(self):
        self.query = ""
        self.recency = "All"      # "All", "Today", "7 Days", "30 Days"
        self.favorites_only = False
        self.types = {"pose", "clip", "script", "mirror", "selection"}
        self.min_rating = 0
        self.selected_color = None

    def filter_items(self, items: list) -> list:
        if not items:
            return []

        results = []
        now = datetime.datetime.now()

        query_lower = self.query.strip().lower()

        for item in items:
            # 1. Type filter
            itype = item.get("type", "pose")
            if itype not in self.types:
                continue

            # 2. Favorite filter
            if self.favorites_only and not item.get("favorite", False):
                continue

            # 3. Rating filter
            if self.min_rating > 0 and item.get("rating", 0) < self.min_rating:
                continue

            # 4. Color filter
            if self.selected_color and item.get("color") != self.selected_color:
                continue

            # 5. Recency filter
            created_str = item.get("created", "")
            if self.recency != "All" and created_str:
                try:
                    c_date = datetime.datetime.strptime(created_str[:10], "%Y-%m-%d")
                    days_diff = (now - c_date).days
                    if self.recency == "Today" and days_diff > 0:
                        continue
                    elif self.recency == "7 Days" and days_diff > 7:
                        continue
                    elif self.recency == "30 Days" and days_diff > 30:
                        continue
                except Exception:
                    pass

            # 6. Text query filter
            if query_lower:
                name_match = query_lower in item.get("name", "").lower()
                tags_match = any(query_lower in t.lower() for t in item.get("tags", []))
                notes_match = query_lower in item.get("notes", "").lower()
                author_match = query_lower in item.get("author", "").lower()

                if not (name_match or tags_match or notes_match or author_match):
                    continue

            results.append(item)

        return results
