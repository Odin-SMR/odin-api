from flask import Blueprint

from odinapi.views.statistics import FreqmodeStatistics, TimelineFreqmodeStatistics

stats = Blueprint("stats", __name__)
stats.add_url_rule(
    "/rest_api/<version>/statistics/freqmode/",
    view_func=FreqmodeStatistics.as_view("freqmodestatistics"),
)
stats.add_url_rule(
    "/rest_api/<version>/statistics/freqmode/timeline/",
    view_func=TimelineFreqmodeStatistics.as_view("timefmstatistics"),
)
@stats.route("/rest_api/health_check")
def health_check():
    return "Odin API OK!"
