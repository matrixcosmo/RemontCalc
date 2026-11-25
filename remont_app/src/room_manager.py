class RoomManager:
    def __init__(self, config, project_manager):
        self.config = config
        self.project_manager = project_manager

    @property
    def rooms(self):
        res = []
        for p in self.project_manager.get_all_projects():
            res.extend(p.rooms)
        return res
