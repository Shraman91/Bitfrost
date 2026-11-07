import asyncio
import traceback
from backend.tests.test_proxy import (
    test_proxy_run_not_found,
    test_proxy_limits_enforced,
    test_proxy_forwards_and_records_usage
)

async def main():
    tests = [
        ("test_proxy_run_not_found", test_proxy_run_not_found),
        ("test_proxy_limits_enforced", test_proxy_limits_enforced),
        ("test_proxy_forwards_and_records_usage", test_proxy_forwards_and_records_usage),
    ]
    passed = 0
    failed = 0
    print("=" * 60, flush=True)
    print("Running Metering Proxy Unit Tests", flush=True)
    print("=" * 60, flush=True)
    for name, test_fn in tests:
        print(f"Running {name}...", flush=True)
        try:
            await test_fn()
            print(f"[PASS] {name}", flush=True)
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}", flush=True)
            traceback.print_exc()
            failed += 1
    print("=" * 60, flush=True)
    print(f"Results: {passed} passed, {failed} failed", flush=True)
    print("=" * 60, flush=True)
    if failed > 0:
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
