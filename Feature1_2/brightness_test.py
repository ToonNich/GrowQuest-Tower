import nest_asyncio
import asyncio
from pywizlight import wizlight, PilotBuilder

nest_asyncio.apply()

bulb = wizlight("192.168.1.114")  # Replace with your bulb IP

async def brightness_test():
    for brightness in range(10, 101, 10):  # From 10 to 100, step 10
        print(f"Setting brightness to {brightness}% (white light)")
        await bulb.turn_on(PilotBuilder(rgb=(255, 255, 255), brightness=brightness))
        await asyncio.sleep(3)  # Hold for 3 seconds so you can see

    print("Turning bulb off")
    await bulb.turn_off()

if __name__ == "__main__":
    asyncio.run(brightness_test())
