from pywizlight.discovery import discover_lights
import asyncio

async def discover_multi():
    for bcast in ("192.168.1.255", "192.168.0.255", "10.0.0.255" , "172.20.10.15"):
        bulbs = await discover_lights(broadcast_space=bcast)
        if bulbs:
            print(f"✅ Found on {bcast}:")
            for bulb in bulbs:
                print(f"   💡 {bulb.ip}")
            return
        else:
            print(f"…nothing on {bcast}")
    print("❌ No bulbs found. Check subnet, firewall, and network isolation.")

# In a .py file:
if __name__ == "__main__":
    asyncio.run(discover_multi())
# In Jupyter, just: await discover_multi()
