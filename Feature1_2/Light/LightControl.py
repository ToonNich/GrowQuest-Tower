import nest_asyncio
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pywizlight import wizlight, PilotBuilder

nest_asyncio.apply()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LightControl")

app = FastAPI()

# Enable CORS for frontend on localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],  # Use ["*"] to allow all origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Replace with your actual bulb IP address
bulb = wizlight("192.168.1.114")

class ColorCommand(BaseModel):
    r: Optional[int] = None
    g: Optional[int] = None
    b: Optional[int] = None
    colortemp: Optional[int] = None  # Color temperature in Kelvins (e.g., 6500 for cool white)
    brightness: int = 100

@app.post("/turn_on")
async def turn_on_color(cmd: ColorCommand):
    try:
        if cmd.colortemp is not None:
            logger.info(f"Turning bulb ON with color temperature {cmd.colortemp}K at brightness {cmd.brightness}")
            await bulb.turn_on(PilotBuilder(colortemp=cmd.colortemp, brightness=cmd.brightness))
        elif None not in (cmd.r, cmd.g, cmd.b):
            logger.info(f"Turning bulb ON with RGB({cmd.r}, {cmd.g}, {cmd.b}) at brightness {cmd.brightness}")
            await bulb.turn_on(PilotBuilder(rgb=(cmd.r, cmd.g, cmd.b), brightness=cmd.brightness))
        else:
            raise HTTPException(status_code=400, detail="Must provide either RGB or color temperature")
        return {"status": "turned on"}
    except Exception as e:
        logger.error(f"Failed to turn on bulb: {e}")
        raise HTTPException(status_code=500, detail="Failed to turn on bulb")

@app.post("/turn_off")
async def turn_off():
    try:
        logger.info("Turning bulb OFF")
        await bulb.turn_off()
        return {"status": "turned off"}
    except Exception as e:
        logger.error(f"Failed to turn off bulb: {e}")
        raise HTTPException(status_code=500, detail="Failed to turn off bulb")
