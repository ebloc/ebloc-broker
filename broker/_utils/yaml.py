#!/usr/bin/env python3

import os
from pathlib import Path

import ruamel.yaml


class SubYaml(dict):
    """SubYaml object."""

    def __init__(self, parent):
        self.parent = parent

    def updated(self):
        self.parent.updated()

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            v = SubYaml(self)
            v.update(value)
            value = v
        super().__setitem__(key, value)
        self.updated()

    def __getitem__(self, key):
        try:
            super().__getitem__(key)
        except KeyError:
            super().__setitem__(key, SubYaml(self))
            self.updated()
        return super().__getitem__(key)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.updated()

    def update(self, *args, **kw):
        for arg in args:
            for k, v in arg.items():
                self[k] = v
        for k, v in kw.items():
            self[k] = v
        self.updated()
        return
        for arg in args:
            super().update(arg)
        super().update(**kw)
        self.updated()


_SR = ruamel.yaml.representer.SafeRepresenter
_SR.add_representer(SubYaml, _SR.represent_dict)


class Yaml(dict):
    """Yaml object.

    __ https://codereview.stackexchange.com/a/210162/127969
    __ https://stackoverflow.com/a/68685839/2402577
    __ https://stackoverflow.com/a/68694688/2402577
    """

    def __init__(self, filename, auto_dump=True):
        self.filename = filename if hasattr(filename, "open") else Path(filename)
        self.filename_temp = f"{self.filename}~"
        self.auto_dump = auto_dump
        self.changed = False
        self.yaml = ruamel.yaml.YAML(typ="safe")
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
        """Dump yaml object."""
        if not self.changed and not force:
            return

        with open(self.filename_temp, "w") as f:
            # write to a temporary file
            self.yaml.dump(dict(self), f)

        # unlink the real filename and rename the temporary to the real
        os.rename(self.filename_temp, self.filename)
        self.changed = False

    def __setitem__(self, key, value):
        """Update given key's value."""
        if isinstance(value, dict):
            v = SubYaml(self)
            v.update(value)
            value = v
        super().__setitem__(key, value)
        self.updated()

    def __getitem__(self, key):
        try:
            super().__getitem__(key)
        except KeyError:
            super().__setitem__(key, SubYaml(self))
            self.updated()
        return super().__getitem__(key)

    def __delitem__(self, key):
        super().__delitem__(key)
        self.updated()

    def update(self, *args, **kw):
        for arg in args:
            for k, v in arg.items():
                self[k] = v
        for k, v in kw.items():
            self[k] = v
        self.updated()


if __name__ == "__main__":
    config_file = Path("test.yaml")
    cfg = Yaml(config_file)
    cfg["setup"]["a"] = 199
    #
    config_file = Path("test_1.yaml")
    cfg = Yaml(config_file)
    cfg["a"] = 1
    cfg["b"]["x"] = 2
    cfg["c"]["y"]["z"] = 42

    print(f"{config_file} 1:")
    print(config_file.read_text())

    cfg["b"]["x"] = 3
    cfg["a"] = 4

    print(f"{config_file} 2:")
    print(config_file.read_text())

    cfg.update(a=9, d=196)
    cfg["c"]["y"].update(k=11, l=12)

    print(f"{config_file} 3:")
    print(config_file.read_text())

    # reread config from file
    cfg = Yaml(config_file)
    assert isinstance(cfg["c"]["y"], SubYaml)
    assert cfg["c"]["y"]["z"] == 42
    del cfg["c"]
    print(f"{config_file} 4:")
    print(config_file.read_text())

    # start from scratch immediately use updating
    config_file.unlink()
    cfg = Yaml(config_file)
    cfg.update(a=dict(b=4))
    cfg.update(c=dict(b=dict(e=5)))
    assert isinstance(cfg["a"], SubYaml)
    assert isinstance(cfg["c"]["b"], SubYaml)
    cfg["c"]["b"]["f"] = 222

    print(f"{config_file} 5:")
    print(config_file.read_text())

    # cfg = Yaml("test.yaml")
    # print(cfg)
    # # cfg["z"] = 110
    # cfg["setup"]["a"] = 110
    # cfg.updated()
    # print(cfg)
    # # cfg.update({"b": 4})
    # # cfg.update(c=5)
    # # del cfg['a']
    # # print(cfg)
    # print("------")
    # print(open(cfg.filename).read())
