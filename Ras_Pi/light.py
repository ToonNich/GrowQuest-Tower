from pywizlight.discovery import discover_lights
import asyncio

async def discover():
    bulbs = await discover_lights(broadcast_space="192.168.1.255")
    if not bulbs:
        print("❌ No bulbs found. Check that WiZ bulb is on the same Wi-Fi and powered on.")
    for bulb in bulbs:
        print(f"💡 Found WiZ bulb at: {bulb.ip}")

asyncio.run(discover())
