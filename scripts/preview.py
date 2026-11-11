"""Development preview compatible with hosts that append Vite-style flags."""
import argparse
import subprocess
import sys
parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', default='8000')
args, _ = parser.parse_known_args()
raise SystemExit(subprocess.call([sys.executable, '-m', 'backend.server', '--host', args.host, '--port', args.port]))
