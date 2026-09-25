import json
import subprocess
import traceback
import unittest
from types import SimpleNamespace

import reply


class SendReplyReceiptTests(unittest.TestCase):
    def setUp(self):
        with reply._attempt_lock:
            reply._attempted_replies.clear()
        self.channel = sorted(reply.ALLOWED_CHANNELS)[0]
        self.target = 'a' * 64
        self.event_id = '0123456789abcdef' * 4
        self.secret = 'PRIVATE_OUTPUT_SENTINEL_DO_NOT_DISCLOSE'
        self.content = '  Literal $(touch forbidden); `echo forbidden`\nSecond line.  '
        self.env = {
            'BUZZ_GIT_ORIGIN_CHANNEL_ID': self.channel,
            'BUZZ_PRIVATE_KEY': 'test-private-key',
            'BUZZ_RELAY_URL': 'wss://invalid.example',
            'BUZZ_AUTH_TAG': 'test-auth-tag',
            'UNRELATED_SECRET': 'must-not-be-forwarded',
            'HOME': '/untrusted/home',
            'PATH': '/untrusted/bin',
        }
        self.calls = []

    def receipt(self, **updates):
        value = {'accepted': True, 'event_id': self.event_id}
        value.update(updates)
        return json.dumps(value)

    def runner_for(self, stdout, returncode=0, error=None):
        def runner(argv, **kwargs):
            self.calls.append((argv, kwargs))
            if error is not None:
                raise error
            return SimpleNamespace(
                returncode=returncode, stdout=stdout, stderr=self.secret
            )
        return runner

    def send(self, runner, target=None):
        return reply.send_reply(
            self.channel,
            self.target if target is None else target,
            self.content,
            env=self.env,
            runner=runner,
        )

    def assert_safe_failure(self, runner, target=None):
        with self.assertRaises(RuntimeError) as caught:
            self.send(runner, target)
        error = caught.exception
        self.assertTrue(str(error).strip())
        self.assertNotIn(self.secret, str(error))
        rendered = ''.join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        self.assertNotIn(self.secret, rendered)
        return error

    def test_00_exit_zero_with_rejected_receipt_is_not_confirmation(self):
        runner = self.runner_for(
            self.receipt(accepted=False, diagnostic=self.secret)
        )
        self.assert_safe_failure(runner)
        self.assertEqual(len(self.calls), 1)
        self.assertIn(self.target, reply._attempted_replies)

    def test_invalid_receipts_are_rejected_even_with_exit_zero(self):
        invalid = [
            ('empty', ''),
            ('whitespace', ' \t\r\n'),
            ('malformed', '{' + self.secret),
            ('null', 'null'),
            ('array', '[' + self.receipt() + ']'),
            ('string', json.dumps(self.secret)),
            ('number', '42'),
            ('boolean', 'true'),
            ('missing both fields', '{}'),
            ('missing accepted', json.dumps({'event_id': self.event_id})),
            ('missing event_id', '{"accepted": true}'),
            ('two objects', self.receipt() + '\n' + self.receipt()),
            ('trailing junk', self.receipt() + self.secret),
            ('trailing scalar', self.receipt() + ' null'),
            ('leading junk', self.secret + self.receipt()),
            ('non-JSON whitespace', '\u00a0' + self.receipt()),
            ('NaN extension', self.receipt(extra=float('nan'))),
            ('Infinity extension', self.receipt(extra=float('inf'))),
            ('negative Infinity extension', self.receipt(extra=float('-inf'))),
        ]
        for accepted in (False, None, 0, 1, 1.0, 'true', 'false', [], {}, [True], {'ok': True}):
            invalid.append((f'accepted={accepted!r}', self.receipt(accepted=accepted)))
        for event_id in (
            None, True, 123, [], {}, '', 'a' * 63, 'a' * 65,
            'A' * 64, 'g' * 64, '0x' + 'a' * 62,
            ' ' + self.event_id, self.event_id + ' ',
            self.event_id + '\n', 'a' * 31 + '\n' + 'a' * 32,
            '\uff41' * 64,
        ):
            invalid.append((f'event_id={event_id!r}', self.receipt(event_id=event_id)))
        for index, (label, stdout) in enumerate(invalid):
            with self.subTest(label=label):
                target = f'{index:064x}'
                previous_calls = len(self.calls)
                self.assert_safe_failure(self.runner_for(stdout), target)
                self.assertEqual(len(self.calls), previous_calls + 1)
                self.assertIn(target, reply._attempted_replies)
                self.assert_safe_failure(self.runner_for(self.receipt()), target)
                self.assertEqual(len(self.calls), previous_calls + 1)

    def test_valid_receipts_allow_extra_fields_and_json_whitespace(self):
        receipts = [
            self.receipt(),
            ' \t\r\n' + self.receipt(
                extra={'list': [1, None, False, 'text'], 'nested': {}},
                diagnostic=self.secret,
            ) + '\n\r\t ',
            '{"event_id": "' + self.event_id + '", "accepted": true}',
        ]
        for index, stdout in enumerate(receipts):
            with self.subTest(stdout=stdout):
                target = f'{index:064x}'
                self.assertEqual(
                    self.send(self.runner_for(stdout), target),
                    'Reply sent to Buzz.',
                )
                self.assertIn(target, reply._attempted_replies)

    def test_nonzero_exits_reject_even_valid_receipts(self):
        for index, returncode in enumerate((1, 2, 127, 255, -9, -15)):
            with self.subTest(returncode=returncode):
                target = f'{index:064x}'
                self.assert_safe_failure(
                    self.runner_for(self.receipt(diagnostic=self.secret), returncode),
                    target,
                )
                self.assertIn(target, reply._attempted_replies)

    def test_attempt_guard_survives_every_outcome_without_blocking_other_events(self):
        outcomes = [
            ('success', self.receipt(), 0, None, True),
            ('rejection', self.receipt(accepted=False), 0, None, False),
            ('invalid receipt', '{', 0, None, False),
            ('nonzero', self.receipt(), 1, None, False),
            ('timeout', '', 0, subprocess.TimeoutExpired(
                cmd=[self.secret], timeout=30,
                output=self.secret, stderr=self.secret,
            ), False),
            ('start failure', '', 0, OSError(self.secret), False),
        ]
        for index, (label, stdout, code, error, confirmed) in enumerate(outcomes):
            with self.subTest(outcome=label):
                target = f'{index:064x}'
                other_target = f'{index + 100:064x}'
                previous_calls = len(self.calls)
                runner = self.runner_for(stdout, code, error)
                if confirmed:
                    self.assertEqual(self.send(runner, target), 'Reply sent to Buzz.')
                else:
                    self.assert_safe_failure(runner, target)
                self.assertEqual(len(self.calls), previous_calls + 1)
                self.assertIn(target, reply._attempted_replies)
                self.assert_safe_failure(self.runner_for(self.receipt()), target)
                self.assertEqual(len(self.calls), previous_calls + 1)
                self.assertEqual(
                    self.send(self.runner_for(self.receipt()), other_target),
                    'Reply sent to Buzz.',
                )
                self.assertEqual(len(self.calls), previous_calls + 2)

    def test_sender_contract_and_minimal_environment_are_unchanged(self):
        self.assertEqual(
            self.send(self.runner_for(self.receipt())), 'Reply sent to Buzz.'
        )
        self.assertEqual(self.calls, [(
            [reply.BUZZ_CLI, 'messages', 'send', '--channel', self.channel,
             '--content', '-', '--reply-to', self.target],
            {
                'input': self.content,
                'text': True,
                'capture_output': True,
                'timeout': 30,
                'check': False,
                'env': {
                    'HOME': '/benchmark',
                    'PATH': '/benchmark/bin:/usr/local/bin:/usr/bin:/bin',
                    'BUZZ_PRIVATE_KEY': 'test-private-key',
                    'BUZZ_RELAY_URL': 'wss://invalid.example',
                    'BUZZ_AUTH_TAG': 'test-auth-tag',
                },
                'shell': False,
                'cwd': '/benchmark',
            },
        )])

    def test_optional_auth_tag_is_not_required(self):
        del self.env['BUZZ_AUTH_TAG']
        self.assertEqual(self.send(self.runner_for(self.receipt())), 'Reply sent to Buzz.')
        self.assertEqual(
            set(self.calls[0][1]['env']),
            {'HOME', 'PATH', 'BUZZ_PRIVATE_KEY', 'BUZZ_RELAY_URL'},
        )

    def test_validation_still_precedes_runner_and_attempt_guard(self):
        other_channel = sorted(reply.ALLOWED_CHANNELS)[1]
        cases = [
            (other_channel, self.target, 'hello'),
            ('not-a-channel', self.target, 'hello'),
            (self.channel, 'A' * 64, 'hello'),
            (self.channel, self.target + '\n', 'hello'),
            (self.channel, self.target, ''),
            (self.channel, self.target, ' \t\n'),
            (self.channel, self.target, None),
            (self.channel, self.target, 'x' * (reply.MAX_CONTENT_CHARS + 1)),
        ]
        for channel, target, content in cases:
            with self.subTest(channel=channel, target=target, content=content):
                with self.assertRaises(ValueError):
                    reply.send_reply(
                        channel, target, content, env=self.env,
                        runner=self.runner_for(self.receipt()),
                    )
                self.assertEqual(self.calls, [])
                self.assertEqual(reply._attempted_replies, set())
        self.assertEqual(self.send(self.runner_for(self.receipt())), 'Reply sent to Buzz.')

    def test_missing_trusted_channel_prevents_invocation(self):
        del self.env['BUZZ_GIT_ORIGIN_CHANNEL_ID']
        with self.assertRaises(ValueError):
            self.send(self.runner_for(self.receipt()))
        self.assertEqual(self.calls, [])
        self.assertEqual(reply._attempted_replies, set())

    def test_missing_credentials_prevent_invocation_without_consuming_target(self):
        for key in ('BUZZ_PRIVATE_KEY', 'BUZZ_RELAY_URL'):
            with self.subTest(key=key):
                value = self.env.pop(key)
                try:
                    self.assert_safe_failure(self.runner_for(self.receipt()))
                    self.assertEqual(self.calls, [])
                    self.assertEqual(reply._attempted_replies, set())
                finally:
                    self.env[key] = value
        self.assertEqual(self.send(self.runner_for(self.receipt())), 'Reply sent to Buzz.')


if __name__ == '__main__':
    unittest.main()
