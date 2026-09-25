import json
import os
import subprocess
import sys
import unittest
import reply

class ProcessIntegration(unittest.TestCase):
    def setUp(self):
        reply._attempted_replies.clear()
        self.channel=sorted(reply.ALLOWED_CHANNELS)[0]
        self.env={'BUZZ_PRIVATE_KEY':'fixture-only','BUZZ_RELAY_URL':'wss://example.invalid','BUZZ_GIT_ORIGIN_CHANNEL_ID':self.channel}
        self.calls=0

    def runner(self, stdout, code=0):
        def run(argv, **kwargs):
            self.calls+=1
            assert argv[0]==reply.BUZZ_CLI
            assert kwargs['shell'] is False
            kwargs['cwd']=os.path.dirname(__file__)
            script='import sys; assert sys.stdin.read()=="literal $HOME\\n  body  "; print('+repr(stdout)+'); sys.exit('+str(code)+')'
            return subprocess.run([sys.executable,'-c',script], **kwargs)
        return run

    def send(self, runner):
        return reply.send_reply(self.channel,'a'*64,'literal $HOME\n  body  ',env=self.env,runner=runner)

    def test_real_process_valid_whitespace_extra_fields(self):
        receipt=' \n'+json.dumps({'accepted':True,'event_id':'b'*64,'extra':{'x':1}})+'\n '
        self.assertEqual(self.send(self.runner(receipt)),'Reply sent to Buzz.')
        self.assertEqual(self.calls,1)

    def test_real_process_rejected_receipt_blocks_retry(self):
        runner=self.runner(json.dumps({'accepted':False,'event_id':'b'*64}))
        for _ in range(2):
            with self.assertRaises(RuntimeError): self.send(runner)
        self.assertEqual(self.calls,1)

    def test_real_process_nonzero_rejects_valid_receipt(self):
        with self.assertRaises(RuntimeError):
            self.send(self.runner(json.dumps({'accepted':True,'event_id':'b'*64}),1))

    def test_real_process_malformed_receipt_no_output_leak(self):
        with self.assertRaises(RuntimeError) as cm:
            self.send(self.runner('PRIVATE-STDOUT not JSON'))
        self.assertNotIn('PRIVATE',str(cm.exception))

if __name__=='__main__': unittest.main(verbosity=2)
