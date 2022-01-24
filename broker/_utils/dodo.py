#!/usr/bin/env python3

from pathlib import Path
from ruamel.yaml import YAML, comments, representer


class SubConfig(comments.CommentedMap):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(self)

    def updated(self):
        self.parent.updated()

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            v = SubConfig(self)
            v.update(value)
            value = v
        super().__setitem__(key, value)
        self.updated()

    def __getitem__(self, key):
        try:
            res = super().__getitem__(key)
        except KeyError:
            super().__setitem__(key, SubConfig(self))
            self.updated()
            return super().__getitem__(key)
        return res

    def __delitem__(self, key):
        res = super().__delitem__(key)
        self.updated()

    def update(self, *args, **kw):
        for arg in args:
            for k, v in arg.items():
                self[k] = v
        for k, v in kw.items():
            self[k] = v
        self.updated()
        return


_SR = representer.RoundTripRepresenter
_SR.add_representer(SubConfig, _SR.represent_dict)


class Config(comments.CommentedMap):
    def __init__(self, filename, auto_dump=True):
        super().__init__(self)
        self.filename = filename if hasattr(filename, "open") else Path(filename)
        self.auto_dump = auto_dump
        self.changed = False
        self.yaml = YAML()
        self.yaml.indent(mapping=4, sequence=4, offset=2)
        self.yaml.default_flow_style = False
        if self.filename.exists():
            with open(filename) as f:
                self.update(self.yaml.load(f) or {})

    def updated(self):
        if self.auto_dump:
            self.dump(force=True)
        else:
            self.changed = True

    def dump(self, force=False):
        if not self.changed and not force:
            return
        with open(self.filename, "w") as f:
            self.yaml.dump(self, f)
        self.changed = False

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            v = SubConfig(self)
            v.update(value)
            value = v
        super().__setitem__(key, value)
        self.updated()

    def __getitem__(self, key):
        try:
            res = super().__getitem__(key)
        except KeyError:
            super().__setitem__(key, SubConfig(self))
            self.updated()
        return super().__getitem__(key)

    def __delitem__(self, key):
        res = super().__delitem__(key)
        self.updated()

    def update(self, *args, **kw):
        for arg in args:
            for k, v in arg.items():
                self[k] = v
        for k, v in kw.items():
            self[k] = v
        self.updated()


cfg = Config(Path("config.yaml"))
