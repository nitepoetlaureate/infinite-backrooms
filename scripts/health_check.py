#!/usr/bin/env python3
"""Health check script for Infinite AI Backrooms.

This script performs comprehensive health checks for production deployments.
Run periodically to ensure all systems are operational.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import aiohttp

# Note: Import statements for monitoring modules removed to avoid conflicts
# The standalone HealthChecker below provides all necessary functionality


class HealthChecker:
    """Comprehensive health checker for the application."""

    def __init__(self, streamlit_url: str, ollama_url: str):
        """Initialize health checker.

        Args:
            streamlit_url: Base URL for Streamlit app
            ollama_url: Base URL for Ollama API
        """
        self.streamlit_url = streamlit_url.rstrip("/")
        self.ollama_url = ollama_url.rstrip("/")
        self.results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "unknown",
        }

    async def check_streamlit_health(self) -> bool:
        """Check if Streamlit app is responding.

        Returns:
            True if healthy
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.streamlit_url}/_stcore/health", timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    healthy = response.status == 200
                    self.results["checks"]["streamlit"] = {
                        "status": "healthy" if healthy else "unhealthy",
                        "status_code": response.status,
                        "response_time_ms": 0,  # Add timing if needed
                    }
                    return healthy
        except Exception as e:
            self.results["checks"]["streamlit"] = {
                "status": "error",
                "error": str(e),
            }
            return False

    async def check_ollama_health(self) -> bool:
        """Check if Ollama API is responding.

        Returns:
            True if healthy
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m["name"] for m in data.get("models", [])]
                        self.results["checks"]["ollama"] = {
                            "status": "healthy",
                            "status_code": response.status,
                            "models_available": len(models),
                            "models": models,
                        }
                        return True
                    else:
                        self.results["checks"]["ollama"] = {
                            "status": "unhealthy",
                            "status_code": response.status,
                        }
                        return False
        except Exception as e:
            self.results["checks"]["ollama"] = {
                "status": "error",
                "error": str(e),
            }
            return False

    async def check_ollama_inference(self, model: str = "tinyllama") -> bool:
        """Test Ollama inference capability.

        Args:
            model: Model to test (default: tinyllama for speed)

        Returns:
            True if inference works
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": "Hello",
                    "stream": False,
                }
                start_time = datetime.now()
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()

                    if response.status == 200:
                        data = await response.json()
                        self.results["checks"]["ollama_inference"] = {
                            "status": "healthy",
                            "model": model,
                            "response_time_seconds": response_time,
                            "response_received": bool(data.get("response")),
                        }
                        return True
                    else:
                        self.results["checks"]["ollama_inference"] = {
                            "status": "failed",
                            "model": model,
                            "status_code": response.status,
                        }
                        return False
        except asyncio.TimeoutError:
            self.results["checks"]["ollama_inference"] = {
                "status": "timeout",
                "model": model,
                "error": "Inference took longer than 30 seconds",
            }
            return False
        except Exception as e:
            self.results["checks"]["ollama_inference"] = {
                "status": "error",
                "model": model,
                "error": str(e),
            }
            return False

    def check_static_files(self) -> bool:
        """Check if required static files exist.

        Returns:
            True if all files exist
        """
        required_files = [
            "static/css/system.css",
            "streamlit_backroom.py",
            "src/services/ollama_client.py",
        ]

        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        self.results["checks"]["static_files"] = {
            "status": "healthy" if not missing_files else "error",
            "missing_files": missing_files,
            "checked_files": required_files,
        }
        return not missing_files

    def check_log_directory(self) -> bool:
        """Check if log directory is writable.

        Returns:
            True if writable
        """
        log_dir = Path("conversations")
        try:
            log_dir.mkdir(exist_ok=True)
            test_file = log_dir / ".health_check_test"
            test_file.write_text("test")
            test_file.unlink()

            self.results["checks"]["log_directory"] = {
                "status": "healthy",
                "path": str(log_dir.absolute()),
                "writable": True,
            }
            return True
        except Exception as e:
            self.results["checks"]["log_directory"] = {
                "status": "error",
                "path": str(log_dir.absolute()),
                "writable": False,
                "error": str(e),
            }
            return False

    async def run_all_checks(self, skip_inference: bool = False) -> bool:
        """Run all health checks.

        Args:
            skip_inference: Skip inference test (slow)

        Returns:
            True if all checks passed
        """
        print("Running health checks...")
        print(f"Timestamp: {self.results['timestamp']}")
        print("-" * 60)

        checks = [
            ("Streamlit App", self.check_streamlit_health()),
            ("Ollama API", self.check_ollama_health()),
        ]

        # Run async checks
        async_results = await asyncio.gather(*[check for _, check in checks])

        # Run sync checks
        sync_results = [
            ("Static Files", self.check_static_files()),
            ("Log Directory", self.check_log_directory()),
        ]

        # Optional inference check
        if not skip_inference:
            print("Running inference test (this may take a moment)...")
            inference_result = await self.check_ollama_inference()
            async_results.append(inference_result)
            checks.append(("Ollama Inference", inference_result))

        # Combine results
        all_results = list(zip([name for name, _ in checks], async_results)) + sync_results

        # Print results
        all_passed = True
        for name, result in all_results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{name:20s} {status}")
            if not result:
                all_passed = False

        self.results["overall_status"] = "healthy" if all_passed else "unhealthy"

        print("-" * 60)
        print(f"Overall Status: {self.results['overall_status'].upper()}")

        return all_passed

    def save_results(self, output_file: str = "health_check_results.json") -> None:
        """Save results to JSON file.

        Args:
            output_file: Output file path
        """
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to: {output_file}")

    def print_detailed_results(self) -> None:
        """Print detailed results in human-readable format."""
        print("\n" + "=" * 60)
        print("DETAILED HEALTH CHECK RESULTS")
        print("=" * 60)
        print(json.dumps(self.results, indent=2))


