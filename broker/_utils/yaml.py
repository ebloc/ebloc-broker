#!/usr/bin/env python3

import os
import shutil
from atomicwrites import atomic_write
from contextlib import suppress
from filelock import FileLock
from pathlib import Path
from ruamel.yaml import YAML, comments, representer

from broker._utils.tools import _remove, print_tb

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

    * How to auto_dump modified values in nested dictionaries using ruamel.yaml?
    __ https://stackoverflow.com/a/68694688/2402577

    * representer.RepresenterError: cannot represent an object: {'value': }
    __ https://stackoverflow.com/a/68685839/2402577

    * PyYAML Saving data to .yaml files
    __ https://codereview.stackexchange.com/a/210162/127969

    * Yaml format
    __ https://stackoverflow.com/a/70034493/2402577

    * Keep comments of a yaml file when modify its values in nested dictionaries
    __ https://stackoverflow.com/a/71000545/2402577
    """

    def __init__(self, path, auto_dump=True):
        """Initialize Yaml object.

        :param path: file path of the yaml file
        :param auto_dump: if false read-only on the background operations
        """
        super().__init__(self)
        self.auto_dump = auto_dump
        path = os.path.expanduser(path)  # dirname of the absolute path
        self.dirname = os.path.dirname(os.path.abspath(path))
        self.fn = os.path.basename(path)
        if self.fn[0] == ".":
            fp_lockname = f"{self.fn}.lock"
        else:
            fp_lockname = f".{self.fn}.lock"

        self.fp_lock = os.path.join(self.dirname, fp_lockname)
        self.path = path if hasattr(path, "open") else Path(path)
        self.path_temp = Path(f"{path}~")
        self.changed = False
        self.yaml = YAML()
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        with FileLock(self.fp_lock, timeout=2):
            _remove(self.path_temp)
            if self.auto_dump:
                if self.path.exists():
                    shutil.copyfile(self.path, self.path_temp)
                else:
                    self.path_temp.touch()

            if self.path.exists():
                if self.auto_dump:
                    _path = self.path_temp
                else:
                    _path = self.path

                with open(_path, "r") as f:
                    self.update(self.yaml.load(f) or {})

            if self.auto_dump:
                shutil.move(self.path_temp, self.path)

    def updated(self):
        if self.auto_dump:
            self.dump(force=True)
        else:
            self.changed = True

    def dump(self, force=False):
        """Dump yaml object."""
        if not self.changed and not force:
            return

        if self.path_temp.exists():
            path = self.path_temp
        else:
            path = self.path

        #: alternative: `with open(path, "w") as f:`
        with atomic_write(path, overwrite=True) as f:
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
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


def print_file(fn):
    print(str(Path(fn).read_text()).rstrip())


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
    print(f"{config_file} 1:-=-=-=-=-=-=-=-=-=-")
    print_file(config_file)
    cfg["b"]["x"] = 3
    cfg["a"] = 4
    print(f"{config_file} 2:-=-=-=-=-=-=-=-=-=-")
    print_file(config_file)

    cfg.update(a=9, d=196)
    cfg["c"]["y"].update(k=11, l=12)
    print(f"{config_file} 3:-=-=-=-=-=-=-=-=-=-")
    print_file(config_file)

    # reread config from file
    cfg = Yaml(config_file)
    assert isinstance(cfg["c"]["y"], SubYaml)
    assert cfg["c"]["y"]["z"] == 45
    del cfg["c"]
    print(f"{config_file} 4:-=-=-=-=-=-=-=-=-=-")
    print_file(config_file)

    # start from scratch immediately use updating
    config_file.unlink()
    cfg = Yaml(config_file)
    cfg.update(a=dict(b=4))
    cfg.update(c=dict(b=dict(e=5)))
    assert isinstance(cfg["a"], SubYaml)
    assert isinstance(cfg["c"]["b"], SubYaml)
    cfg["c"]["b"]["f"] = 333
    print(f"{config_file} 5:-=-=-=-=-=-=-=-=-=-")
    print_file(config_file)
    cfg_again = Yaml(config_file)
    assert cfg_again["c"]["b"]["f"] == 333, "cfg['c']['b']['f'] is not 333"


def test_4():
    fn = Path("config.yaml")
    print(f"{fn} 6:-=-=-=-=-=-=-=-=-=-")
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
    print_file(fn)


def test_5():
    config_file = Path("test_1.yaml")
    cfg = Yaml(config_file, auto_dump=False)
    cfg["a"] = 1
    cfg["b"]["x"] = 2
    cfg["c"]["y"]["z"] = 45
    cfg.dump()
    config_file.read_text()
    config_file.unlink()


def main():
    try:
        Yaml(Path("config.yaml"))
        test_1()
        test_2()
        test_3()
        test_4()
        test_5()
    except Exception as e:
        print_tb(e)
    finally:
        _remove("test.yaml")
        _remove("config.yaml")


if __name__ == "__main__":
    main()
