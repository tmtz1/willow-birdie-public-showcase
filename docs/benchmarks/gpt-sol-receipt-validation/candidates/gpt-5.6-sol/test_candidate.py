import subprocess
import unittest
from types import SimpleNamespace

import reply


CHANNEL_ID = "test-channel-01"
REPLY_TO = "a" * 64
EVENT_ID = "b" * 64
BASE_ENV = {
    "BUZZ_GIT_ORIGIN_CHANNEL_ID": CHANNEL_ID,
    "BUZZ_PRIVATE_KEY": "test-private-key",
    "BUZZ_RELAY_URL": "wss://relay.invalid",
}


class RecordingRunner:
    def __init__(self, *, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error is not None:
            raise self.error
        return self.result


def completed(stdout, *, stderr="", returncode=0):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


class SendReplyReceiptTests(unittest.TestCase):
    def setUp(self):
        reply._attempted_replies.clear()

    def send(self, runner, *, content="hello", env=None):
        return reply.send_reply(
            CHANNEL_ID,
            REPLY_TO,
            content,
            env=BASE_ENV if env is None else env,
            runner=runner,
        )

    def test_01_exit_zero_with_rejected_receipt_is_unconfirmed(self):
        runner = RecordingRunner(
            result=completed(
                '{"accepted": false, "event_id": "' + EVENT_ID + '"}'
            )
        )

        with self.assertRaises(RuntimeError):
            self.send(runner)

        self.assertEqual(len(runner.calls), 1)

    def test_valid_receipt_returns_existing_success_string(self):
        receipt = (
            " \n\t{\"accepted\": true, \"event_id\": \""
            + EVENT_ID
            + "\", \"relay\": \"ignored\", \"sequence\": 7}\r\n "
        )
        runner = RecordingRunner(result=completed(receipt))

        self.assertEqual(self.send(runner), "Reply sent to Buzz.")
        self.assertEqual(len(runner.calls), 1)

    def test_invalid_zero_exit_receipts_are_rejected(self):
        invalid_receipts = {
            "empty": "",
            "whitespace": " \n\t ",
            "malformed": "{",
            "null": "null",
            "array": "[]",
            "string": '"receipt"',
            "number": "17",
            "empty_object": "{}",
            "missing_accepted": '{"event_id": "' + EVENT_ID + '"}',
            "missing_event_id": '{"accepted": true}',
            "accepted_false": (
                '{"accepted": false, "event_id": "' + EVENT_ID + '"}'
            ),
            "accepted_number": (
                '{"accepted": 1, "event_id": "' + EVENT_ID + '"}'
            ),
            "accepted_string": (
                '{"accepted": "true", "event_id": "' + EVENT_ID + '"}'
            ),
            "accepted_null": (
                '{"accepted": null, "event_id": "' + EVENT_ID + '"}'
            ),
            "event_id_number": '{"accepted": true, "event_id": 12}',
            "event_id_null": '{"accepted": true, "event_id": null}',
            "event_id_short": (
                '{"accepted": true, "event_id": "' + ("b" * 63) + '"}'
            ),
            "event_id_long": (
                '{"accepted": true, "event_id": "' + ("b" * 65) + '"}'
            ),
            "event_id_uppercase": (
                '{"accepted": true, "event_id": "' + ("B" * 64) + '"}'
            ),
            "event_id_non_hex": (
                '{"accepted": true, "event_id": "' + ("g" * 64) + '"}'
            ),
            "multiple_objects": (
                '{"accepted": true, "event_id": "'
                + EVENT_ID
                + '"}{"accepted": true, "event_id": "'
                + EVENT_ID
                + '"}'
            ),
            "trailing_junk": (
                '{"accepted": true, "event_id": "' + EVENT_ID + '"} junk'
            ),
            "non_json_constant": (
                '{"accepted": true, "event_id": "'
                + EVENT_ID
                + '", "extra": NaN}'
            ),
        }

        for label, stdout in invalid_receipts.items():
            with self.subTest(label=label):
                reply._attempted_replies.clear()
                runner = RecordingRunner(result=completed(stdout))
                with self.assertRaises(RuntimeError):
                    self.send(runner)
                self.assertEqual(len(runner.calls), 1)

    def test_nonzero_exit_is_rejected_even_with_valid_receipt(self):
        valid_receipt = (
            '{"accepted": true, "event_id": "' + EVENT_ID + '"}'
        )
        for returncode in (1, 2, -9):
            with self.subTest(returncode=returncode):
                reply._attempted_replies.clear()
                runner = RecordingRunner(
                    result=completed(valid_receipt, returncode=returncode)
                )
                with self.assertRaises(RuntimeError):
                    self.send(runner)
                self.assertEqual(len(runner.calls), 1)

    def test_unconfirmed_error_message_never_echoes_stdout_or_stderr(self):
        stdout_secret = "SENSITIVE_STDOUT_7f3841"
        stderr_secret = "SENSITIVE_STDERR_21ad90"
        runner = RecordingRunner(
            result=completed(
                '{"accepted": true, "event_id": "'
                + EVENT_ID
                + '"} '
                + stdout_secret,
                stderr=stderr_secret,
            )
        )

        with self.assertRaises(RuntimeError) as raised:
            self.send(runner)

        message = str(raised.exception)
        self.assertNotIn(stdout_secret, message)
        self.assertNotIn(stderr_secret, message)

    def test_nonzero_error_message_never_echoes_stdout_or_stderr(self):
        stdout_secret = "NONZERO_STDOUT_905ca2"
        stderr_secret = "NONZERO_STDERR_f2c19b"
        runner = RecordingRunner(
            result=completed(
                stdout_secret,
                stderr=stderr_secret,
                returncode=3,
            )
        )

        with self.assertRaises(RuntimeError) as raised:
            self.send(runner)

        message = str(raised.exception)
        self.assertNotIn(stdout_secret, message)
        self.assertNotIn(stderr_secret, message)

    def test_runner_contract_remains_fixed_and_minimal(self):
        content = "  literal --content value\nsecond line  "
        runner = RecordingRunner(
            result=completed(
                '{"accepted": true, "event_id": "' + EVENT_ID + '"}'
            )
        )
        env = {
            **BASE_ENV,
            "UNRELATED_SECRET": "must-not-leak",
        }

        self.assertEqual(
            self.send(runner, content=content, env=env),
            "Reply sent to Buzz.",
        )
        self.assertEqual(len(runner.calls), 1)
        args, kwargs = runner.calls[0]
        self.assertEqual(
            args,
            (
                [
                    reply.BUZZ_CLI,
                    "messages",
                    "send",
                    "--channel",
                    CHANNEL_ID,
                    "--content",
                    "-",
                    "--reply-to",
                    REPLY_TO,
                ],
            ),
        )
        self.assertEqual(kwargs["input"], content)
        self.assertIs(kwargs["text"], True)
        self.assertIs(kwargs["capture_output"], True)
        self.assertEqual(kwargs["timeout"], 30)
        self.assertIs(kwargs["check"], False)
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["cwd"], "/benchmark")
        self.assertEqual(
            kwargs["env"],
            {
                "HOME": "/benchmark",
                "PATH": (
                    "/benchmark/bin:"
                    "/usr/local/bin:/usr/bin:/bin"
                ),
                "BUZZ_PRIVATE_KEY": "test-private-key",
                "BUZZ_RELAY_URL": "wss://relay.invalid",
            },
        )

    def test_target_stays_blocked_after_every_invoked_outcome(self):
        valid_receipt = (
            '{"accepted": true, "event_id": "' + EVENT_ID + '"}'
        )
        cases = {
            "success": (
                RecordingRunner(result=completed(valid_receipt)),
                True,
            ),
            "nonzero": (
                RecordingRunner(
                    result=completed(valid_receipt, returncode=1)
                ),
                False,
            ),
            "invalid_receipt": (
                RecordingRunner(result=completed("not json")),
                False,
            ),
            "timeout": (
                RecordingRunner(
                    error=subprocess.TimeoutExpired(
                        cmd=[reply.BUZZ_CLI],
                        timeout=30,
                        output="TIMEOUT_STDOUT_SECRET",
                        stderr="TIMEOUT_STDERR_SECRET",
                    )
                ),
                False,
            ),
            "startup_failure": (
                RecordingRunner(error=OSError("STARTUP_SECRET")),
                False,
            ),
        }

        for label, (runner, first_succeeds) in cases.items():
            with self.subTest(label=label):
                reply._attempted_replies.clear()
                if first_succeeds:
                    self.assertEqual(
                        self.send(runner),
                        "Reply sent to Buzz.",
                    )
                else:
                    with self.assertRaises(RuntimeError):
                        self.send(runner)

                with self.assertRaises(RuntimeError):
                    self.send(runner)
                self.assertEqual(len(runner.calls), 1)

    def test_unrelated_event_can_send_after_an_attempt(self):
        runner = RecordingRunner(
            result=completed(
                '{"accepted": true, "event_id": "' + EVENT_ID + '"}'
            )
        )
        self.assertEqual(self.send(runner), "Reply sent to Buzz.")

        other_reply_to = "c" * 64
        other_runner = RecordingRunner(
            result=completed(
                '{"accepted": true, "event_id": "' + ("d" * 64) + '"}'
            )
        )
        result = reply.send_reply(
            CHANNEL_ID,
            other_reply_to,
            "another reply",
            env=BASE_ENV,
            runner=other_runner,
        )

        self.assertEqual(result, "Reply sent to Buzz.")
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(len(other_runner.calls), 1)

    def test_validation_failure_does_not_invoke_or_consume_target(self):
        runner = RecordingRunner(
            result=completed(
                '{"accepted": true, "event_id": "' + EVENT_ID + '"}'
            )
        )

        with self.assertRaises(ValueError):
            self.send(runner, content="   \n")
        self.assertEqual(runner.calls, [])

        self.assertEqual(self.send(runner), "Reply sent to Buzz.")
        self.assertEqual(len(runner.calls), 1)


if __name__ == "__main__":
    unittest.main()
