#!/usr/bin/env python3

import os
import readline
import shutil
import subprocess
import traceback
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any, Callable, Optional, Union


class ShellProgram:
    executable: str
    args: list[str]

    def __init__(self, executable: str, *args):
        self.executable = executable
        self.args = list(map(str, args))

    def run(self, check: bool = True, **kwargs) -> subprocess.Popen:
        process = subprocess.Popen([self.executable, *self.args], executable=self.executable, **kwargs)
        if check:
            ret: int = process.wait()
            assert ret == 0, f"{self.executable} returned {ret}"
        return process

    def __str__(self) -> str:
        process = self.run(stdout=subprocess.PIPE)
        return process.stdout.read().decode()

    def __repr__(self) -> str:
        self.run()
        return ""

    def __or__(self, other: 'ShellProgram') -> 'PipedShellProgram':
        return PipedShellProgram(self, other)


@dataclass
class PipedShellProgram:
    left: Union[ShellProgram, 'PipedShellProgram']
    right: Union[ShellProgram, 'PipedShellProgram']

    def run(self, check: bool = True, stdin: Optional[int] = None, stdout: Optional[int] = None) -> subprocess.Popen:
        left_process = self.left.run(check=False, stdin=stdin, stdout=subprocess.PIPE)
        right_process = self.right.run(stdin=left_process.stdout, stdout=stdout)
        if check:
            ret2: int = right_process.wait()
            assert ret2 == 0, f"Process returned {ret2}"
            ret1: int = left_process.wait()
            assert ret1 == 0, f"Process returned {ret1}"
        return right_process

    def __str__(self) -> str:
        process = self.run(stdout=subprocess.PIPE)
        return process.stdout.read().decode()

    def __repr__(self) -> str:
        self.run()
        return ""




class ShellDict(dict):
    """A special dict subclass that returns Popen objects if the requested names are
    found in the PATH variable."""
    def __getitem__(self, key: str) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            if (executable := shutil.which(key)):
                return partial(ShellProgram, executable)
            raise


def default_prompt() -> str:
    prompt: list[str] = []
    prompt.append(f"{os.getlogin()}@{os.uname().nodename.split('.')[0]}")

    try:
        prompt.append(str('~' / Path.cwd().relative_to(Path.home())))
    except ValueError:
        prompt.append(str(Path.cwd()))

    if os.geteuid() == 0:
        prompt.append("#")
    else:
        prompt.append("$")

    prompt.append('')
    return ' '.join(prompt)


def main() -> None:
    env: dict[str, str] = os.environ
    globals_: dict[str, Any] = ShellDict(locals().copy())

    history_path: Path = Path("~/.pysh_history").expanduser()
    history_path.touch()
    readline.read_history_file(history_path)

    globals_["prompt_function"] = default_prompt

    pyshrc_path: Path = Path("~/.pyshrc").expanduser()
    if pyshrc_path.is_file():
        exec(pyshrc_path.read_text(), globals_)

    while True:
        try:
            command: str = input(globals_['prompt_function']())
            if not command:
                continue

            try:
                ret: object = eval(command, globals_)
                if ret is not None:
                    end: str = "\n"
                    if isinstance(ret, (ShellProgram, PipedShellProgram)):
                        end = ""
                    print(repr(ret), end=end)
            except SyntaxError:
                exec(command, globals_)
        except (EOFError, KeyboardInterrupt):
            print()
            break
        except Exception:
            traceback.print_exc()
    readline.write_history_file(history_path)


if __name__ == '__main__':
    main()