async def run_new_health_check(args, streamlit_url: str, skip_inference: bool) -> int:
    """Run health check with new monitoring system.

    Args:
        args: Parsed command line arguments
        streamlit_url: Streamlit URL to check
        skip_inference: Whether to skip inference checks

    Returns:
        Exit code (0 = healthy, 1 = unhealthy)
    """
    # Initialize monitoring
    init_logging(
        log_file="logs/health_check.log",
        log_level=LogLevel.INFO
    )
    logger = get_logger("health_check")
    metrics = get_metrics_collector()

    # Create new health checker
    health_checker = NewHealthChecker()

    # Add health checks
    if streamlit_url:
        health_checker.add_http_check(
            name="streamlit_app",
            url=f"{streamlit_url}/_stcore/health",
            expected_status=200
        )

    if args.ollama_url:
        # Add Ollama API health check
        health_checker.add_http_check(
            name="ollama_api",
            url=f"{args.ollama_url}/api/tags",
            expected_status=200
        )

        # Add Ollama inference check
        async def check_ollama_inference():
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "tinyllama",
                    "prompt": "Hello",
                    "stream": False,
                }
                try:
                    async with session.post(
                        f"{args.ollama_url}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return (HealthStatus.HEALTHY, "Inference successful", {"response_received": bool(data.get("response"))})
                        else:
                            return (HealthStatus.UNHEALTHY, f"Inference failed with status {response.status}", {})
                except Exception as e:
                    return (HealthStatus.UNHEALTHY, f"Inference error: {str(e)}", {})

        if not skip_inference:
            health_checker.add_custom_check("ollama_inference", check_ollama_inference)

    # Add resource checks
    health_checker.add_resource_check("cpu", threshold=80.0)
    health_checker.add_resource_check("memory", threshold=85.0)
    health_checker.add_resource_check("disk", threshold=90.0)

    # Run health checks
    logger.info("Running comprehensive health checks with new monitoring system")
    if args.production:
        print("Running in PRODUCTION mode with new monitoring - focusing on critical health checks")

    system_health = await health_checker.check_all()

    # Record health status metrics
    health_status_value = 1 if system_health.status == HealthStatus.HEALTHY else 0
    metrics.record_gauge("health.overall_status", health_status_value, labels={
        "status": system_health.status.value
    })

    # Print results
    print(f"\nOverall Health Status: {system_health.status.value.upper()}")
    print(f"Summary: {system_health.summary}")
    print(f"Timestamp: {system_health.timestamp}")
    print("\nIndividual Checks:")
    for check in system_health.checks:
        status_symbol = "✓" if check.status == HealthStatus.HEALTHY else "✗"
        print(f"  {status_symbol} {check.name}: {check.status.value.upper()}")
        if check.message:
            print(f"    {check.message}")
        if args.verbose and check.details:
            for key, value in check.details.items():
                print(f"    {key}: {value}")

    # Save results
    results_data = system_health.to_dict()
    with open(args.output, 'w') as f:
        json.dump(results_data, f, indent=2)

    # Handle CI environment
    import os
    if os.getenv("CI"):
        # Create GitHub Actions compatible output
        with open("health_summary.txt", "w") as f:
            f.write(f"Overall Status: {system_health.status.value}\n")
            for check in system_health.checks:
                f.write(f"{check.name}: {check.status.value}\n")

        # Set GitHub Actions output if in GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):
            print(f"::set-output name=health_status::{system_health.status.value}")
            print(f"::set-output name=checks_passed::{system_health.status == HealthStatus.HEALTHY}")

    logger.info(f"Health check completed. Results saved to {args.output}")

    return 0 if system_health.status == HealthStatus.HEALTHY else 1


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = healthy, 1 = unhealthy)
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Health check for Infinite AI Backrooms")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8501",
        help="Base URL for the application (default: http://localhost:8501)",
    )
    parser.add_argument(
        "--streamlit-url",
        default=None,
        help="Streamlit app URL (overrides --base-url for Streamlit checks)",
    )
    parser.add_argument(
        "--ollama-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama API URL (default: from OLLAMA_BASE_URL env var or http://localhost:11434)",
    )
    parser.add_argument(
        "--skip-inference",
        action="store_true",
        help="Skip inference test (faster but less thorough)",
    )
    parser.add_argument(
        "--output",
        default="health_check_results.json",
        help="Output JSON file (default: health_check_results.json)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed results",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (skip inference, focus on critical checks)",
    )
    parser.add_argument(
        "--use-new-monitoring",
        action="store_true",
        help="Use new comprehensive monitoring system",
    )

    args = parser.parse_args()

    # Handle URL logic
    streamlit_url = args.streamlit_url or args.base_url

    # In production mode, skip inference by default
    skip_inference = args.skip_inference or args.production

    if args.use_new_monitoring:
        # Use new monitoring system
        return await run_new_health_check(args, streamlit_url, skip_inference)

    # Legacy health check path
    checker = HealthChecker(streamlit_url, args.ollama_url)

    # Add additional checks for production
    if args.production:
        print("Running in PRODUCTION mode - focusing on critical health checks")
        skip_inference = True

    all_passed = await checker.run_all_checks(skip_inference=skip_inference)

    # Save results in CI environment
    if os.getenv("CI"):
        # Create GitHub Actions compatible output
        with open("health_summary.txt", "w") as f:
            f.write(f"Overall Status: {checker.results['overall_status']}\n")
            for check_name, check_result in checker.results["checks"].items():
                status = check_result.get("status", "unknown")
                f.write(f"{check_name}: {status}\n")

        # Set GitHub Actions output if in GitHub Actions
        if os.getenv("GITHUB_ACTIONS"):
            print(f"::set-output name=health_status::{checker.results['overall_status']}")
            print(f"::set-output name=checks_passed::{all_passed}")

    checker.save_results(args.output)

    if args.verbose or args.production:
        checker.print_detailed_results()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
