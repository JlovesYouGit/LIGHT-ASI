import unittest
from engine.world.onion_gateway import OnionGateway

class TestOnionGateway(unittest.TestCase):
    def setUp(self):
        self.gateway = OnionGateway()
        self.gateway.set_simulator(True)

    def test_decoding_base64(self):
        # SERVER-READY-ACCEPT
        raw = "U0VSVkVSLVJFQURZLUFDQ0VQVA=="
        decoded = self.gateway.decode_traffic(raw)
        self.assertIn("SERVER-READY-ACCEPT", decoded)

    def test_decoding_hex(self):
        # "hello" in hex: 68656c6c6f
        raw = "68656c6c6f"
        decoded = self.gateway.decode_traffic(raw)
        self.assertIn("hello", decoded)

    def test_send_message(self):
        res = self.gateway.send_message("hello")
        self.assertEqual(res["status"], "sent (simulated)")
        self.assertIn("GENESIS ACTIVATED", res["response_decoded"])
        
        messages = self.gateway.get_messages()
        self.assertEqual(len(messages), 2) # out and in
        self.assertEqual(messages[0]["direction"], "out")
        self.assertEqual(messages[1]["direction"], "in")

if __name__ == "__main__":
    unittest.main()
