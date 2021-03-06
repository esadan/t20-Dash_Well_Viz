from plotly.subplots import make_subplots
import plotly.graph_objs as go


class WellLog:
    """Well log wrapper.

    Args:
        n_tracks (int): number of vertical tracks.
        shared_yaxes (bool): shared Y axes for all tracks?

    Other keyword arguments will be passed to plotly.make_subplots()

    Attributes:
        fig (plotly go.Figure object)

    """

    def __init__(self, n_tracks, shared_yaxes=True, **kwargs):
        self.fig = make_subplots(
            rows=1,
            cols=n_tracks,
            subplot_titles=[f"{t + 1}:" for t in range(n_tracks)],
            shared_yaxes=shared_yaxes,
            **kwargs,
        )

    def get_trace(self, name):
        """Get a dictionary containing the plotly graph object for the trace.

        Args:
            name (str): current name of the plotly graph object.

        Returns: dict containing key *'go'* containing the current plotly graph
            object, and other keys: *'track_no'* (int): zero-indexed track/column
            containing the trace.

        """
        trace = None
        for tr in self.fig.data:
            if tr.name == name:
                trace = {"go": tr}
        if trace is None:
            raise KeyError(
                f"Could not find trace.name = '{name}' in {[t['name'] for t in self.fig.data]}"
            )
        else:
            if trace["go"].yaxis == "y":
                trace["track_no"] = 0
            else:
                trace["track_no"] = int(trace["go"].yaxis.replace("y", "")) - 1

            return trace

    def add_trace(self, graph_obj, name=None, track_no=0, **kwargs):
        """Add a trace to the plotly figure.

        Args:
            graph_obj (plotly graph object)
            name (str)
            track_no (int): zero-indexed track/column number

        Other keyword arguments (e.g. "secondary_x") are passed through
        to plotly.go.Figure.add_trace.

        """
        if name is None:
            name = graph_obj.name
        self.fig.add_trace(graph_obj, row=1, col=track_no + 1, **kwargs)


def make_scatter(series, **kwargs):
    return go.Scatter(x=series.values, y=series.index, **kwargs)


def make_composite_log(
    df,
    lines=(),
    log_tracks=(),
    lines_func=make_scatter,
    line_kwargs=None,
):
    """Make a composite well log from a pandas.DataFrame.

    Args:
        df (pandas.DataFrame): the index should be the depth.
        lines (list of lists): list of column names to plot as lines on
            the composite log. Each item should be a list of column names;
            each list refers to each track. So for example, for a composite
            log showing gamma in the first track and neutron and density in
            the second track, you would use: ``lines=[["GAMM"], ["NEUT", "RHO"]]``.
        log_tracks (list): list of tracks to set as log scale (zero-indexed,
            i.e. ``log_tracks=[0]`` would apply to left-most track; also
            allows negative indices so that ``log_tracks=[-1]`` would apply
            to the right-most track).
        lines_func (function): function which takes a pandas.Series and
            returns a plotly graph object e.g. ``go.Scatter``
        line_kwargs (dict): dictionary which is passed also for each
            call to lines_func. Default is `{"mode": "lines", "line": {"width": 1}}`

    Returns: ``WellLog`` object with a plotly ``Figure`` as the ``fig``
        attribute.

    """
    if line_kwargs is None:
        line_kwargs = {"mode": "lines", "line": {"width": 1}}
    n_tracks = max([len(lines)])

    columns = []
    log = WellLog(n_tracks=n_tracks)
    for i, column_names in enumerate(lines):
        for column in column_names:
            log.add_trace(
                lines_func(df[column], name=column, **line_kwargs), track_no=i
            )
            columns.append(column)

    data_range = df[columns].dropna(how="any")
    log.fig.update_yaxes(range=(max(data_range.index), min(data_range.index)))

    for track_no in log_tracks:
        if track_no < 0:
            track_no = n_tracks + track_no
        if track_no == 0:
            log.fig.update_layout(xaxis_type="log")
        else:
            log.fig.update_layout(**{f"xaxis{track_no + 1:.0f}_type": "log"})

    log.fig.update_layout(template='plotly_white')

    return log
