#!/usr/bin/env python3
"""Basic source-publication checks, not a complete secret scanner. GPL-3.0-or-later."""
from pathlib import Path
import re
import sys

from common import ROOT

EXCLUDED = {'.git', '.cache', '.local', 'dist', '__pycache__'}
FORBIDDEN_SUFFIXES = {'.apk', '.jar', '.so', '.p12', '.jks', '.keystore', '.key', '.pem', '.log', '.password'}
FORBIDDEN_NAMES = {'adbkey', 'adbkey.pub', 'local-auth.json', 'session-state.json', 'state.json', '.env'}
PATTERNS = [
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----'),
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{30,}'),
    re.compile(rb'/' + rb'Users/[^/\s]+/'),
    re.compile(rb'\b192\.168\.\d{1,3}\.\d{1,3}\b'),
]


def main():
    failures, count = [], 0
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED for part in relative.parts) or not path.is_file():
            continue
        count += 1
        if path.suffix in FORBIDDEN_SUFFIXES or path.name in FORBIDDEN_NAMES:
            failures.append(str(relative) + ': private/binary file type')
        if path.stat().st_size > 1_000_000:
            failures.append(str(relative) + ': unexpectedly large source file')
        data = path.read_bytes()
        if any(pattern.search(data) for pattern in PATTERNS):
            failures.append(str(relative) + ': possible private material; inspect locally')
    if failures:
        print('\n'.join(failures), file=sys.stderr)
        raise SystemExit(1)
    print(f'Basic publication audit passed ({count} source files); manually review before pushing.')


if __name__ == '__main__':
    main()
