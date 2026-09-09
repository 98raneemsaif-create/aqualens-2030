"""Capture a real setup command, redacting credential-bearing log lines."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys


if __name__ == '__main__':
    output = Path(sys.argv[1])
    command = sys.argv[2:]
    if not command:
        raise SystemExit('Usage: capture_phase_a.py OUTPUT COMMAND [ARG ...]')
    output.parent.mkdir(parents=True, exist_ok=True)
    sensitive = re.compile(r'password|secret|authorization|bearer|fernet|\bjwt\b|access_token|refresh_token', re.I)
    with output.open('w', encoding='utf-8') as log:
        log.write('Started UTC: ' + datetime.now(timezone.utc).isoformat() + '\n')
        log.write('Command argv: ' + json.dumps(command) + '\n')
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding='utf-8', errors='replace')
        for line in process.stdout:
            safe = '[REDACTED credential-related log line]\n' if sensitive.search(line) else line
            log.write(safe)
            log.flush()
            print(safe, end='', flush=True)
        status = process.wait()
        log.write('Exit code: ' + str(status) + '\n')
        log.write('Finished UTC: ' + datetime.now(timezone.utc).isoformat() + '\n')
    raise SystemExit(status)
