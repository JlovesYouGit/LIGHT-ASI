import sys
import os
sys.path.append(os.getcwd())

from engine.world.onion_gateway import OnionGateway

def live_test():
    print("[*] Starting Live Onion Test...")
    gateway = OnionGateway()
    
    print(f"[*] Connecting to {gateway.gateway_target}...")
    res = gateway.establish_communication()
    print(f"[✓] Status: {res.get('status')}")
    print(f"[✓] Protocol: {res.get('protocol')}")
    
    print("\n[*] Latest Decoded Traffic:")
    messages = gateway.get_messages()
    for m in messages:
        print(f"--- {m['direction'].upper()} [{m['timestamp']}] ---")
        print(m['decoded'])
        print("-" * 40)

    # test custom message
    print("\n[*] Sending 'Hello' to see response decoding...")
    res = gateway.send_message("Hello from Light-ASI")
    print(f"[✓] Sent. Response Preview: {res.get('response_preview')}")

if __name__ == "__main__":
    live_test()
