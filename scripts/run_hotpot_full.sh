#!/bin/bash
# Full HotpotQA distractor run (7,405 dev questions) + significance, each under a 1 GB RSS
# watchdog so a memory blow-up kills the job instead of the machine (this VM has no swap).
# Resumable: finished questions are cached in results/hotpotqa/cache/.
cd "$(dirname "$0")/.." || exit 1
export PYTHONPATH=.
LIMIT_MB=1000
LOG=results/hotpot_full.log

memguard() {  # memguard <cmd...>: run cmd, kill it if its RSS exceeds LIMIT_MB
  "$@" & local pid=$! peak=0 rss
  while kill -0 "$pid" 2>/dev/null; do
    rss=$(ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024)}')
    [ "${rss:-0}" -gt "$peak" ] && peak=$rss
    if [ "${rss:-0}" -gt "$LIMIT_MB" ]; then echo "MEMGUARD: RSS ${rss}MB > ${LIMIT_MB}MB, killing" >&2; kill -9 "$pid"; fi
    sleep 1
  done
  wait "$pid"; local rc=$?
  echo "MEMGUARD: peak RSS ${peak}MB, exit $rc" >&2
  return $rc
}

{
  echo "== hotpotqa full $(date +%H:%M)"
  memguard .venv/bin/python -m bench.hotpot --full &&
    echo "== hotpotqa significance $(date +%H:%M)" &&
    memguard .venv/bin/python -m bench.significance --dataset hotpotqa --full
  echo "EXIT=$? $(date +%H:%M)"
} > "$LOG" 2>&1
