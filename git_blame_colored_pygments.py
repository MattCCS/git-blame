"""
"""

import argparse
import datetime
import math
import os
import pathlib
import re
import subprocess

from typing import Any, List

from termcolor import colored
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import CppLexer, PythonLexer

os.environ["FORCE_COLOR"] = "1"


cpp_lexer = CppLexer()
python_lexer = PythonLexer()
terminal_formatter = Terminal256Formatter(style="monokai")

DATETIME_NOW = datetime.datetime.now()

CPP_FILE_SUFFIXES = {
    ".cpp",
    ".c",
    ".cc",
    ".h",
    ".hpp",
    ".hh",
}


def colorize_cpp(code):
    return highlight(code, cpp_lexer, terminal_formatter)


def colorize_python(code):
    return highlight(code, python_lexer, terminal_formatter)


def color_and_justify(text, color=None, width=0, attrs=None):
    attrs = attrs or []
    # ANSI adds 9
    # Each attr adds 4
    return colored(text, color=color, attrs=attrs).ljust(width + 9 + 4 * len(attrs))


def color_date(dt, tz):
    dt_human = dt.strftime("%Y-%m-%d %H:%M:%S ") + tz

    color = None
    attrs = None
    dt_diff = DATETIME_NOW - dt
    if dt_diff < datetime.timedelta(days=30):
        color = "red"
        attrs = ["bold"]
    elif dt_diff > datetime.timedelta(days=365):
        color = "blue"
        attrs=["bold"]

    return color_and_justify(dt_human, color=color, attrs=attrs)


def number_of_lines_in_file(file_path: pathlib.Path) -> int:
    with open(file_path, "rb") as f:
        return sum(1 for _ in f)


def colorize_file_with_colorizer_and_split_by_line(
    colorizer: Any, file_path: pathlib.Path
) -> List[str]:
    with open(file_path, "rb") as infile:
        code = infile.read()

    colorized = colorizer(code)
    return colorized.splitlines()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path", type=pathlib.Path, help="Path to the file you wish to blame"
    )
    args, unknownargs = parser.parse_known_args()
    return (args, unknownargs)


def main():
    (args, unknownargs) = parse_args()
    file_path: pathlib.Path = args.file_path

    blame_output = subprocess.check_output(
        ["git", "blame", "--color-by-age", "--line-porcelain", file_path, *unknownargs]
    )

    author_color = {}

    colors = [
        # "grey",
        "red",
        "green",
        "yellow",
        "blue",
        "magenta",
        "cyan",
        "white",
    ]

    color_index = 0
    line_number = 0
    longest_author_name = 0
    line_number_chars = int(math.log10(number_of_lines_in_file(file_path))) + 1

    lines = blame_output.splitlines()

    colorizer = lambda code: code.decode("utf-8")
    if file_path.suffix in CPP_FILE_SUFFIXES:
        colorizer = lambda code: colorize_cpp(code)
    elif file_path.suffix == ".py":
        colorizer = lambda code: colorize_python(code)

    full_colorized_code_by_line = colorize_file_with_colorizer_and_split_by_line(
        colorizer=colorizer, file_path=file_path
    )

    for line in lines:
        m = re.search(b"^author\s+(.*)$", line)
        if m:
            author = m.group(1)
            author = author.strip().decode()
            longest_author_name = max(longest_author_name, len(author))

    lines_to_print = []

    for line in lines:
        if m := re.search(b"^author\s+(.*)$", line):
            author = m.group(1)
            author = author.strip().decode()

            if not author in author_color:
                color_index = (color_index + 1) % len(colors)
                author_color[author] = colors[color_index]

            continue

        if m := re.search(b"^author-time\s+(.*)$", line):
            author_timestamp = m.group(1)
            author_datetime = datetime.datetime.fromtimestamp(int(author_timestamp))
            continue

        if m := re.search(b"^author-tz\s+(.*)$", line):
            author_tz = m.group(1).decode("utf-8")
            continue

        if m := re.search(b"^([0-9a-f]{40})\s+(.*)$", line):
            human_hash = m.group(1).decode("utf-8")[:10]
            continue

        if not re.search(b"^\t(.*)$", line):
            continue

        human_date = color_date(dt=author_datetime, tz=author_tz)
        human_name = color_and_justify(
            author, author_color[author], width=longest_author_name, attrs=["bold"]
        )
        human_lineno = str(line_number).rjust(line_number_chars)
        try:
            human_code = full_colorized_code_by_line[line_number]
        except IndexError:
            # The syntax highlighters strip trailing newlines.
            human_code = ""

        lines_to_print.append(
            f"{human_hash} ({human_name} {human_date}   {human_lineno}) {human_code}"
        )
        line_number += 1

    print("\n".join(lines_to_print))


if __name__ == "__main__":
    main()
