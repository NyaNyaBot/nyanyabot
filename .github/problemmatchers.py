#!/usr/bin/env python3
# Taken from Qutebrowser: https://github.com/qutebrowser/qutebrowser/blob/master/scripts/dev/ci/problemmatchers.py
# Licensed under GPLv3
import json
import pathlib
import sys

MATCHERS = {
    # filename.py:1:1: D100 Missing docstring in public module
    "flake8": [
        {
            # "undefined name" is FXXX (i.e. not an error), but e.g. multiple
            # spaces before an operator is EXXX (i.e. an error) - that makes little
            # sense, so let's just treat everything as a warning instead.
            "severity": "warning",
            "pattern":  [
                {
                    "regexp":  r"^(\033\[0m)?([^:]+):(\d+):(\d+): ([A-Z]\d{3}) (.*)$",
                    "file":    2,
                    "line":    3,
                    "column":  4,
                    "code":    5,
                    "message": 6,
                },
            ],
        },
    ],

    # filename.py:80: error: Name 'foo' is not defined  [name-defined]
    "mypy":   [
        {
            "pattern": [
                {
                    "regexp":   r"^(\033\[0m)?([^:]+):(\d+): ([^:]+): (.*)  \[(.*)\]$",
                    "file":     2,
                    "line":     3,
                    "severity": 4,
                    "message":  5,
                    "code":     6,
                },
            ],
        },
    ],

    # For some reason, ANSI color escape codes end up as part of the message
    # GitHub gets with colored pylint output - so we have those escape codes
    # (e.g. "\033[35m...\033[0m") as part of the regex patterns...
    "pylint": [
        {
            # filename.py:80:10: E0602: Undefined variable 'foo' (undefined-variable)
            "severity": "error",
            "pattern":  [
                {
                    "regexp":  r"^([^:]+):(\d+):(\d+): (E\d+): \033\[[\d;]+m([^\033]+).*$",
                    "file":    1,
                    "line":    2,
                    "column":  3,
                    "code":    4,
                    "message": 5,
                },
            ],
        },
        {
            # filename.py:78:14: W0613: Unused argument 'unused' (unused-argument)
            "severity": "warning",
            "pattern":  [
                {
                    "regexp":  r"^([^:]+):(\d+):(\d+): ([A-DF-Z]\d+): \033\[[\d;]+m([^\033]+).*$",
                    "file":    1,
                    "line":    2,
                    "column":  3,
                    "code":    4,
                    "message": 5,
                },
            ],
        },
    ],

    "tests":  [
        {
            # pytest test summary output
            "severity": "error",
            "pattern":  [
                {
                    "regexp": r'^=+ short test summary info =+$',
                },
                {
                    "regexp":  r"^((ERROR|FAILED) .*)",
                    "message": 1,
                    "loop":    True,
                }
            ],
        },
        {
            # pytest error lines
            # E       end2end.fixtures.testprocess.WaitForTimeout: Timed out
            #         after 15000ms waiting for [...]
            "severity": "error",
            "pattern":  [
                {
                    "regexp":  r'^\033\[1m\033\[31mE       ([a-zA-Z0-9.]+: [^\033]*)\033\[0m$',
                    "message": 1,
                },
            ],
        },
    ]
}


def add_matcher(output_dir, owner, data):
    data['owner'] = owner
    out_data = {'problemMatcher': [data]}
    output_file = output_dir / '{}.json'.format(owner)
    with output_file.open('w', encoding='utf-8') as f:
        json.dump(out_data, f)

    print("::add-matcher::{}".format(output_file))


def main(testenv, tempdir):
    testenv = sys.argv[1]
    if testenv.startswith('py3'):
        testenv = 'tests'

    if testenv not in MATCHERS:
        return

    output_dir = pathlib.Path(tempdir)

    for idx, data in enumerate(MATCHERS[testenv]):
        owner = '{}-{}'.format(testenv, idx)
        add_matcher(output_dir=output_dir, owner=owner, data=data)


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
