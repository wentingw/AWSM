"""Wait for completed author handoff, verify regeneration, then fresh final review."""
import argparse, json, subprocess, sys, time
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--method', choices=['M1', 'M2', 'M3', 'M4'], required=True)
    a = p.parse_args()
    label = a.method.lower() + '_repair'
    events = RUN / 'provenance' / (label + '_events.jsonl')
    final = RUN / 'provenance' / (label + '_final.txt')
    status = RUN / 'provenance' / (a.method.lower() + '_post_repair_stage.json')
    def record(stage, **extra):
        status.write_text(json.dumps(dict(method=a.method, stage=stage, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **extra), indent=2) + '\n')
        print(a.method, stage, flush=True)
    record('waiting_for_author_completion')
    while True:
        if final.exists() and events.exists():
            rows = []
            for line in events.read_text().splitlines():
                try: rows.append(json.loads(line))
                except json.JSONDecodeError: pass
            if rows and rows[-1].get('type') == 'turn.completed': break
            if rows and rows[-1].get('type') == 'turn.failed':
                record('author_failed'); return
        time.sleep(10)
    try:
        record('rebuild_verification')
        with (RUN / 'provenance' / (a.method.lower() + '_rebuild.log')).open('w') as log:
            subprocess.run([sys.executable, str(RUN/'tools/verify_rebuild.py'), '--method', a.method], stdout=log, stderr=subprocess.STDOUT, check=True)
        record('final_review')
        subprocess.run([sys.executable, str(RUN/'tools/launch_phase.py'), '--method', a.method, '--phase', 'final_review'], check=True)
        review = json.loads((RUN/'models'/a.method/'independent_review/final_review.json').read_text())
        record('final_review_finished', review_status=review['status'], blockers=review.get('technical_protocol_blockers', []))
    except Exception as exc:
        record('failed', error=str(exc)); raise

if __name__ == '__main__': main()
