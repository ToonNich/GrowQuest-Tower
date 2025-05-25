import nest_asyncio
import asyncio
from pywizlight import wizlight, PilotBuilder

# Fix the loop issue
nest_asyncio.apply()

# Your bulb IP
bulb = wizlight("192.168.1.125")

async def main():
    print("🔌 Turning bulb ON (white)...")
    await bulb.turn_on(PilotBuilder(rgb=(255, 255, 255), brightness=100))
    await asyncio.sleep(2)

    print("🌸 Changing to Grow Light (pink)...")
    await bulb.turn_on(PilotBuilder(rgb=(255, 0, 180), brightness=100))
    await asyncio.sleep(2)

    print("🔕 Turning bulb OFF...")
    await bulb.turn_off()

asyncio.get_event_loop().run_until_complete(main())
