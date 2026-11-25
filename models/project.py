from datetime import datetime
import uuid
from models.room import Room

class Project:
    def __init__(self, name, region="г. Брянск", id=None):
        self.id = id or f"proj_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.region = region
        self.rooms = []
        self.total_cost = 0.0
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.metadata = {"room_count": 0}

    def add_room(self, room):
        if isinstance(room, dict):
            room = Room.from_dict(room)
        self.rooms.append(room)
        self.recalculate()

    def remove_room(self, room_id):
        self.rooms = [r for r in self.rooms if r.id != room_id]
        self.recalculate()

    def recalculate(self):
        self.total_cost = round(sum(r.cost for r in self.rooms), 2)
        self.metadata["room_count"] = len(self.rooms)

    def to_dict(self):
        self.recalculate()
        return {
            "id": self.id, "name": self.name, "region": self.region,
            "rooms": [r.to_dict() for r in self.rooms],
            "total_cost": self.total_cost, "created_date": self.created_date,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data):
        p = cls(name=data.get("name", "Объект"), region=data.get("region", "г. Брянск"), id=data.get("id"))
        p.created_date = data.get("created_date", p.created_date)
        for r_data in data.get("rooms", []):
            p.rooms.append(Room.from_dict(r_data))
        p.recalculate()
        return p
