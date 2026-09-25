"""Regression tests: a Buzz reply is confirmed only by a valid JSON receipt."""

import json
import os
import subprocess
import sys
import traceback
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import reply  # noqa: E402

CHANNEL = 'test-channel-01'
OTHER_CHANNEL = 'test-channel-02'
REPLY_TO = 'a' * 64
OTHER_REPLY_TO = 'b' * 64
EVENT_ID = '0123456789abcdef' * 4
PRIVATE_KEY = 'nsec1-test-private-key-must-not-leak'
RELAY_URL = 'wss://relay.invalid'
LEAK = 'LEAKMARKER-7f3a'
SUCCESS = 'Reply sent to Buzz.'
_DEFAULT = object()


def receipt(**fields):
    body = {'accepted': True, 'event_id': EVENT_ID}
    body.update(fields)
    return json.dumps(body)


def make_env(**extra):
    env = {
        'BUZZ_GIT_ORIGIN_CHANNEL_ID': CHANNEL,
        'BUZZ_PRIVATE_KEY': PRIVATE_KEY,
        'BUZZ_RELAY_URL': RELAY_URL,
        'UNRELATED_SECRET': 'not-for-the-child-process',
    }
    env.update(extra)
    return env


class FakeRunner:
    """Injected stand-in for subprocess.run; never starts a real sender."""

    def __init__(self, returncode=0, stdout=_DEFAULT, stderr='diagnostic ' + LEAK, exc=None):
        self.returncode = returncode
        self.stdout = receipt() if stdout is _DEFAULT else stdout
        self.stderr = stderr
        self.exc = exc
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((list(args), dict(kwargs)))
        if self.exc is not None:
            raise self.exc
        return subprocess.CompletedProcess(args, self.returncode, stdout=self.stdout, stderr=self.stderr)


class ReplyTestCase(unittest.TestCase):
    def setUp(self):
        reply._attempted_replies.clear()
        self.addCleanup(reply._attempted_replies.clear)

    def send(self, runner, reply_to=REPLY_TO, content='hello from genie', env=None):
        return reply.send_reply(
            CHANNEL, reply_to, content, env=make_env() if env is None else env, runner=runner
        )

    def assert_safe_error(self, exc):
        rendered = ''.join(traceback.format_exception(exc))
        for secret in (LEAK, PRIVATE_KEY):
            self.assertNotIn(secret, str(exc))
            self.assertNotIn(secret, rendered)

    def assert_unconfirmed(self, runner, reply_to=REPLY_TO):
        with self.assertRaises(RuntimeError) as ctx:
            self.send(runner, reply_to=reply_to)
        self.assertEqual(len(runner.calls), 1)
        self.assertTrue(str(ctx.exception))
        self.assert_safe_error(ctx.exception)
        self.assertIn(reply_to, reply._attempted_replies)
        return ctx.exception

    def assert_all_unconfirmed(self, payloads, returncode=0):
        for payload in payloads:
            with self.subTest(stdout=payload, returncode=returncode):
                reply._attempted_replies.clear()
                self.assert_unconfirmed(FakeRunner(returncode=returncode, stdout=payload))

    def assert_all_confirmed(self, payloads):
        for payload in payloads:
            with self.subTest(stdout=payload):
                reply._attempted_replies.clear()
                runner = FakeRunner(stdout=payload)
                self.assertEqual(self.send(runner), SUCCESS)
                self.assertEqual(len(runner.calls), 1)

    def assert_retry_blocked(self, reply_to=REPLY_TO):
        retry = FakeRunner()
        with self.assertRaises(RuntimeError) as ctx:
            self.send(retry, reply_to=reply_to)
        self.assertEqual(retry.calls, [])
        self.assert_safe_error(ctx.exception)


