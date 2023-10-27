import os.path
from odinapi.pg_database import squeeze_query

from flask import abort, jsonify
from flask.views import MethodView
from sqlalchemy import text

from ..pg_database import db


class FileInfo(MethodView):
    """plots information"""

    def get(self, version):
        """GET"""
        result_dict = {}
        for file_ending in ["ac1", "ac2", "shk", "fba", "att"]:
            query = text(
                squeeze_query(
                    """\
                select created from level0_files_imported
                where file ~ :f
                order by created desc limit 1"""
                )
            )
            db_result = db.session.execute(query, params=dict(f=".*" + file_ending))
            first_row = db_result.first()
            if first_row is not None:
                result_dict[file_ending] = first_row[0]
            else:
                result_dict[file_ending] = None
        return jsonify(**result_dict)
