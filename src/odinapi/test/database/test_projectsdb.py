# pylint: disable=no-self-use,redefined-outer-name
from mock import patch
import pytest

from odinapi.database.level2db import ProjectsDB, ProjectError


@pytest.fixture
def projectdb(mongodb):
    with patch(
        'odinapi.database.level2db.mongo.get_collection',
        return_value=mongodb['testdb']['testcollection']
    ):
        yield ProjectsDB()


def test_projectdb_empty(projectdb):
    projects = list(projectdb.get_projects())
    assert len(projects) == 0


def test_add_project(projectdb):
    projectdb.add_project_if_not_exists('my-project')
    project = projectdb.get_project('my-project')
    assert project['name'] == 'my-project'
    assert project['development']


class TestPublishProject(object):
    def test_publish_project(self, projectdb):
        projectdb.add_project_if_not_exists('my-project')
        projectdb.publish_project('my-project')
        project = projectdb.get_project('my-project')
        assert not project['development']

    def test_publish_unknown_project(self, projectdb):
        with pytest.raises(ProjectError):
            projectdb.publish_project('my-project')


class TestGetProjects(object):

    @pytest.fixture(autouse=True)
    def projects(self, projectdb):
        projectdb.add_project_if_not_exists('my-project-dev')
        projectdb.add_project_if_not_exists('my-project-prod')
        projectdb.publish_project('my-project-prod')

    def test_get_all(self, projectdb):
        projects = list(projectdb.get_projects(development=None))
        assert len(projects) == 2

    def test_get_development(self, projectdb):
        projects = list(projectdb.get_projects(development=True))
        assert len(projects) == 1
        assert projects[0]['name'] == 'my-project-dev'

    def test_get_production(self, projectdb):
        projects = list(projectdb.get_projects(development=False))
        assert len(projects) == 1
        assert projects[0]['name'] == 'my-project-prod'