class ExitZeroRejectedReceiptTests(ReplyTestCase):
    """Written first: exit status 0 alone must not count as a confirmed send."""

    def test_exit_zero_with_rejected_receipt_raises(self):
        runner = FakeRunner(returncode=0, stdout=receipt(accepted=False, reason=LEAK))
        self.assert_unconfirmed(runner)

    def test_exit_zero_rejected_receipt_blocks_retry_of_same_target(self):
        self.assert_unconfirmed(FakeRunner(returncode=0, stdout=receipt(accepted=False)))
        self.assert_retry_blocked()


class ReceiptRejectionTests(ReplyTestCase):
    def test_empty_or_whitespace_stdout_rejected(self):
        self.assert_all_unconfirmed(['', ' ', '\n', ' \t\r\n '])

    def test_missing_stdout_rejected(self):
        self.assert_all_unconfirmed([None])

    def test_malformed_json_rejected(self):
        self.assert_all_unconfirmed([
            receipt()[:-1],
            receipt(note=LEAK)[1:],
            str({'accepted': True, 'event_id': EVENT_ID}),
            'accepted=true event_id=' + EVENT_ID,
            'not json ' + LEAK,
            '{"accepted": True, "event_id": "' + EVENT_ID + '"}',
            '{accepted: true, event_id: "' + EVENT_ID + '"}',
        ])

    def test_non_object_json_rejected(self):
        self.assert_all_unconfirmed([
            'null',
            'true',
            'false',
            '0',
            '1',
            '"' + LEAK + '"',
            '[]',
            json.dumps([{'accepted': True, 'event_id': EVENT_ID}]),
            json.dumps([True, EVENT_ID]),
        ])

    def test_missing_fields_rejected(self):
        self.assert_all_unconfirmed([
            '{}',
            json.dumps({'event_id': EVENT_ID, 'note': LEAK}),
            json.dumps({'accepted': True, 'note': LEAK}),
            json.dumps({'Accepted': True, 'Event_ID': EVENT_ID}),
            json.dumps({'ok': True, 'id': EVENT_ID}),
        ])

    def test_accepted_must_be_exactly_true(self):
        values = [False, None, 0, 1, 1.0, 'true', 'True', 'yes', 'accepted', [True], {'value': True}, [], {}]
        payloads = [receipt(accepted=value, note=LEAK) for value in values]
        payloads.append(receipt()[:-1] + ', "accepted": false}')
        self.assert_all_unconfirmed(payloads)

    def test_event_id_must_be_64_lowercase_hex(self):
        values = [
            None,
            True,
            0,
            12345,
            [EVENT_ID],
            {'id': EVENT_ID},
            '',
            EVENT_ID.upper(),
            EVENT_ID[:32] + EVENT_ID[32:].upper(),
            EVENT_ID[:-1],
            EVENT_ID + '0',
            'a' * 128,
            'g' * 64,
            'z' + EVENT_ID[1:],
            EVENT_ID[:63] + '-',
            '0x' + EVENT_ID[2:],
            ' ' + EVENT_ID,
            EVENT_ID + ' ',
            EVENT_ID + '\n',
            '\n' + EVENT_ID,
            '\u0660' * 64,
            '\uff10' * 64,
            LEAK,
        ]
        self.assert_all_unconfirmed([receipt(event_id=value) for value in values])

    def test_multiple_json_objects_rejected(self):
        self.assert_all_unconfirmed([
            receipt() + receipt(),
            receipt() + '\n' + receipt(),
            receipt() + ' ' + receipt(accepted=False),
            receipt(accepted=False) + '\n' + receipt(),
            receipt() + '\n' + json.dumps({'note': LEAK}),
        ])

    def test_trailing_or_leading_junk_rejected(self):
        self.assert_all_unconfirmed([
            receipt() + 'x',
            receipt() + ' OK',
            receipt() + '\n' + LEAK,
            receipt() + '}',
            receipt() + ',',
            receipt() + '\n[]',
            receipt() + '\x00',
            'OK ' + receipt(),
            LEAK + '\n' + receipt(),
        ])

    def test_nonzero_exit_rejected_even_with_valid_receipt(self):
        for code in (1, 2, 70, 127, 255, -9, -15):
            with self.subTest(returncode=code):
                reply._attempted_replies.clear()
                self.assert_unconfirmed(FakeRunner(returncode=code, stdout=receipt()))

    def test_errors_never_echo_stdout_or_stderr(self):
        cases = [
            FakeRunner(stdout=receipt(accepted=False, detail=LEAK), stderr=LEAK),
            FakeRunner(stdout=LEAK, stderr=LEAK),
            FakeRunner(returncode=1, stdout=LEAK, stderr=LEAK),
            FakeRunner(stdout=receipt(event_id=LEAK)),
            FakeRunner(stdout=receipt() + LEAK),
        ]
        for runner in cases:
            with self.subTest(stdout=runner.stdout):
                reply._attempted_replies.clear()
                self.assert_unconfirmed(runner)


