import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.protocol.query import ping_bedrock_server

def test_live_ping():
    server = "geo.hivebedrock.network"
    port = 19132
    print(f"Pinging {server}:{port}...")
    result = ping_bedrock_server(server, port, timeout=3.0)
    print("Result:", result)
    if result["online"]:
        print(f"SUCCESS: Ping={result['latency_ms']}ms, Players={result['current_players']}/{result['max_players']}")
        return 0
    else:
        print("Could not reach Hive (network or rate limit), trying Galaxite...")
        result2 = ping_bedrock_server("play.galaxite.net", 19132, timeout=3.0)
        print("Result 2:", result2)
        return 0 if result2["online"] else 1

if __name__ == "__main__":
    sys.exit(test_live_ping())
