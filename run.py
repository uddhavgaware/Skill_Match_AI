"""
SkillMatch AI - Production & Development Application Launcher
Supports both development hot-reload mode and multi-worker production mode.
Can be configured via environment variables or CLI arguments.
"""

import argparse
import multiprocessing
import os
import sys
import uvicorn


def parse_args():
    parser = argparse.ArgumentParser(description="SkillMatch AI Application Launcher")
    parser.add_argument(
        "--prod",
        action="store_true",
        default=os.getenv("ENVIRONMENT", "").lower() == "production",
        help="Run in production mode (multi-worker, no reload, 0.0.0.0 binding)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", None),
        help="Host address to bind the server (default: 0.0.0.0 in prod, 127.0.0.1 in dev)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port number to bind (default: 8000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("WORKERS", "0")),
        help="Number of worker processes in production mode (default: cpu_count * 2 + 1)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=None,
        help="Explicitly enable/disable auto-reload",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "info"),
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Logging level",
    )
    return parser.parse_args()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = parse_args()
    is_prod = args.prod

    # Determine host
    if args.host:
        host = args.host
    else:
        host = "0.0.0.0" if is_prod else "127.0.0.1"

    port = args.port

    # Determine reload and workers
    if is_prod:
        reload_enabled = False if args.reload is None else args.reload
        # In Windows, multi-worker uvicorn via multiprocessing can have spawn nuances,
        # so default to min(multiprocessing.cpu_count(), 4)
        cpu_count = multiprocessing.cpu_count() or 2
        workers = args.workers if args.workers > 0 else min(cpu_count, 4)
    else:
        reload_enabled = True if args.reload is None else args.reload
        workers = 1

    mode_label = "PRODUCTION (Multi-Worker)" if is_prod else "DEVELOPMENT (Hot-Reload)"

    print("=" * 68)
    print(f">> Starting SkillMatch AI Platform [{mode_label}]")
    print(f">> Listening on       : http://{host}:{port}")
    print(f">> API Health Check   : http://{host}:{port}/api/health")
    print(f">> API Documentation  : http://{host}:{port}/docs")
    print(f">> Worker Processes   : {workers}")
    print(f">> Hot Reload         : {'Enabled' if reload_enabled else 'Disabled'}")
    print("=" * 68)

    # In production with multiple workers, reload cannot be True
    if workers > 1:
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            workers=workers,
            log_level=args.log_level,
            access_log=True,
            timeout_keep_alive=65,
        )
    else:
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=reload_enabled,
            log_level=args.log_level,
            access_log=True,
        )


if __name__ == "__main__":
    main()
