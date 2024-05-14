"""Core"""

import asyncio
from dataclasses import dataclass


@dataclass
class Core:
    consumption = 0
    production = 0
    surplus = 0
    config = {}

    async def core_loop(self):
        while True:
            print("Running core loop...")
            print(self.surplus)
            await asyncio.sleep(1)
