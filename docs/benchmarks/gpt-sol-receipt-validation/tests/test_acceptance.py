import json
import subprocess
import unittest
from unittest.mock import Mock
import reply

CHANNEL = sorted(reply.ALLOWED_CHANNELS)[0]
EVENT = 'a' * 64
ENV = {'BUZZ_PRIVATE_KEY': 'fixture-not-a-real-key', 'BUZZ_RELAY_URL': 'wss://example.invalid', 'BUZZ_GIT_ORIGIN_CHANNEL_ID': CHANNEL}
VALID = json.dumps({'accepted': True, 'event_id': 'b' * 64, 'message': 'ok'})

class Acceptance(unittest.TestCase):
    def setUp(self):
        reply._attempted_replies.clear()

    def send(self, stdout=VALID, code=0, **kw):
        runner = Mock(return_value=subprocess.CompletedProcess([], code, stdout=stdout, stderr='PRIVATE-STDERR'))
        value = reply.send_reply(CHANNEL, EVENT, 'literal $(do not execute)\n  text  ', env=ENV, runner=runner, **kw)
        return value, runner

    def test_valid_receipt_and_literal_payload(self):
        value, runner = self.send()
        self.assertEqual(value, 'Reply sent to Buzz.')
        args, kw = runner.call_args
        self.assertIs(kw['shell'], False)
        self.assertEqual(kw['input'], 'literal $(do not execute)\n  text  ')
        self.assertEqual(args[0], [reply.BUZZ_CLI, 'messages', 'send', '--channel', CHANNEL, '--content', '-', '--reply-to', EVENT])
        self.assertEqual(set(kw['env']), {'HOME', 'PATH', 'BUZZ_PRIVATE_KEY', 'BUZZ_RELAY_URL'})
        self.assertEqual(kw['timeout'], 30)

    def test_success_blocks_duplicate(self):
        _, runner = self.send()
        with self.assertRaises(RuntimeError):
            reply.send_reply(CHANNEL, EVENT, 'again', env=ENV, runner=runner)
        self.assertEqual(runner.call_count, 1)

    def test_nonzero_even_with_valid_receipt(self):
        with self.assertRaises(RuntimeError) as cm:
            self.send(code=1)
        self.assertNotIn('PRIVATE', str(cm.exception))

    def test_timeout_blocks_duplicate(self):
        runner = Mock(side_effect=subprocess.TimeoutExpired('fake', 30, output='PRIVATE-STDOUT'))
        for _ in range(2):
            with self.assertRaises(RuntimeError) as cm:
                reply.send_reply(CHANNEL, EVENT, 'text', env=ENV, runner=runner)
            self.assertNotIn('PRIVATE', str(cm.exception))
        self.assertEqual(runner.call_count, 1)

    def test_oserror_blocks_duplicate(self):
        runner = Mock(side_effect=OSError('PRIVATE-STDERR'))
        for _ in range(2):
            with self.assertRaises(RuntimeError) as cm:
                reply.send_reply(CHANNEL, EVENT, 'text', env=ENV, runner=runner)
            self.assertNotIn('PRIVATE', str(cm.exception))
        self.assertEqual(runner.call_count, 1)

    def test_cross_channel_never_runs(self):
        runner = Mock()
        with self.assertRaises(ValueError):
            reply.send_reply(sorted(reply.ALLOWED_CHANNELS)[1], EVENT, 'text', env=ENV, runner=runner)
        runner.assert_not_called()

    def test_missing_trust_never_runs(self):
        runner = Mock()
        with self.assertRaises(ValueError):
            reply.send_reply(CHANNEL, EVENT, 'text', env={}, runner=runner)
        runner.assert_not_called()

    def test_malformed_target_never_runs(self):
        runner = Mock()
        with self.assertRaises(ValueError):
            reply.send_reply(CHANNEL, 'A'*64, 'text', env=ENV, runner=runner)
        runner.assert_not_called()

    def test_content_validation_preserved(self):
        for content in ['', '  ', 'x'*4001, None]:
            with self.subTest(content_type=type(content).__name__):
                with self.assertRaises(ValueError):
                    reply.send_reply(CHANNEL, EVENT, content, env=ENV, runner=Mock())

    def test_unrelated_event_still_sends_after_failure(self):
        runner=Mock(side_effect=[subprocess.CompletedProcess([],0,stdout='{}'), subprocess.CompletedProcess([],0,stdout=VALID)])
        with self.assertRaises(RuntimeError):
            reply.send_reply(CHANNEL, EVENT, 'first', env=ENV, runner=runner)
        self.assertEqual(reply.send_reply(CHANNEL,'c'*64,'second',env=ENV,runner=runner),'Reply sent to Buzz.')

BAD = {
    'empty':'', 'whitespace':'  ', 'garbage':'PRIVATE-STDOUT', 'null':'null',
    'list':'[]', 'string':'"PRIVATE-STDOUT"', 'missing_accepted':json.dumps({'event_id':'b'*64}),
    'false':json.dumps({'accepted':False,'event_id':'b'*64}),
    'integer':json.dumps({'accepted':1,'event_id':'b'*64}),
    'truthy_string':json.dumps({'accepted':'true','event_id':'b'*64}),
    'missing_event':json.dumps({'accepted':True}),
    'upper_event':json.dumps({'accepted':True,'event_id':'B'*64}),
    'short_event':json.dumps({'accepted':True,'event_id':'b'*63}),
    'event_type':json.dumps({'accepted':True,'event_id':123}),
    'two_objects':VALID+'\n'+VALID, 'trailing_junk':VALID+' PRIVATE-STDOUT',
}
def bad_test(stdout):
    def test(self):
        runner=Mock(return_value=subprocess.CompletedProcess([],0,stdout=stdout,stderr='PRIVATE-STDERR'))
        for _ in range(2):
            with self.assertRaises(RuntimeError) as cm:
                reply.send_reply(CHANNEL,EVENT,'text',env=ENV,runner=runner)
            self.assertNotIn('PRIVATE',str(cm.exception))
        self.assertEqual(runner.call_count,1)
    return test
for name, stdout in BAD.items():
    setattr(Acceptance,'test_bad_receipt_'+name,bad_test(stdout))

if __name__ == '__main__':
    unittest.main(verbosity=2)
