# playwright-streamlit-e2e-tester

**Purpose**: Create end-to-end browser tests for Streamlit applications using Playwright

**Use When**: Need to validate complete user workflows, test UI interactions, or ensure production readiness

---

## Domain Knowledge

### Playwright for Streamlit
- Playwright provides reliable browser automation
- Works with Streamlit's dynamic rerun model
- Supports async/await patterns natively
- Handles JavaScript-heavy applications well

### Streamlit UI Behavior
- Streamlit reruns script on every interaction
- Components update asynchronously
- Session state persists across reruns
- Some operations trigger page reloads

### E2E Testing Best Practices
- Test from user perspective
- Validate complete workflows
- Test across multiple browsers
- Capture screenshots on failure
- Measure performance metrics

### Common Streamlit Selectors
- Text inputs: `input[type="text"]`
- Buttons: `button[kind="primary"]`
- Selectboxes: `[data-baseweb="select"]`
- Text areas: `textarea`
- Markdown: `[data-testid="stMarkdown"]`

---

## Workflow

### Step 1: Setup Playwright Infrastructure (30-45 min)

**Install Dependencies**:
```bash
# Install Playwright
pip install playwright pytest-playwright

# Install browsers
playwright install chromium firefox webkit

# Verify installation
playwright --version
```

**Create Playwright Configuration**:
```python
# pytest.ini or pyproject.toml
[pytest]
addopts =
    --headed  # Run with visible browser during development
    --slowmo=100  # Slow down operations for debugging
    --browser=chromium
    --browser=firefox
    --screenshot=only-on-failure
    --video=retain-on-failure

[tool.pytest.ini_options]
markers =
    e2e: End-to-end browser tests
    slow: Slow-running tests
    visual: Visual regression tests
```

### Step 2: Create Base Test Infrastructure (45-60 min)

**Pattern: Base Streamlit Test Class**:
```python
"""Base infrastructure for Streamlit E2E tests."""
import pytest
from playwright.async_api import Page, expect
from typing import AsyncGenerator
import asyncio


class StreamlitTestBase:
    """Base class for Streamlit E2E tests.

    Provides common utilities for interacting with Streamlit applications.
    """

    BASE_URL = "http://localhost:8501"
    DEFAULT_TIMEOUT = 30000  # 30 seconds

    @pytest.fixture(autouse=True)
    async def setup(self, page: Page):
        """Setup test environment before each test.

        Args:
            page: Playwright page fixture
        """
        self.page = page
        page.set_default_timeout(self.DEFAULT_TIMEOUT)

        # Navigate to app
        await page.goto(self.BASE_URL)

        # Wait for Streamlit to be ready
        await self.wait_for_streamlit_ready()

    async def wait_for_streamlit_ready(self):
        """Wait for Streamlit app to fully load.

        Streamlit shows a loading indicator during initialization.
        """
        # Wait for Streamlit's loading overlay to disappear
        try:
            loading_indicator = self.page.locator('[data-testid="stStatusWidget"]')
            await loading_indicator.wait_for(state="hidden", timeout=10000)
        except:
            # If no loading indicator, app is ready
            pass

        # Give Streamlit a moment to stabilize
        await asyncio.sleep(0.5)

    async def wait_for_rerun(self, timeout: int = 5000):
        """Wait for Streamlit rerun to complete.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        # Wait for running indicator to appear and disappear
        try:
            running = self.page.locator('[data-testid="stStatusWidget"]')
            await running.wait_for(state="visible", timeout=1000)
            await running.wait_for(state="hidden", timeout=timeout)
        except:
            pass

        await asyncio.sleep(0.3)  # Stabilization delay

    async def fill_text_input(self, label: str, value: str):
        """Fill text input by label.

        Args:
            label: Input label text
            value: Value to enter
        """
        input_locator = self.page.get_by_label(label)
        await input_locator.fill(value)
        await input_locator.press("Enter")
        await self.wait_for_rerun()

    async def click_button(self, text: str):
        """Click button by text.

        Args:
            text: Button text
        """
        button = self.page.get_by_role("button", name=text)
        await button.click()
        await self.wait_for_rerun()

    async def select_option(self, label: str, option: str):
        """Select option from selectbox.

        Args:
            label: Selectbox label
            option: Option to select
        """
        selectbox = self.page.get_by_label(label)
        await selectbox.click()

        option_locator = self.page.get_by_text(option, exact=True)
        await option_locator.click()

        await self.wait_for_rerun()

    async def get_markdown_content(self) -> str:
        """Get all markdown content from page.

        Returns:
            str: Combined markdown text
        """
        markdown_elements = self.page.locator('[data-testid="stMarkdown"]')
        count = await markdown_elements.count()

        texts = []
        for i in range(count):
            text = await markdown_elements.nth(i).inner_text()
            texts.append(text)

        return "\n".join(texts)

    async def screenshot(self, name: str):
        """Take screenshot for debugging.

        Args:
            name: Screenshot filename
        """
        await self.page.screenshot(path=f"screenshots/{name}.png")

    async def assert_text_visible(self, text: str):
        """Assert text is visible on page.

        Args:
            text: Text to find
        """
        locator = self.page.get_by_text(text)
        await expect(locator).to_be_visible()

    async def assert_text_not_visible(self, text: str):
        """Assert text is not visible on page.

        Args:
            text: Text that should not be present
        """
        locator = self.page.get_by_text(text)
        await expect(locator).not_to_be_visible()
```

