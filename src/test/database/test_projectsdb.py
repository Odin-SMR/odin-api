from datetime import datetime

from mock import patch
import pytest

from odinapi.database.level2db import ProjectsDB, ProjectError, ProjectAnnotation
from odinapi.database.mongo import get_collection, get_database


def get_empty_collection(col):
    col.drop()
    return col


@pytest.fixture
def projectdb(db_context):
    with patch(
        "odinapi.database.level2db.mongo.get_collection",
        side_effect=lambda db, col: get_empty_collection(
            get_database(db).get_collection(col)
        ),
    ):
        yield ProjectsDB()


@pytest.mark.slow
def test_projectdb_empty(projectdb):
    projects = list(projectdb.get_projects())
    assert len(projects) == 0


@pytest.mark.slow
def test_add_project(projectdb):
    projectdb.add_project_if_not_exists("my-project")
    project = projectdb.get_project("my-project")
    assert project["name"] == "my-project"
    assert project["development"]


class TestPublishProject:
    @pytest.mark.slow
    def test_publish_project(self, projectdb):
        projectdb.add_project_if_not_exists("my-project")
        projectdb.publish_project("my-project")
        project = projectdb.get_project("my-project")
        assert not project["development"]

    @pytest.mark.slow
    def test_publish_unknown_project(self, projectdb):
        with pytest.raises(ProjectError):
            projectdb.publish_project("my-project")


class TestGetProjects:
    @pytest.mark.slow
    @pytest.fixture(autouse=True)
    def projects(self, projectdb):
        projectdb.add_project_if_not_exists("my-project-dev")
        projectdb.add_project_if_not_exists("my-project-prod")
        projectdb.publish_project("my-project-prod")

    @pytest.mark.slow
    def test_get_all(self, projectdb):
        projects = list(projectdb.get_projects(development=None))
        assert len(projects) == 2

    @pytest.mark.slow
    def test_get_development(self, projectdb):
        projects = list(projectdb.get_projects(development=True))
        assert len(projects) == 1
        assert projects[0]["name"] == "my-project-dev"

    @pytest.mark.slow
    def test_get_production(self, projectdb):
        projects = list(projectdb.get_projects(development=False))
        assert len(projects) == 1
        assert projects[0]["name"] == "my-project-prod"


class TestAnnotations:
    @pytest.mark.slow
    def test_get_annotations_unknown_project(self, projectdb):
        with pytest.raises(ProjectError):
            list(projectdb.get_annotations("my-project"))

    @pytest.mark.slow
    def test_get_empty_annotations(self, projectdb):
        projectdb.add_project_if_not_exists("my-project")
        assert list(projectdb.get_annotations("my-project")) == []

    @pytest.mark.slow
    def test_add_one_annotation(self, projectdb):
        projectdb.add_project_if_not_exists("my-project")
        annotation = ProjectAnnotation(
            text="This is my project",
            created_at=datetime(2000, 1, 2, 3, 4, 5),
        )
        projectdb.add_annotation("my-project", annotation)
        assert list(projectdb.get_annotations("my-project")) == [annotation]

    @pytest.mark.slow
    def test_add_multiple_annotation(self, projectdb):
        projectdb.add_project_if_not_exists("my-project")
        annotations = [
            ProjectAnnotation(
                text="This is my project.",
                created_at=datetime(2000, 1, 2, 3, 4, 5),
            ),
            ProjectAnnotation(
                text="You cannot have my project.",
                created_at=datetime(2000, 1, 2, 3, 4, 6),
            ),
            ProjectAnnotation(
                text="It's mine.",
                created_at=datetime(2000, 1, 2, 3, 4, 7),
            ),
        ]
        for annotation in annotations:
            projectdb.add_annotation("my-project", annotation)
        assert list(projectdb.get_annotations("my-project")) == annotations

    @pytest.mark.slow
    def test_add_annotation_with_freqmode(self, projectdb):
        projectdb.add_project_if_not_exists("my-project")
        annotation = ProjectAnnotation(
            text="Booooo",
            created_at=datetime(2000, 1, 2, 3, 4, 5),
            freqmode=73,
        )
        projectdb.add_annotation("my-project", annotation)
        assert list(projectdb.get_annotations("my-project")) == [annotation]

    @pytest.mark.slow
    def test_add_annotation_unknown_project(self, projectdb):
        annotation = ProjectAnnotation(
            text="Not my project",
            created_at=datetime(2000, 1, 2, 3, 4, 5),
        )
        with pytest.raises(ProjectError):
            projectdb.add_annotation("my-project", annotation)
