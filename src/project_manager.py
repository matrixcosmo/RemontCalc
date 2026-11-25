from models.project import Project

class ProjectManager:
    def __init__(self, config, data_manager):
        self.config = config
        self.data_manager = data_manager
        self.projects = {}

    def load_projects(self, data):
        self.projects = {}
        raw_list = data.get("projects", []) if isinstance(data, dict) else []
        if isinstance(raw_list, dict):
            raw_list = list(raw_list.values())
        for p_data in raw_list:
            proj = Project.from_dict(p_data)
            self.projects[proj.id] = proj

    def add_project(self, project):
        if isinstance(project, dict):
            project = Project.from_dict(project)
        self.projects[project.id] = project
        return project

    def get_project(self, proj_id):
        return self.projects.get(proj_id)

    def delete_project(self, proj_id):
        if proj_id in self.projects:
            del self.projects[proj_id]

    def get_all_projects(self):
        return list(self.projects.values())

    def to_dict(self):
        return {"projects": [p.to_dict() for p in self.projects.values()], "metadata": {"version": "1.1", "total_projects": len(self.projects)}}