### Step 3: Implement Core Workflow Tests (2-3 hours)

**Pattern: First Run Experience Test**:
```python
"""E2E tests for first run experience."""
import pytest
from playwright.async_api import Page, expect
from tests.e2e.base import StreamlitTestBase


@pytest.mark.e2e
@pytest.mark.asyncio
class TestFirstRunExperience(StreamlitTestBase):
    """Test first-time user experience."""

    async def test_welcome_screen_displays(self):
        """Test that welcome screen shows on first run."""
        # Should show welcome message
        await self.assert_text_visible("Welcome to Infinite Backrooms")

        # Should show setup instructions
        await self.assert_text_visible("Configure Your AI Personas")

    async def test_ollama_connection_check(self):
        """Test Ollama connection validation."""
        # Click connection check button
        await self.click_button("Check Ollama Connection")

        # Should show connection status
        connection_status = self.page.get_by_text("Connected to Ollama")
        await expect(connection_status).to_be_visible(timeout=10000)

        # Should display available models
        await self.assert_text_visible("Available Models:")

    async def test_persona_creation(self):
        """Test creating new AI persona."""
        # Fill persona details
        await self.fill_text_input("Persona Name", "TestBot")
        await self.fill_text_input("System Prompt", "You are a helpful test assistant")
        await self.select_option("Model", "llama2")

        # Create persona
        await self.click_button("Create Persona")

        # Should show success message
        await self.assert_text_visible("Persona created successfully")

        # Persona should appear in list
        await self.assert_text_visible("TestBot")
```

**Pattern: Conversation Flow Test**:
```python
"""E2E tests for conversation workflows."""
import pytest
from playwright.async_api import Page, expect
from tests.e2e.base import StreamlitTestBase


@pytest.mark.e2e
@pytest.mark.asyncio
class TestConversationFlow(StreamlitTestBase):
    """Test conversation execution workflows."""

    async def test_start_conversation(self):
        """Test starting a new conversation."""
        # Navigate to conversation page
        await self.click_button("Start Conversation")

        # Should show conversation interface
        await self.assert_text_visible("Conversation in Progress")

        # Should have message input
        message_input = self.page.get_by_label("Your message")
        await expect(message_input).to_be_visible()

    async def test_send_message_and_receive_response(self):
        """Test sending message and receiving AI response."""
        # Send message
        await self.fill_text_input("Your message", "Hello, AI!")

        # Should show user message
        await self.assert_text_visible("You: Hello, AI!")

        # Should receive AI response (with timeout for generation)
        ai_response = self.page.locator('[data-testid="stMarkdown"]').filter(
            has_text="TestBot:"
        )
        await expect(ai_response).to_be_visible(timeout=30000)

    async def test_multi_turn_conversation(self):
        """Test multi-turn conversation flow."""
        messages = [
            "What is Python?",
            "Tell me more about functions",
            "Give me an example"
        ]

        for msg in messages:
            await self.fill_text_input("Your message", msg)
            await self.wait_for_rerun()

            # Verify message appears
            await self.assert_text_visible(f"You: {msg}")

        # Should have all messages in history
        markdown = await self.get_markdown_content()
        assert all(msg in markdown for msg in messages)

    async def test_thinking_mode_toggle(self):
        """Test enabling/disabling thinking mode."""
        # Enable thinking mode
        thinking_toggle = self.page.get_by_label("Enable Thinking Mode")
        await thinking_toggle.check()
        await self.wait_for_rerun()

        # Send message
        await self.fill_text_input("Your message", "Solve 2+2")

        # Should show thinking content
        await self.assert_text_visible("<think>")

        # Disable thinking mode
        await thinking_toggle.uncheck()
        await self.wait_for_rerun()

        # Send another message
        await self.fill_text_input("Your message", "What is 3+3?")

        # Should not show thinking content
        markdown = await self.get_markdown_content()
        assert "<think>" not in markdown

    async def test_stop_conversation(self):
        """Test stopping conversation mid-generation."""
        # Start long-running generation
        await self.fill_text_input(
            "Your message",
            "Write a very long essay about artificial intelligence"
        )

        # Click stop button while generating
        await asyncio.sleep(2)  # Let generation start
        await self.click_button("Stop Generation")

        # Should show stopped message
        await self.assert_text_visible("Generation stopped")
```

