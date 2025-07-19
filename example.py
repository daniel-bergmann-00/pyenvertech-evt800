#!/usr/bin/env python
"""Basic usage example and testing of pyenvertechevt800."""

import argparse
import asyncio
import logging
import signal
import sys

import pyenvertechevt800

# This example will work with Python 3.9+

_LOGGER = logging.getLogger(__name__)

VAR = {}


def print_table(sensors: dict):
    """Print sensors formatted as table."""
    for sen_name, sen_value in sensors.items():
        if sen_value is None:
            print("{:>20}".format(sen_name))
        else:
            print("{:>20}{:>25}".format(sen_name, str(sen_value)))


async def main_loop(ip: str, port: int):
    """Run main loop."""

    def on_data(data):
        print_table(data)

    _LOGGER.debug("Initializing device")
    VAR["device"] = pyenvertechevt800.EnvertechEVT800(ip, port, on_data)
    _LOGGER.debug("Starting device")
    VAR["device"].start()


async def main():
    """Run example."""
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Test the EVT800 connect library.")
    parser.add_argument(
        "ip",
        type=str,
        help="IP address of the EVT800 device",
        default="192.168.2.66",
        required=False,
    )
    parser.add_argument(
        "port", type=int, help="Port of the TCP Server", default="14889", required=False
    )

    args = parser.parse_args()

    def _shutdown(*_):
        try:
            _LOGGER.debug("Stopping device")
            VAR["device"].stop()
        except Exception:
            return

    signal.signal(signal.SIGINT, _shutdown)

    _LOGGER.debug("Starting main_loop")
    await main_loop(args.ip, args.port)

    if VAR["device"] and VAR["device"]._task:
        await VAR["device"]._task


if __name__ == "__main__":
    asyncio.run(main())
