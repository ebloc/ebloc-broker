#!/usr/bin/env python3

import os
from contextlib import suppress
from pathlib import Path

from filelock import FileLock
from ruamel.yaml import YAML, comments, representer

from broker._utils.tools import print_tb

_SR = representer.RoundTripRepresenter


class SubYaml(comments.CommentedMap):
    """SubYaml object."""

    def __init__(self, parent):
        self.parent = parent
        super().__init__(self)

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
            return super().__getitem__(key)
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

            for attr in [comments.Comment.attrib, comments.Format.attrib]:
                if hasattr(arg, attr):
                    setattr(self, attr, getattr(arg, attr))

        for k, v in kw.items():
            self[k] = v

        self.updated()


_SR.add_representer(SubYaml, _SR.represent_dict)


class Yaml(comments.CommentedMap):
    """Create yaml object.

    How to auto-dump modified values in nested dictionaries using ruamel.yaml?
    __ https://stackoverflow.com/a/68694688/2402577

    representer.RepresenterError: cannot represent an object: {'value': }
    __ https://stackoverflow.com/a/68685839/2402577

    PyYAML Saving data to .yaml files
    __ https://codereview.stackexchange.com/a/210162/127969

    Yaml format
    __ https://stackoverflow.com/a/70034493/2402577

    Keep comments of a yaml file when modify its values in nested dictionaries
    __ https://stackoverflow.com/a/71000545/2402577
    """

    def __init__(self, path, auto_dump=True):
        super().__init__(self)
        path = os.path.expanduser(path)  # dirname of the absolute path
        self.dirname = os.path.dirname(os.path.abspath(path))
        self.filename = os.path.basename(path)
        if self.filename[0] == ".":
            fp_lockname = f"{self.filename}.lock"
        else:
            fp_lockname = f".{self.filename}.lock"

        self.fp_lock = os.path.join(self.dirname, fp_lockname)
        self.path = path if hasattr(path, "open") else Path(path)
        self.auto_dump = auto_dump
        self.changed = False
        self.yaml = YAML()
        self.yaml.indent(mapping=4, sequence=4, offset=2)
        if self.path.exists():
            with FileLock(self.fp_lock, timeout=1):
                with open(path) as f:
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

        with open(self.path, "w") as f:
            self.yaml.dump(dict(self), f)

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

            for attr in [comments.Comment.attrib, comments.Format.attrib]:
                if hasattr(arg, attr):
                    setattr(self, attr, getattr(arg, attr))

        for k, v in kw.items():
            self[k] = v

        self.updated()


_SR.add_representer(Yaml, _SR.represent_dict)

cfg = Yaml(Path("config.yaml"))


def test_1():
    config_file = Path("test.yaml")
    cfg = Yaml(config_file)
    cfg["setup"]["a"] = 200
    cfg["setup2"]["c"] = 1
    with suppress(Exception):
        del cfg["setup1"]

    cfg["setup1"]["b"] = 999
    cfg_again = Yaml(config_file)
    assert cfg_again["setup"]["a"] == 200, "setup_a is not 200"
    assert cfg_again["setup1"]["b"] == 999, "setup1_b is not 999"


def test_2():
    config_file = Path("test.yaml")
    cfg = Yaml(config_file)
    cfg["setup"]["a"] = 201
    cfg_again = Yaml(config_file)
    assert cfg_again["setup"]["a"] == 201, "setup_a is not changed"


def test_3():
    config_file = Path("test_1.yaml")
    cfg = Yaml(config_file)
    cfg["a"] = 1
    cfg["b"]["x"] = 2
    cfg["c"]["y"]["z"] = 45
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
    assert cfg["c"]["y"]["z"] == 45
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
    cfg["c"]["b"]["f"] = 333
    print(f"{config_file} 5:")
    print(config_file.read_text())
    cfg_again = Yaml(config_file)
    assert cfg_again["c"]["b"]["f"] == 333, "cfg['c']['b']['f'] is not 333"


def test_4():
    fn = Path("config.yaml")
    fn.write_text(
        """
    c:  # my comment
      b:
         f: 5
      x: {g: 6}
    a:
      z: 4
      b: 4  # my comment
    """
    )
    Yaml(fn)
    print(Path(fn).read_text())


def main():
    try:
        test_1()
        test_2()
        test_3()
        test_4()
    except Exception as e:
        print_tb(e)


if __name__ == "__main__":
    main()