**Pattern: Error Handling Test**:
```python
"""E2E tests for error handling."""
import pytest
from playwright.async_api import Page, expect
from tests.e2e.base import StreamlitTestBase


@pytest.mark.e2e
@pytest.mark.asyncio
class TestErrorHandling(StreamlitTestBase):
    """Test application error handling."""

    async def test_ollama_connection_failure(self):
        """Test handling Ollama connection failure."""
        # Mock Ollama being down (requires test mode or mock server)
        # Click connection check
        await self.click_button("Check Ollama Connection")

        # Should show error message
        error_msg = self.page.get_by_text("Failed to connect to Ollama")
        await expect(error_msg).to_be_visible()

        # Should show helpful instructions
        await self.assert_text_visible("Please ensure Ollama is running")

    async def test_invalid_input_validation(self):
        """Test input validation and error messages."""
        # Try to create persona with empty name
        await self.fill_text_input("Persona Name", "")
        await self.click_button("Create Persona")

        # Should show validation error
        await self.assert_text_visible("Persona name is required")

    async def test_timeout_handling(self):
        """Test timeout handling for long requests."""
        # Configure very short timeout (test mode)
        # Send message that would timeout
        await self.fill_text_input(
            "Your message",
            "Generate an extremely long response"
        )

        # Should show timeout error after configured timeout
        timeout_msg = self.page.get_by_text("Request timed out")
        await expect(timeout_msg).to_be_visible(timeout=35000)

    async def test_recovery_after_error(self):
        """Test that app recovers gracefully after errors."""
        # Trigger error
        await self.click_button("Trigger Test Error")

        # Should show error
        await self.assert_text_visible("An error occurred")

        # Should be able to continue using app
        await self.click_button("Dismiss Error")
        await self.fill_text_input("Your message", "Testing recovery")

        # Should work normally
        await self.assert_text_visible("You: Testing recovery")
```

### Step 4: Add Performance Testing (45-60 min)

**Pattern: Performance Metrics**:
```python
"""E2E performance tests."""
import pytest
import time
from playwright.async_api import Page
from tests.e2e.base import StreamlitTestBase


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
class TestPerformance(StreamlitTestBase):
    """Test application performance characteristics."""

    async def test_initial_load_time(self):
        """Test initial page load performance."""
        start_time = time.time()

        await self.page.goto(self.BASE_URL)
        await self.wait_for_streamlit_ready()

        load_time = time.time() - start_time

        # Should load in under 5 seconds
        assert load_time < 5.0, f"Page loaded in {load_time:.2f}s, expected < 5s"

    async def test_rerun_performance(self):
        """Test Streamlit rerun performance."""
        # Measure time for simple interaction
        start_time = time.time()

        await self.click_button("Test Button")

        rerun_time = time.time() - start_time

        # Rerun should complete in under 2 seconds
        assert rerun_time < 2.0, f"Rerun took {rerun_time:.2f}s, expected < 2s"

    async def test_message_generation_time(self):
        """Test AI message generation performance."""
        start_time = time.time()

        await self.fill_text_input("Your message", "Hello")

        # Wait for response to complete
        await self.page.wait_for_selector(
            '[data-testid="stMarkdown"]:has-text("TestBot:")',
            timeout=30000
        )

        generation_time = time.time() - start_time

        # Should generate response in under 30 seconds
        assert generation_time < 30.0

    async def test_memory_usage_stability(self):
        """Test memory usage remains stable over multiple interactions."""
        # Perform many interactions
        for i in range(50):
            await self.fill_text_input("Your message", f"Message {i}")
            await self.wait_for_rerun()

        # Check page is still responsive
        button = self.page.get_by_role("button").first
        await expect(button).to_be_enabled()

        # Memory should be managed (no leaks causing slowdown)
        start_time = time.time()
        await self.click_button("Test Button")
        response_time = time.time() - start_time

        # Should still be fast after many operations
        assert response_time < 3.0
```

### Step 5: Implement Visual Regression Tests (60-90 min)