class ReceiptAcceptanceTests(ReplyTestCase):
    def test_valid_receipt_returns_unchanged_success_string(self):
        runner = FakeRunner(stdout=receipt())
        self.assertEqual(self.send(runner), SUCCESS)
        self.assertEqual(len(runner.calls), 1)

    def test_extra_receipt_fields_allowed(self):
        self.assert_all_confirmed([
            receipt(relay='wss://relay.invalid', created_at=1760000000),
            receipt(tags=[['e', REPLY_TO]], meta={'accepted': False}, note=None),
            json.dumps({'event_id': EVENT_ID, 'extra': [1, 2, 3], 'accepted': True}),
        ])

    def test_surrounding_json_whitespace_allowed(self):
        self.assert_all_confirmed([
            receipt() + '\n',
            '\n' + receipt(),
            '  ' + receipt() + '  ',
            '\r\n\t ' + receipt() + ' \t\r\n',
            json.dumps({'accepted': True, 'event_id': EVENT_ID}, indent=2) + '\n',
        ])

    def test_stderr_diagnostics_do_not_block_valid_receipt(self):
        runner = FakeRunner(stdout=receipt(), stderr='warning: relay slow ' + LEAK)
        self.assertEqual(self.send(runner), SUCCESS)


class NoBlindRetryGuardTests(ReplyTestCase):
    def test_blocked_after_success(self):
        self.assertEqual(self.send(FakeRunner()), SUCCESS)
        self.assert_retry_blocked()

    def test_blocked_after_invalid_receipt(self):
        self.assert_unconfirmed(FakeRunner(stdout='{"accepted": true}'))
        self.assert_retry_blocked()

    def test_blocked_after_nonzero_exit(self):
        self.assert_unconfirmed(FakeRunner(returncode=1))
        self.assert_retry_blocked()

    def test_blocked_after_timeout(self):
        exc = subprocess.TimeoutExpired(cmd=[reply.BUZZ_CLI], timeout=30, output=LEAK, stderr=LEAK)
        self.assert_unconfirmed(FakeRunner(exc=exc))
        self.assert_retry_blocked()

    def test_blocked_after_start_failure(self):
        self.assert_unconfirmed(FakeRunner(exc=FileNotFoundError(2, 'No such file', reply.BUZZ_CLI)))
        self.assert_retry_blocked()

    def test_unrelated_event_can_still_send_after_invalid_receipt(self):
        self.assert_unconfirmed(FakeRunner(stdout=receipt(accepted=False)))
        other = FakeRunner()
        self.assertEqual(self.send(other, reply_to=OTHER_REPLY_TO), SUCCESS)
        self.assertEqual(len(other.calls), 1)
        self.assert_retry_blocked(REPLY_TO)


