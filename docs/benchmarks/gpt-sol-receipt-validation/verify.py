#!/usr/bin/env python3
"""Offline verification. No provider calls, relay requests, or real credentials."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
MODELS = {'gpt-5.6-sol': 10, 'gpt-6-sol': 8, 'gpt-6-astra': 10, 'claude-opus-5-5': 31}
WORKER = '''import io,json,sys,unittest
suite=unittest.defaultTestLoader.discover(sys.argv[1],pattern=sys.argv[2])
result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)
print(json.dumps({'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'failure_ids':sorted(t.id() for t,_ in result.failures),'error_ids':sorted(t.id() for t,_ in result.errors)}))
'''


def matches(result, count, failures):
    return all(result.get(k) == v for k, v in
               {'run': count, 'failures': failures, 'errors': 0, 'skipped': 0}.items())


def run_suite(target, suite, count, failures=0, pattern='test*.py'):
    env = {'PATH': os.defpath, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(ROOT / target)}
    proc = subprocess.run([sys.executable, '-c', WORKER, suite, pattern], cwd=ROOT,
                          env=env, capture_output=True, text=True, timeout=60, check=True)
    result = json.loads(proc.stdout)
    result.update(target=target, suite=suite, expected_count=count, expected_failures=failures)
    result['passed'] = matches(result, count, failures)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'historical-hashes.json').read_text())
    hashes_ok = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
                    for p, h in manifest['sha256'].items())
    results = [run_suite('baseline', 'tests', 30, 19)]
    for model, count in MODELS.items():
        results.append(run_suite('candidates/' + model, 'tests', 30))
        results.append(run_suite('candidates/' + model, 'candidates/' + model, count, pattern='test_candidate.py'))
    for model in ['gpt-5.6-sol', 'gpt-6-sol']:
        results.append(run_suite('followup-v1/' + model, 'tests', 30))
        results.append(run_suite('followup-v1/' + model, 'followup-v1/tests', 1))
    report = {'verified_at': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
              'platform': platform.system(), 'execution': 'local offline fixture tests; no model inference',
              'historical_hashes_match': hashes_ok, 'results': results,
              'passed': hashes_ok and all(r['passed'] for r in results)}
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