**Pattern: Screenshot Comparison**:
```python
"""Visual regression tests."""
import pytest
from playwright.async_api import Page, expect
from tests.e2e.base import StreamlitTestBase


@pytest.mark.e2e
@pytest.mark.visual
@pytest.mark.asyncio
class TestVisualRegression(StreamlitTestBase):
    """Visual regression test suite."""

    async def test_homepage_appearance(self):
        """Test homepage visual appearance."""
        # Wait for page to stabilize
        await self.wait_for_streamlit_ready()

        # Take screenshot
        await expect(self.page).to_have_screenshot(
            "homepage.png",
            full_page=True
        )

    async def test_conversation_interface_layout(self):
        """Test conversation interface visual layout."""
        # Navigate to conversation
        await self.click_button("Start Conversation")

        # Send a message to populate interface
        await self.fill_text_input("Your message", "Test")
        await self.wait_for_rerun()

        # Capture conversation layout
        await expect(self.page).to_have_screenshot(
            "conversation-interface.png",
            full_page=True
        )

    async def test_responsive_design_mobile(self):
        """Test mobile responsive design."""
        # Set mobile viewport
        await self.page.set_viewport_size({"width": 375, "height": 667})

        # Should adapt layout
        await expect(self.page).to_have_screenshot(
            "mobile-homepage.png",
            full_page=True
        )

    async def test_responsive_design_tablet(self):
        """Test tablet responsive design."""
        # Set tablet viewport
        await self.page.set_viewport_size({"width": 768, "height": 1024})

        await expect(self.page).to_have_screenshot(
            "tablet-homepage.png",
            full_page=True
        )
```

### Step 6: Setup CI Integration (30-45 min)

**Create E2E Test Script**:
```bash
#!/bin/bash
# scripts/run_e2e_tests.sh

set -e

echo "🚀 Starting E2E test suite..."

# Start Streamlit app in background
echo "📱 Starting Streamlit application..."
streamlit run streamlit_backroom.py --server.port 8501 --server.headless true &
STREAMLIT_PID=$!

# Wait for app to be ready
echo "⏳ Waiting for application to start..."
timeout=30
while ! curl -s http://localhost:8501 > /dev/null; do
    sleep 1
    timeout=$((timeout - 1))
    if [ $timeout -eq 0 ]; then
        echo "❌ Application failed to start"
        kill $STREAMLIT_PID
        exit 1
    fi
done

echo "✅ Application ready"

# Run E2E tests
echo "🧪 Running E2E tests..."
pytest tests/e2e/ -v --headed=false --screenshot=only-on-failure

TEST_RESULT=$?

# Cleanup
echo "🧹 Cleaning up..."
kill $STREAMLIT_PID

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ E2E tests passed"
    exit 0
else
    echo "❌ E2E tests failed"
    exit 1
fi
```

---

## Best Practices

### Test Reliability
1. Always wait for Streamlit reruns to complete
2. Use stable selectors (data-testid, role, label)
3. Add appropriate timeouts for async operations
4. Handle dynamic content gracefully

### Test Maintenance
1. Use page object pattern for complex pages
2. Extract common interactions to base class
3. Keep tests independent and isolated
4. Clean up state between tests

### Performance
1. Run E2E tests separately from unit tests
2. Use headless mode in CI
3. Parallelize tests when possible
4. Mock external services for speed

### Debugging
1. Take screenshots on failure
2. Record videos for complex failures
3. Use headed mode during development
4. Add strategic wait points

---

## Success Criteria

- [ ] E2E tests cover all critical user workflows
- [ ] Tests pass consistently (no flakiness)
- [ ] Visual regression tests establish baselines
- [ ] Performance benchmarks documented
- [ ] CI integration working
- [ ] Screenshots captured on failures
- [ ] Test execution time < 10 minutes
- [ ] Cross-browser testing implemented

---

## Tools Available
- Read: Read application code
- Write: Create test files
- Bash: Run Playwright, start Streamlit
- Grep: Find selectors in code
- Glob: Discover UI components

---

## Validation Commands

```bash
# Install Playwright
pip install playwright pytest-playwright
playwright install

# Run E2E tests (headed mode for development)
pytest tests/e2e/ -v --headed --slowmo=100

# Run E2E tests (headless for CI)
pytest tests/e2e/ -v --headed=false

# Run specific test
pytest tests/e2e/test_conversation.py::TestConversationFlow::test_send_message -v

# Generate test report
pytest tests/e2e/ --html=report.html --self-contained-html

# Update visual regression baselines
pytest tests/e2e/ --update-snapshots

# Run performance tests only
pytest tests/e2e/ -m slow -v

# Run with coverage
pytest tests/e2e/ --cov=src --cov-report=html
```
