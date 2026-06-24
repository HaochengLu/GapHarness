from __future__ import annotations

import os
import tempfile
import unittest

from gapharness.llm_client import ChatMessage, LLMClientError, OpenAICompatibleClient


def _fake_response(content: str = '{"ok": true}', model: str = "test-model"):
    return {
        "model": model,
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 5},
    }


class _CountingClient(OpenAICompatibleClient):
    """Client that records _post calls and never touches the network."""

    def __init__(self, *args, response=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.post_calls = 0
        self._response = response or _fake_response()

    def _post(self, path, payload):  # type: ignore[override]
        self.post_calls += 1
        return self._response


class LLMClientCacheTests(unittest.TestCase):
    def _messages(self):
        return [
            ChatMessage(role="system", content="You are a profiler."),
            ChatMessage(role="user", content="Classify this request."),
        ]

    def test_default_behavior_unchanged_no_cache_dir(self):
        client = _CountingClient(api_key="test-key", base_url="https://example.test", model="m")
        self.assertIsNone(client.cache_dir)
        resp = client.chat_json(self._messages())
        self.assertEqual(resp.content, '{"ok": true}')
        # No cache means every call hits _post.
        client.chat_json(self._messages())
        self.assertEqual(client.post_calls, 2)

    def test_cache_writes_then_replays_without_network(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            client = _CountingClient(
                api_key="test-key",
                base_url="https://example.test",
                model="m",
                cache_dir=cache_dir,
            )
            first = client.chat_json(self._messages())
            self.assertEqual(client.post_calls, 1)
            # One cache file should now exist.
            entries = [f for f in os.listdir(cache_dir) if f.endswith(".json")]
            self.assertEqual(len(entries), 1)

            # Second identical call is served from cache; _post not called again.
            second = client.chat_json(self._messages())
            self.assertEqual(client.post_calls, 1)
            self.assertEqual(first.content, second.content)
            self.assertEqual(first.raw, second.raw)

    def test_replay_with_fresh_client_and_no_api_key(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            writer = _CountingClient(
                api_key="test-key",
                base_url="https://example.test",
                model="m",
                cache_dir=cache_dir,
            )
            writer.chat_json(self._messages())

            # A new client with NO api key can replay purely from disk.
            replayer = _CountingClient(
                api_key=None,
                base_url="https://example.test",
                model="m",
                cache_dir=cache_dir,
            )
            self.assertIsNone(replayer.api_key)
            resp = replayer.chat_json(self._messages())
            self.assertEqual(resp.content, '{"ok": true}')
            self.assertEqual(replayer.post_calls, 0)

    def test_cache_miss_without_api_key_raises(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            client = _CountingClient(
                api_key=None,
                base_url="https://example.test",
                model="m",
                cache_dir=cache_dir,
            )
            with self.assertRaises(LLMClientError):
                client.chat_json(self._messages())
            self.assertEqual(client.post_calls, 0)

    def test_distinct_requests_get_distinct_cache_entries(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            client = _CountingClient(
                api_key="test-key",
                base_url="https://example.test",
                model="m",
                cache_dir=cache_dir,
            )
            client.chat_json(self._messages())
            # Different temperature -> different key -> new network call.
            client.chat_json(self._messages(), temperature=0.7)
            self.assertEqual(client.post_calls, 2)
            entries = [f for f in os.listdir(cache_dir) if f.endswith(".json")]
            self.assertEqual(len(entries), 2)

    def test_cache_key_is_stable_and_model_sensitive(self):
        client = _CountingClient(
            api_key="test-key", base_url="https://example.test", model="m"
        )
        payload_a = {"model": "m", "messages": [{"role": "user", "content": "hi"}]}
        payload_a_again = {"messages": [{"role": "user", "content": "hi"}], "model": "m"}
        payload_b = {"model": "other", "messages": [{"role": "user", "content": "hi"}]}
        self.assertEqual(client.cache_key(payload_a), client.cache_key(payload_a_again))
        self.assertNotEqual(client.cache_key(payload_a), client.cache_key(payload_b))

    def test_env_var_enables_cache(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            prev = os.environ.get("GAPHARNESS_CACHE_DIR")
            os.environ["GAPHARNESS_CACHE_DIR"] = cache_dir
            try:
                client = _CountingClient(
                    api_key="test-key", base_url="https://example.test", model="m"
                )
                self.assertEqual(client.cache_dir, cache_dir)
                client.chat_json(self._messages())
                client.chat_json(self._messages())
                self.assertEqual(client.post_calls, 1)
            finally:
                if prev is None:
                    os.environ.pop("GAPHARNESS_CACHE_DIR", None)
                else:
                    os.environ["GAPHARNESS_CACHE_DIR"] = prev


if __name__ == "__main__":
    unittest.main()
