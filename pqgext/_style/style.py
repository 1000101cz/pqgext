from .._settings import pqgext_settings as pes


class PQGExtStyle:
    def __init__(self):
        ...

    @property
    def palette(self):
        if pes.palette is None:
            def_palette = ['blue', 'red', 'green', 'orange', 'purple', 'pink']
            return def_palette
        else:
            return pes.palette

    @property
    def primary_color(self):
        if pes.primary_color is None:
            def_prim_col = (50, 120, 220)
            return def_prim_col
        else:
            return pes.primary_color

    @property
    def secondary_color(self):
        if pes.secondary_color is None:
            def_sec_col = (220, 120, 50)
            return def_sec_col
        return pes.secondary_color

