#!/usr/bin/env python3
"""Prints an xcresult bundle's test totals and failures as workflow annotations.

    summarize.py <bundle.xcresult> <title> <error|warning>

Annotations are readable through the public API, so the outcome can be checked
without downloading logs.
"""

import json
import os
import subprocess
import sys

bundle, title, level = sys.argv[1], sys.argv[2], sys.argv[3]

if not os.path.exists(bundle):
    print(f"::{level} title={title}::no result bundle - the tests did not run")
    sys.exit(0)

raw = subprocess.run(
    ["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", bundle],
    capture_output=True, text=True,
)
if raw.returncode != 0:
    print(f"::{level} title={title}::could not read {bundle}: {raw.stderr.strip()[:300]}")
    sys.exit(0)

summary = json.loads(raw.stdout)
totals = "result={result} total={totalTestCount} passed={passedTests} failed={failedTests} skipped={skippedTests}".format(
    **{key: summary.get(key, "?") for key in ("result", "totalTestCount", "passedTests", "failedTests", "skippedTests")}
)
print(f"::notice title={title}::{totals}")

failures = summary.get("testFailures", [])
names = sorted({failure.get("testIdentifierString") or failure.get("testName", "?") for failure in failures})
if names:
    # One annotation carries every failing test name; nine more carry the first messages.
    print(f"::{level} title={title} - failing tests ({len(names)})::" + " | ".join(names)[:6000])
    for failure in failures[:9]:
        text = " ".join(str(failure.get("failureText", "")).split())[:500]
        print(f"::{level} title={title} - {failure.get('testName', '?')}::{text}")

with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a") as out:
    out.write(f"### {title}\n\n`{totals}`\n\n")
    for name in names:
        out.write(f"- {name}\n")
