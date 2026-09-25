import json
import subprocess
import unittest

import reply


class ReplyReceiptTests(unittest.TestCase):
    def setUp(self):
        reply._attempted_replies.clear()
        self.channel = sorted(reply.ALLOWED_CHANNELS)[0]
        self.target = "a" * 64
        self.env = {
            "BUZZ_GIT_ORIGIN_CHANNEL_ID": self.channel,
            "BUZZ_PRIVATE_KEY": "test-key",
            "BUZZ_RELAY_URL": "https://relay.example.invalid",
            "UNRELATED_SECRET": "must-not-be-passed",
        }

    def send(self, stdout, *, returncode=0, stderr="", target=None, runner=None):
        if runner is None:
            def runner(args, **kwargs):
                return subprocess.CompletedProcess(args, returncode, stdout, stderr)
        return reply.send_reply(
            self.channel, self.target if target is None else target,
            "literal message\n", env=self.env, runner=runner,
        )

    def test_00_rejected_receipt_with_zero_exit_is_not_success(self):
        receipt = json.dumps({"accepted": False, "event_id": "b" * 64})
        with self.assertRaises(RuntimeError):
            self.send(receipt)
        with self.assertRaises(RuntimeError):
            self.send(json.dumps({"accepted": True, "event_id": "b" * 64}))

    def test_valid_receipt_allows_extra_fields_and_surrounding_whitespace(self):
        receipt = ' \n' + json.dumps({
            "accepted": True, "event_id": "b" * 64, "metadata": {"extra": True},
        }) + '\t'
        self.assertEqual(self.send(receipt), "Reply sent to Buzz.")
        with self.assertRaises(RuntimeError):
            self.send(receipt)

    def test_invalid_receipts_are_rejected(self):
        valid = {"accepted": True, "event_id": "b" * 64}
        invalid = [
            "", "   ", "not json", "{", "null", "[]",
            json.dumps([valid]),
            json.dumps({"event_id": "b" * 64}),
            json.dumps({"accepted": False, "event_id": "b" * 64}),
            json.dumps({"accepted": 1, "event_id": "b" * 64}),
            json.dumps({"accepted": "true", "event_id": "b" * 64}),
            json.dumps({"accepted": True}),
            json.dumps({"accepted": True, "event_id": None}),
            json.dumps({"accepted": True, "event_id": 123}),
            json.dumps({"accepted": True, "event_id": "B" * 64}),
            json.dumps({"accepted": True, "event_id": "b" * 63}),
            json.dumps({"accepted": True, "event_id": "b" * 65}),
            json.dumps({"accepted": True, "event_id": "g" * 64}),
            json.dumps(valid) + json.dumps(valid),
            json.dumps(valid) + " trailing junk",
        ]
        for index, stdout in enumerate(invalid):
            with self.subTest(index=index, stdout=stdout):
                with self.assertRaises(RuntimeError):
                    self.send(stdout, target=f"{index:064x}")

    def test_nonzero_exit_rejects_even_a_valid_receipt_without_leaking_output(self):
        receipt = json.dumps({
            "accepted": True, "event_id": "b" * 64,
            "detail": "PRIVATE_STDOUT_MARKER",
        })
        with self.assertRaises(RuntimeError) as caught:
            self.send(receipt, returncode=1, stderr="PRIVATE_STDERR_MARKER")
        self.assertNotIn("PRIVATE_STDOUT_MARKER", str(caught.exception))
        self.assertNotIn("PRIVATE_STDERR_MARKER", str(caught.exception))
        with self.assertRaises(RuntimeError):
            self.send(receipt)

    def test_invalid_receipt_does_not_block_unrelated_event(self):
        with self.assertRaises(RuntimeError):
            self.send(json.dumps({"accepted": False, "event_id": "b" * 64}))
        self.assertEqual(
            self.send(json.dumps({"accepted": True, "event_id": "c" * 64}), target="d" * 64),
            "Reply sent to Buzz.",
        )

    def test_timeout_blocks_target_without_retry(self):
        calls = []

        def timeout_runner(args, **kwargs):
            calls.append(args)
            raise subprocess.TimeoutExpired(args, 30)

        with self.assertRaises(RuntimeError):
            self.send("", runner=timeout_runner)
        with self.assertRaises(RuntimeError):
            self.send("", runner=timeout_runner)
        self.assertEqual(len(calls), 1)

    def test_fixed_command_literal_stdin_and_minimal_environment(self):
        calls = []

        def runner(args, **kwargs):
            calls.append((args, kwargs))
            return subprocess.CompletedProcess(
                args, 0, json.dumps({"accepted": True, "event_id": "b" * 64}), "",
            )

        self.assertEqual(self.send("", runner=runner), "Reply sent to Buzz.")
        args, kwargs = calls[0]
        self.assertEqual(args, [
            reply.BUZZ_CLI, "messages", "send", "--channel", self.channel,
            "--content", "-", "--reply-to", self.target,
        ])
        self.assertEqual(kwargs["input"], "literal message\n")
        self.assertIs(kwargs["shell"], False)
        self.assertIs(kwargs["text"], True)
        self.assertIs(kwargs["capture_output"], True)
        self.assertIs(kwargs["check"], False)
        self.assertEqual(kwargs["timeout"], 30)
        self.assertEqual(kwargs["cwd"], "/benchmark")
        self.assertEqual(set(kwargs["env"]), {
            "HOME", "PATH", "BUZZ_PRIVATE_KEY", "BUZZ_RELAY_URL",
        })
        self.assertEqual(kwargs["env"]["BUZZ_PRIVATE_KEY"], "test-key")

    def test_invalid_channel_or_content_never_invokes_runner(self):
        def forbidden_runner(*args, **kwargs):
            self.fail("sender must not run")

        with self.assertRaises(ValueError):
            reply.send_reply(
                "test-channel-02"
                if self.channel != "test-channel-02"
                else "test-channel-01",
                self.target, "message", env=self.env, runner=forbidden_runner,
            )
        with self.assertRaises(ValueError):
            reply.send_reply(
                self.channel, self.target, "   ", env=self.env, runner=forbidden_runner,
            )


if __name__ == "__main__":
    unittest.main()
