"""Follow-up suite; never included in the frozen 26/30-check scores."""
import subprocess
import unittest
from unittest.mock import Mock
import reply


class DeepJSON(unittest.TestCase):
    def test_deep_json_is_sanitized_and_attempt_stays_blocked(self):
        reply._attempted_replies.clear()
        channel = sorted(reply.ALLOWED_CHANNELS)[0]
        env = {'BUZZ_PRIVATE_KEY': 'fixture-only', 'BUZZ_RELAY_URL': 'wss://example.invalid',
               'BUZZ_GIT_ORIGIN_CHANNEL_ID': channel}
        runner = Mock(return_value=subprocess.CompletedProcess([], 0, stdout='[' * 10000 + ']' * 10000))
        with self.assertRaises(RuntimeError) as caught:
            reply.send_reply(channel, 'd' * 64, 'fixture', env=env, runner=runner)
        # RecursionError subclasses RuntimeError; assert the exact public exception.
        self.assertIs(type(caught.exception), RuntimeError)
        self.assertIn('not confirmed', str(caught.exception))
        self.assertNotIn('JSON', str(caught.exception))
        with self.assertRaises(RuntimeError):
            reply.send_reply(channel, 'd' * 64, 'fixture', env=env, runner=runner)
        self.assertEqual(runner.call_count, 1)
