#!/usr/bin/env python3

import asyncio


async def _sleep(sleep_time: int = 1):
    """Sleep async.

    __ https://stackoverflow.com/a/61764275/2402577
    """
    await asyncio.sleep(sleep_time)
