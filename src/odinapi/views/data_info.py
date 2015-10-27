
""" doc
"""
from flask import jsonify
from flask.views import MethodView
from database import DatabaseConnector

class FileInfo(MethodView):
    """plots information"""
    def get(self):
        """GET"""
        db_connection = DatabaseConnector()
        result_dict = {}
        for file_ending in ['ac1', 'ac2', 'shk', 'fba', 'att']:
            query = (
                "select created from level0_files_imported "
                "where file ~ '.*{0}' "
                "order by created desc limit 1"
                ).format(file_ending)
            db_result = db_connection.query(query)
            result_dict[file_ending] = db_result.getresult()[0][0]
        return jsonify(**result_dict)

