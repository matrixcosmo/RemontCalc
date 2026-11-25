from config.prices import PRICES, REGION_COEFFICIENTS

class CostCalculator:
    def __init__(self, config, room_manager=None):
        self.config = config
        self.room_manager = room_manager

    def calculate_room(self, room, region="г. Брянск"):
        price = PRICES.get(room.repair_class, 3450.0)
        coeff = REGION_COEFFICIENTS.get(region, 1.0)
        return room.calculate_cost(price, coeff)

    def calculate_project(self, project):
        for room in project.rooms:
            self.calculate_room(room, project.region)
        project.recalculate()
        return project.total_cost
