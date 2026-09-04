import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

class CatalogueService:
    def __init__(self):
        self.shows = [
            {"id": 1, "title": "Orbit School", "synopsis": "Curious lessons from beyond the atmosphere.", "section": "Kids", "category": "Education", "status": "published", "languages": ["English", "Hindi"], "seasons": [{"number": 1, "title": "First Light", "episodes": [{"number": 1, "title": "The Solar System", "description": "A tour of our cosmic neighborhood.", "duration": 24, "content_group": "orbit-1", "languages": ["English", "Hindi"], "video_provider": "youtube", "video_id": "6jiMIXOGtGg"}]}]},
            {"id": 2, "title": "Field Notes", "synopsis": "Small stories from the living world.", "section": "Documentary", "category": "Nature", "status": "draft", "languages": ["English"], "seasons": [{"number": 1, "title": "Behind the Lens", "episodes": [{"number": 1, "title": "Tiny Worlds", "description": "A short documentary clip.", "duration": 6, "content_group": "field-1", "languages": ["English"], "video_provider": "youtube", "video_id": "5DPNuX82wvE"}]}]},
        ]
        self.publish_runs = []
        self.root = Path(os.getenv("STORAGE_PATH", "./data/storage")); self.root.mkdir(parents=True, exist_ok=True)
        self.manifest = self.root / "current.json"

    def create_show(self, data):
        show = {"id": max([s["id"] for s in self.shows], default=0) + 1, **data, "languages": [], "seasons": []}
        self.shows.append(show); return show

    def validation_report(self):
        issues = []
        for show in self.shows:
            if show["status"] == "published" and not show.get("section"):
                issues.append({"type": "missing_section", "label": "Missing section", "show": show["title"], "issue": "Add a section before publishing."})
            for season in show.get("seasons", []):
                for episode in season.get("episodes", []):
                    for field in ("duration", "content_group"):
                        if not episode.get(field):
                            issues.append({"type": f"missing_{field}", "label": f"Missing {field}", "show": show["title"], "season": season["number"], "episode": episode["title"], "issue": f"Episode must have a {field}."})
        return {"can_publish": not issues, "summary": {"errors": len(issues), "warnings": 0}, "groups": [{"type": "validation", "label": "Items to fix", "items": issues}] if issues else []}

    def build(self):
        output = []
        for show in sorted((s for s in self.shows if s["status"] == "published"), key=lambda s: (s["section"], s["title"], s["id"])):
            seasons = []
            trailers = []
            for season in sorted(show.get("seasons", []), key=lambda s: s["number"]):
                target = trailers if season["number"] == 0 else seasons
                episodes = [{k: e[k] for k in ("number", "title", "description", "duration", "content_group", "languages", "video_provider", "video_id")} for e in sorted(season.get("episodes", []), key=lambda e: (e["number"], e["content_group"]))]
                target.append({"number": season["number"], "title": season.get("title", ""), "episodes": episodes})
            output.append({"id": show["id"], "title": show["title"], "synopsis": show["synopsis"], "section": show["section"], "category": show["category"], "languages": show["languages"], "seasons": seasons, "trailers": trailers})
        return {"version": 1, "published_at": None, "shows": output}

    def publish(self, triggered_by):
        report = self.validation_report()
        if not report["can_publish"]:
            raise ValueError("Catalogue has blocking validation errors")
        run_id = len(self.publish_runs) + 1
        catalogue = self.build(); catalogue["published_at"] = datetime.now(timezone.utc).isoformat()
        key = f"catalogue-{run_id}.json"; path = self.root / key
        fd, temp = tempfile.mkstemp(dir=self.root, prefix="catalogue-tmp-", text=True)
        with os.fdopen(fd, "w") as handle: json.dump(catalogue, handle, indent=2, sort_keys=True); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, path)
        fd, temp = tempfile.mkstemp(dir=self.root, prefix="manifest-tmp-", text=True)
        with os.fdopen(fd, "w") as handle: json.dump({"catalogue_key": key}, handle); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp, self.manifest)
        result = {"run": run_id, "status": "success", "triggered_by": triggered_by, "shows": len(catalogue["shows"]), "catalogue_entries": sum(len(s["seasons"]) + len(s["trailers"]) for s in catalogue["shows"]), "catalogue_key": key, "published_at": catalogue["published_at"]}
        self.publish_runs.insert(0, result); return result

    def read_catalogue(self):
        if not self.manifest.exists(): return {"version": 1, "published_at": None, "shows": []}
        key = json.loads(self.manifest.read_text())["catalogue_key"]
        return json.loads((self.root / key).read_text())

    def search(self, q, category, language, section):
        q = q.lower(); catalogue = self.read_catalogue()
        return {**catalogue, "shows": [s for s in catalogue["shows"] if (not q or q in s["title"].lower() or q in s["category"].lower() or any(q in e["title"].lower() for se in s["seasons"] for e in se["episodes"])) and (not category or s["category"].lower() == category.lower()) and (not section or s["section"].lower() == section.lower()) and (not language or language in s["languages"])]}
