import os.path
from textwrap import dedent

from flask import abort, jsonify
from flask.views import MethodView
from sqlalchemy import text

from ..pg_database import db
from . import newdonalettyERANC


class FileInfo(MethodView):
    """plots information"""

    def get(self, version):
        """GET"""
        result_dict = {}
        for file_ending in ["ac1", "ac2", "shk", "fba", "att"]:
            query = text(dedent("""\
                select created from level0_files_imported
                where file ~ :f
                order by created desc limit 1"""
            ))
            db_result = db.session.execute(query, params=dict(f=".*" + file_ending))
            first_row = db_result.first()
            if first_row is not None:
                result_dict[file_ending] = first_row[0]
            else:
                result_dict[file_ending] = None
        return jsonify(**result_dict)


class LatestECMF(MethodView):
    """GET the date of the latest available ecmf file"""

    def get(self, version):
        file_name = newdonalettyERANC.get_latest_ecmf_file()
        date = newdonalettyERANC.get_ecmf_file_date(file_name)
        return jsonify(dict(File=os.path.basename(file_name), Date=date))