class InvocationContractTests(ReplyTestCase):
    def test_fixed_argv_literal_stdin_and_minimal_environment(self):
        content = '$(touch /tmp/pwn); `id` | cat && echo --reply-to --channel x; rm -rf ~'
        runner = FakeRunner()
        self.assertEqual(self.send(runner, content=content), SUCCESS)
        self.assertEqual(len(runner.calls), 1)
        args, kwargs = runner.calls[0]
        self.assertEqual(
            args,
            [reply.BUZZ_CLI, 'messages', 'send', '--channel', CHANNEL, '--content', '-', '--reply-to', REPLY_TO],
        )
        self.assertEqual(kwargs.get('input'), content)
        self.assertIs(kwargs.get('shell'), False)
        self.assertEqual(kwargs.get('timeout'), 30)
        self.assertIs(kwargs.get('text'), True)
        self.assertIs(kwargs.get('capture_output'), True)
        self.assertIs(kwargs.get('check'), False)
        self.assertEqual(kwargs.get('cwd'), '/benchmark')
        self.assertEqual(
            kwargs.get('env'),
            {
                'HOME': '/benchmark',
                'PATH': '/benchmark/bin:/usr/local/bin:/usr/bin:/bin',
                'BUZZ_PRIVATE_KEY': PRIVATE_KEY,
                'BUZZ_RELAY_URL': RELAY_URL,
            },
        )

    def test_auth_tag_is_only_optional_extra_variable(self):
        runner = FakeRunner()
        self.assertEqual(self.send(runner, env=make_env(BUZZ_AUTH_TAG='tag-123')), SUCCESS)
        child_env = runner.calls[0][1]['env']
        self.assertEqual(
            set(child_env),
            {'HOME', 'PATH', 'BUZZ_PRIVATE_KEY', 'BUZZ_RELAY_URL', 'BUZZ_AUTH_TAG'},
        )
        self.assertEqual(child_env['BUZZ_AUTH_TAG'], 'tag-123')

    def test_channel_must_match_trusted_session_channel(self):
        runner = FakeRunner()
        with self.assertRaises(ValueError):
            reply.send_reply(OTHER_CHANNEL, REPLY_TO, 'hi', env=make_env(), runner=runner)
        self.assertEqual(runner.calls, [])
        self.assertNotIn(REPLY_TO, reply._attempted_replies)

    def test_missing_trusted_channel_refused(self):
        env = make_env()
        del env['BUZZ_GIT_ORIGIN_CHANNEL_ID']
        runner = FakeRunner()
        with self.assertRaises(ValueError):
            self.send(runner, env=env)
        self.assertEqual(runner.calls, [])

    def test_content_validation_preserved(self):
        for content in ('', '   \n', 'x' * (reply.MAX_CONTENT_CHARS + 1), None):
            with self.subTest(content_len=None if content is None else len(content)):
                runner = FakeRunner()
                with self.assertRaises(ValueError):
                    self.send(runner, content=content)
                self.assertEqual(runner.calls, [])
        self.assertEqual(reply._attempted_replies, set())

    def test_max_length_content_sends(self):
        runner = FakeRunner()
        content = 'x' * reply.MAX_CONTENT_CHARS
        self.assertEqual(self.send(runner, content=content), SUCCESS)
        self.assertEqual(runner.calls[0][1]['input'], content)

    def test_invalid_reply_to_refused(self):
        for reply_to in (REPLY_TO.upper(), REPLY_TO[:-1], REPLY_TO + '\n', None):
            with self.subTest(reply_to=reply_to):
                runner = FakeRunner()
                with self.assertRaises(ValueError):
                    self.send(runner, reply_to=reply_to)
                self.assertEqual(runner.calls, [])

    def test_missing_credentials_refused_without_running(self):
        env = make_env()
        del env['BUZZ_PRIVATE_KEY']
        runner = FakeRunner()
        with self.assertRaises(RuntimeError) as ctx:
            self.send(runner, env=env)
        self.assertEqual(runner.calls, [])
        self.assert_safe_error(ctx.exception)


if __name__ == '__main__':
    unittest.main()
