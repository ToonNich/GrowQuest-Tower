from pywizlight.discovery import discover_lights
import asyncio

async def discover():
    bulbs = await discover_lights(broadcast_space="172.20.10.15")
    if not bulbs:
        print("❌ No bulbs found. Make sure the bulb is on the iPhone hotspot.")
    for bulb in bulbs:
        print(f"💡 Found WiZ bulb at: {bulb.ip}")

asyncio.run(discover())
