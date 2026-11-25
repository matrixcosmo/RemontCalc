from datetime import datetime
import uuid

class Room:
    def __init__(self, name, floor_area, wall_area, repair_class="Комфорт", id=None, cost=0.0):
        self.id = id or f"room_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.floor_area = float(floor_area)
        self.wall_area = float(wall_area)
        self.repair_class = repair_class
        self.total_area = round(self.floor_area + self.wall_area * 0.5, 2)
        self.cost = float(cost)
        self.created_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def calculate_cost(self, price_per_m2, region_coeff=1.0):
        self.total_area = round(self.floor_area + self.wall_area * 0.5, 2)
        self.cost = round(self.total_area * float(price_per_m2) * float(region_coeff), 2)
        return self.cost

    def to_dict(self):
        return {
            "id": self.id, "name": self.name,
            "floor_area": self.floor_area, "wall_area": self.wall_area,
            "repair_class": self.repair_class, "total_area": self.total_area,
            "cost": self.cost, "created_date": self.created_date
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", "Помещение"),
            floor_area=data.get("floor_area", 0),
            wall_area=data.get("wall_area", 0),
            repair_class=data.get("repair_class", "Комфорт"),
            id=data.get("id"), cost=data.get("cost", 0)
        )
