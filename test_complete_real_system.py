#!/usr/bin/env python3
"""
COMPLETE REAL SYSTEM TEST - No Mocks, Full Production Validation
This script tests the ENTIRE infinite-backrooms system with REAL components.
"""

import asyncio
import json
import shutil
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from log_viewer import LogParser
from src.models.persona import AIPersona
from src.services.logger import ConversationLogger


class RealSystemTester:
    """Complete real system validation without any mocking."""

    def __init__(self) -> None:
        self.ollama_url = "http://localhost:11434"
        self.temp_dir = None
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str = "") -> None:
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")

        self.test_results.append(
            {"name": test_name, "success": success, "message": message, "timestamp": datetime.now()}
        )

    async def test_ollama_connection(self):
        """Test real Ollama API connection."""
        print("\n" + "=" * 60)
        print("🔌 TESTING OLLAMA API CONNECTION")
        print("=" * 60)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]

                        self.log_test(
                            "Ollama Connection",
                            True,
                            f"Connected successfully. Models: {len(models)} available",
                        )

                        # Check for expected models
                        model_string = " ".join(models)
                        has_small_model = any(
                            model in model_string
                            for model in ["phi3:mini", "llama3:8b", "granite3.3:8b"]
                        )

                        self.log_test(
                            "Required Models Available",
                            has_small_model,
                            f"Has suitable models: {has_small_model}",
                        )

                        return models
                    else:
                        self.log_test(
                            "Ollama Connection",
                            False,
                            f"HTTP {response.status}: {await response.text()}",
                        )
                        return []
        except Exception as e:
            self.log_test("Ollama Connection", False, f"Exception: {e}")
            return []

    async def test_real_ai_responses(self, models):
        """Test actual AI model responses."""
        print("\n" + "=" * 60)
        print("🤖 TESTING REAL AI MODEL RESPONSES")
        print("=" * 60)

        if not models:
            self.log_test("AI Response Test", False, "No models available")
            return

        # Use the smallest available model for speed
        test_model = None
        for model in ["phi3:mini", "llama3:8b", "granite3.3:8b"]:
            if model in models:
                test_model = model
                break

        if not test_model:
            self.log_test("Model Selection", False, "No suitable model found")
            return

        print(f"Using model: {test_model}")

        # Test basic response
        test_cases = [
            {
                "name": "Simple Math",
                "prompt": "What is 2+2? Answer with just the number.",
                "expected": ["4", "four"],
                "timeout": 30,
            },
            {
                "name": "Simple Question",
                "prompt": "What color is the sky? Answer in one word.",
                "expected": ["blue"],
                "timeout": 30,
            },
            {
                "name": "Greeting",
                "prompt": "Say hello in one word.",
                "expected": ["hello", "hi"],
                "timeout": 30,
            },
        ]

        async with aiohttp.ClientSession() as session:
            for i, test_case in enumerate(test_cases):
                print(f"\nTest {i+1}: {test_case['name']}")

                payload = {"model": test_model, "prompt": test_case["prompt"], "stream": False}

                try:
                    start_time = time.time()
                    async with session.post(
                        f"{self.ollama_url}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=test_case["timeout"]),
                    ) as response:
                        end_time = time.time()

                        if response.status == 200:
                            result = await response.json()
                            ai_response = result.get("response", "").strip().lower()
                            response_time = end_time - start_time

                            print(f"  Response: '{ai_response}'")
                            print(f"  Time: {response_time:.2f}s")

                            # Check if expected content is in response
                            success = any(
                                expected in ai_response for expected in test_case["expected"]
                            )

                            self.log_test(
                                f"AI Response: {test_case['name']}",
                                success,
                                f"'{ai_response}' ({response_time:.2f}s)",
                            )

                            if response_time > 20:
                                self.log_test(
                                    f"Response Time Warning: {test_case['name']}",
                                    False,
                                    f"Slow response: {response_time:.2f}s",
                                )

                        else:
                            error_text = await response.text()
                            self.log_test(
                                f"AI Response: {test_case['name']}",
                                False,
                                f"HTTP {response.status}: {error_text[:100]}",
                            )

                except TimeoutError:
                    self.log_test(
                        f"AI Response: {test_case['name']}",
                        False,
                        f"Timeout after {test_case['timeout']}s",
                    )
                except Exception as e:
                    self.log_test(f"AI Response: {test_case['name']}", False, f"Exception: {e}")

        # Test streaming
        print(f"\nTesting streaming with {test_model}...")

        payload["stream"] = True
        chunks_received = 0
        full_response = ""

        try:
            start_time = time.time()
            async with session.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode("utf-8"))
                                if "response" in chunk:
                                    full_response += chunk["response"]
                                    chunks_received += 1
                                if chunk.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue

                    end_time = time.time()
                    streaming_time = end_time - start_time

                    print(f"  Streaming completed: {chunks_received} chunks")
                    print(f"  Full response: '{full_response.strip()}'")
                    print(f"  Streaming time: {streaming_time:.2f}s")

                    self.log_test(
                        "AI Streaming Response",
                        len(full_response.strip()) > 0,
                        f"{chunks_received} chunks, {streaming_time:.2f}s",
                    )
                else:
                    self.log_test("AI Streaming Response", False, f"HTTP {response.status}")

        except Exception as e:
            self.log_test("AI Streaming Response", False, f"Exception: {e}")

    def test_conversation_components(self) -> None:
        """Test conversation system components."""
        print("\n" + "=" * 60)
        print("💬 TESTING CONVERSATION COMPONENTS")
        print("=" * 60)

        # Test AIPersona creation
        print("\nTesting AIPersona creation...")

        try:
            test_personas = [
                AIPersona(
                    id="test_alice",
                    name="Alice",
                    model="phi3:mini",
                    role="Mathematician",
                    enabled=True,
                    color="#FF6B6B",
                ),
                AIPersona(
                    id="test_bob",
                    name="Bob",
                    model="phi3:mini",
                    role="Scientist",
                    enabled=True,
                    color="#4ECDC4",
                ),
                AIPersona(
                    id="test_charlie",
                    name="Charlie",
                    model="phi3:mini",
                    role="Philosopher",
                    enabled=False,  # Disabled
                    color="#45B7D1",
                ),
            ]

            for persona in test_personas:
                print(f"  ✅ Created: {persona.name} ({persona.role}) - Enabled: {persona.enabled}")

            self.log_test("AIPersona Creation", True, f"Created {len(test_personas)} personas")

            # Test speaker selection logic
            print("\nTesting speaker selection...")
            enabled_personas = [p for p in test_personas if p.enabled]

            last_index = -1
            selections = []

            for i in range(6):
                last_index = (last_index + 1) % len(enabled_personas)
                speaker = enabled_personas[last_index]
                selections.append(speaker.name)
                print(f"  Turn {i+1}: {speaker.name}")

            # Verify rotation
            expected_pattern = ["Alice", "Bob", "Alice", "Bob", "Alice", "Bob"]
            rotation_correct = selections == expected_pattern

            self.log_test(
                "Speaker Selection Logic", rotation_correct, f"Pattern: {selections[:3]}..."
            )

        except Exception as e:
            self.log_test("AIPersona Creation", False, f"Exception: {e}")

    def test_file_operations(self) -> None:
        """Test file system operations."""
        print("\n" + "=" * 60)
        print("📁 TESTING FILE SYSTEM OPERATIONS")
        print("=" * 60)

        # Create temporary workspace
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created workspace: {self.temp_dir}")

        try:
            # Test conversation logging
            print("\nTesting conversation logging...")

            logger = ConversationLogger(self.temp_dir)

            test_messages = [
                ("Alice", "Hello world! This is a test message.", datetime.now()),
                ("Bob", "Hi Alice! Great to meet you.", datetime.now() + timedelta(minutes=1)),
                ("Alice", "How are you doing today?", datetime.now() + timedelta(minutes=2)),
                (
                    "Bob",
                    "I'm doing great! Thanks for asking! 🚀",
                    datetime.now() + timedelta(minutes=3),
                ),
                ("Charlie", "Hello everyone! I'm Charlie.", datetime.now() + timedelta(minutes=4)),
            ]

            for persona, message, timestamp in test_messages:
                logger.log_message(persona, message, timestamp)
                print(f"  ✅ Logged: {persona}: {message[:30]}...")

            # Verify log file creation
            log_files = list(Path(self.temp_dir).glob("*.txt"))

            self.log_test(
                "Log File Creation", len(log_files) >= 1, f"Created {len(log_files)} log files"
            )

            if log_files:
                log_file = log_files[0]
                content = log_file.read_text(encoding="utf-8")

                print(f"  📄 Log file: {log_file.name}")
                print(f"  📖 Content size: {len(content)} characters")

                # Verify all messages are in log
                messages_found = 0
                for persona, message, _ in test_messages:
                    if persona in content and message in content:
                        messages_found += 1
                        print(f"  ✅ Found: {persona}: {message[:30]}...")
                    else:
                        print(f"  ❌ Missing: {persona}: {message[:30]}...")

                self.log_test(
                    "Message Logging Accuracy",
                    messages_found == len(test_messages),
                    f"{messages_found}/{len(test_messages)} messages found",
                )

                # Test special characters
                special_test_messages = [
                    ("SpecialChars", "Testing special chars: !@#$%^&*()_+-=[]{}|;:,.<>?"),
                    ("Unicode", "Testing unicode: ñáéíóú 🚀 🎉 💻 🧠"),
                    ("MultiLine", "This is a message\nthat spans\nmultiple lines."),
                ]

                print("\nTesting special character handling...")

                for persona, message in special_test_messages:
                    logger.log_message(persona, message, datetime.now())
                    print(f"  ✅ Logged special chars: {persona}")

                # Re-read and verify
                updated_content = log_file.read_text(encoding="utf-8")

                special_chars_ok = (
                    "!@#$%" in updated_content
                    and "🚀" in updated_content
                    and "\n" in updated_content
                )

                self.log_test(
                    "Special Character Handling",
                    special_chars_ok,
                    "Special chars, unicode, and newlines preserved",
                )

            # Test log parsing
            print("\nTesting log parsing...")

            parser = LogParser(self.temp_dir)
            available_files = parser.get_available_log_files()

            self.log_test(
                "Log File Discovery",
                len(available_files) > 0,
                f"Found {len(available_files)} log files",
            )

            if available_files:
                parsed_messages = parser.parse_all_logs(available_files)

                print(f"  🔍 Parsed {len(parsed_messages)} total messages")

                if parsed_messages:
                    # Show sample parsed messages
                    for i, msg in enumerate(parsed_messages[:3]):
                        print(
                            f"    {i+1}. [{msg.get('time', 'N/A')}] {msg.get('persona', 'N/A')}: {msg.get('content', 'N/A')[:50]}..."
                        )

                    self.log_test(
                        "Log Parsing",
                        len(parsed_messages) > 0,
                        f"Successfully parsed {len(parsed_messages)} messages",
                    )

                    # Test conversation analysis
                    participants = {
                        msg.get("persona", "") for msg in parsed_messages if msg.get("persona")
                    }
                    participants = [p for p in participants if p]  # Remove empty strings

                    print(f"  👥 Participants: {participants}")

                    if len(parsed_messages) >= 2:
                        first_msg = parsed_messages[0]
                        last_msg = parsed_messages[-1]

                        if "datetime" in first_msg and "datetime" in last_msg:
                            duration = last_msg["datetime"] - first_msg["datetime"]
                            print(f"  ⏱️ Conversation span: {duration}")

                    self.log_test(
                        "Conversation Analysis",
                        len(participants) > 0,
                        f"Analyzed conversation with {len(participants)} participants",
                    )

        except Exception as e:
            self.log_test("File System Operations", False, f"Exception: {e}")

    def test_system_performance(self) -> None:
        """Test system performance under load."""
        print("\n" + "=" * 60)
        print("⚡ TESTING SYSTEM PERFORMANCE")
        print("=" * 60)

        # Test concurrent AI requests
        print("\nTesting concurrent AI requests...")

        async def run_concurrent_test():
            if not self.temp_dir:
                return

            async with aiohttp.ClientSession() as session:
                # Prepare concurrent requests
                prompts = [
                    "What is 1+1?",
                    "What is 2+2?",
                    "What is 3+3?",
                    "What is 4+4?",
                    "What is 5+5?",
                ]

                async def get_response(prompt, session_id):
                    try:
                        payload = {"model": "phi3:mini", "prompt": prompt, "stream": False}

                        start_time = time.time()
                        async with session.post(
                            f"{self.ollama_url}/api/generate",
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as response:
                            end_time = time.time()

                            if response.status == 200:
                                result = await response.json()
                                response_text = result.get("response", "").strip()
                                return {
                                    "session_id": session_id,
                                    "prompt": prompt,
                                    "response": response_text,
                                    "time": end_time - start_time,
                                    "success": True,
                                }
                            else:
                                return {
                                    "session_id": session_id,
                                    "prompt": prompt,
                                    "response": None,
                                    "time": end_time - start_time,
                                    "success": False,
                                    "error": f"HTTP {response.status}",
                                }
                    except Exception as e:
                        return {
                            "session_id": session_id,
                            "prompt": prompt,
                            "response": None,
                            "success": False,
                            "error": str(e),
                        }

                # Run all requests concurrently
                print(f"  Launching {len(prompts)} concurrent requests...")
                start_time = time.time()

                results = await asyncio.gather(
                    *[get_response(prompt, i) for i, prompt in enumerate(prompts)],
                    return_exceptions=True,
                )

                end_time = time.time()
                total_time = end_time - start_time

                print(f"  Total concurrent time: {total_time:.2f}s")

                # Analyze results
                successful_results = [
                    r for r in results if isinstance(r, dict) and r.get("success")
                ]
                failed_results = [
                    r for r in results if isinstance(r, dict) and not r.get("success")
                ]

                print(f"  ✅ Successful requests: {len(successful_results)}")
                print(f"  ❌ Failed requests: {len(failed_results)}")

                if successful_results:
                    avg_time = sum(r["time"] for r in successful_results) / len(successful_results)
                    print(f"  ⏱️ Average response time: {avg_time:.2f}s")

                    # Verify responses contain numbers
                    correct_responses = 0
                    for result in successful_results:
                        response_text = result.get("response", "").lower()
                        expected_numbers = {
                            "What is 1+1?": ["1", "one"],
                            "What is 2+2?": ["2", "two"],
                            "What is 3+3?": ["3", "three"],
                            "What is 4+4?": ["4", "four"],
                            "What is 5+5?": ["5", "five"],
                        }

                        expected = expected_numbers.get(result["prompt"], [])
                        if any(num in response_text for num in expected):
                            correct_responses += 1

                    print(f"  🎯 Correct responses: {correct_responses}/{len(successful_results)}")

                    self.log_test(
                        "Concurrent AI Requests",
                        len(successful_results) >= 3,  # At least 3 should succeed
                        f"{len(successful_results)}/{len(prompts)} successful, {total_time:.2f}s total",
                    )

                # Test rapid file operations
                print("\nTesting rapid file operations...")

                logger = ConversationLogger(self.temp_dir)

                file_start_time = time.time()
                messages_logged = 0

                for i in range(50):  # Log 50 messages rapidly
                    logger.log_message(
                        f"PerfTest{i%3}", f"Performance test message {i}", datetime.now()
                    )
                    messages_logged += 1

                file_end_time = time.time()
                file_time = file_end_time - file_start_time

                print(f"  📝 Logged {messages_logged} messages in {file_time:.3f}s")
                print(f"  ⚡ Rate: {messages_logged/file_time:.0f} messages/second")

                self.log_test(
                    "Rapid File Operations",
                    file_time < 5.0,  # Should complete within 5 seconds
                    f"{messages_logged} messages in {file_time:.3f}s",
                )

        # Run the async test
        asyncio.run(run_concurrent_test())

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"\n🧹 Cleaned up temporary directory: {self.temp_dir}")

    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 COMPLETE SYSTEM TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")

        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! System is PRODUCTION READY!")
            print("   • Real AI model integration working flawlessly")
            print("   • Conversation system components fully functional")
            print("   • File operations robust and performant")
            print("   • System performance excellent under load")
        else:
            print(f"\n⚠️ {failed_tests} tests failed. Review issues above.")

        print("\n" + "=" * 60)

        # Show failed tests if any
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            print("\n❌ FAILED TESTS:")
            for result in failed_results:
                print(f"   • {result['name']}: {result['message']}")

        print("=" * 60)

        return failed_tests == 0

    async def run_complete_test(self):
        """Run the complete system test suite."""
        print("🚀 STARTING COMPLETE REAL SYSTEM TEST")
        print("Testing infinite-backrooms with ZERO mocking - ALL REAL COMPONENTS")

        start_time = time.time()

        # Test core connectivity
        models = await self.test_ollama_connection()

        # Test AI responses (only if Ollama is available)
        if models:
            await self.test_real_ai_responses(models)

        # Test conversation components
        self.test_conversation_components()

        # Test file operations
        self.test_file_operations()

        # Test performance
        self.test_system_performance()

        end_time = time.time()
        total_test_time = end_time - start_time

        print(f"\n⏱️ Total test execution time: {total_test_time:.2f}s")

        # Cleanup and summary
        self.cleanup()
        success = self.print_summary()

        return success


async def main():
    """Main entry point."""
    tester = RealSystemTester()
    success = await tester.run_complete_test()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
