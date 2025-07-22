"""EVT-800 devicelibrary for Python.

Source: http://www.github.com/daniel-bergmann-00/pyenvertech-evt800
"""

import asyncio
import logging
import time
from typing import Any, Callable, Optional

_LOGGER = logging.getLogger(__name__)


class Connection:  # pylint: disable=too-few-public-methods
    """Connection details for the EVT-800 device."""

    def __init__(self, ip: str, port: int) -> None:
        """Initialize connection details."""
        self.ip = ip
        self.port = port


class EVT800Task:  # pylint: disable=too-few-public-methods
    """Manage the background task for reading data from the EVT-800 device."""

    def __init__(self) -> None:
        """Initialize the task with the EVT-800 instance."""
        self.stop_event = asyncio.Event()
        self.task: Optional[asyncio.Task] = None


class EnvertechEVT800:
    """Class to connect to the Envertech EVT-800 device and read parameters."""

    def __init__(self, ip: str, port: int, on_data: Callable[[dict], None]):
        """Initialize the EVT-800 device connection."""
        self.conn = Connection(ip=ip, port=port)
        self.on_data = on_data
        self.data = {
            "timestamp": round(time.time() * 1000),  # Use current time in milliseconds
            "id_1": None,
            "id_2": None,
            "sw_version": None,
            "input_voltage_1": None,
            "input_voltage_2": None,
            "power_1": None,
            "power_2": None,
            "ac_voltage_1": None,
            "ac_voltage_2": None,
            "ac_frequency_1": None,
            "ac_frequency_2": None,
            "temperature_1": None,
            "temperature_2": None,
            "total_energy_1": None,
            "total_energy_2": None,
            "current_1": None,
            "current_2": None,
        }
        self.serial_number: str = ""
        self._task: EVT800Task = EVT800Task()
        self.online = False
        self._unavailable_logged = False

    def start(self) -> None:
        """Start the background TCP read task."""
        _LOGGER.debug("Starting TCP read task")
        self._task.stop_event.clear()
        self._task.task = asyncio.create_task(self._run())

    def stop(self) -> None:
        """Stop the TCP read task."""
        _LOGGER.debug("Stopping TCP read task...")
        self._task.stop_event.set()
        if self._task.task is not None:
            self._task.task.cancel("Stopping EVT-800")

    async def test_connection(self, timeout: int = 60) -> bool:
        """Test the connection to the EVT-800 device."""
        try:
            reader, writer = await asyncio.open_connection(self.conn.ip, self.conn.port)
            # Wait up to 60 seconds to receive a valid data package
            packet = None
            try:
                end_time = asyncio.get_event_loop().time() + timeout
                while asyncio.get_event_loop().time() < end_time:
                    buffer = await asyncio.wait_for(reader.read(86), timeout=timeout)
                    if not buffer:
                        continue

                    packet = await self.get_packet_from_buffer(buffer)

                    if not packet:
                        _LOGGER.warning("No valid packet found in buffer")
                        continue

                    _LOGGER.debug("Received packet: %s", packet.hex())

                    if len(packet) == 32:
                        _LOGGER.debug("Parsing poll message packet")
                        self.serial_number = parse_poll_message_packet(packet)
                        return True

                    if packet and len(packet) >= 24:
                        await self.send_ack(writer, packet)
                    else:
                        _LOGGER.warning("Packet too short for ACK, not sent")
            except asyncio.TimeoutError:
                _LOGGER.warning("Timeout waiting for data packet")
                return False
            return False
        except (asyncio.TimeoutError, OSError, asyncio.CancelledError):
            return False

    async def _run(self) -> None:
        while not self._task.stop_event.is_set():
            try:
                await self._main_loop()
            except (asyncio.TimeoutError, OSError, asyncio.CancelledError) as ex:
                self.online = False
                self.reset_data()
                if not self._unavailable_logged:
                    _LOGGER.warning("EVT800 unavailable: %s", ex)
                    self._unavailable_logged = True
                if not self._task.stop_event.is_set():
                    _LOGGER.debug("Retrying connection in %s seconds...", 60)
                    await asyncio.sleep(60)

    async def _main_loop(self) -> None:
        _LOGGER.info("Connecting to EVT800 at %s:%s", self.conn.ip, self.conn.port)
        reader, writer = await asyncio.open_connection(self.conn.ip, self.conn.port)
        self.online = True
        if self._unavailable_logged:
            _LOGGER.info("EVT800 is back online")
            self._unavailable_logged = False
        _LOGGER.info("Connected to EVT800 at %s:%s", self.conn.ip, self.conn.port)

        while not self._task.stop_event.is_set():
            _LOGGER.debug("Waiting for data from EVT800")
            buffer = await asyncio.wait_for(reader.read(86), timeout=60)
            if not buffer:
                break

            packet = await self.get_packet_from_buffer(buffer)
            if not packet:
                _LOGGER.warning("No valid packet found in buffer")
                continue

            _LOGGER.debug("Received packet: %s", packet.hex())
            data = {}
            if len(packet) >= 39:
                _LOGGER.debug("Parsing data packet")
                data = parse_data_packet(packet)
            elif len(packet) == 32:
                _LOGGER.debug("Parsing poll message packet")
                self.serial_number = parse_poll_message_packet(packet)
            else:
                _LOGGER.error("Received packet of unexpected length: %d", len(packet))
                self.reset_data()

            if data:
                self.on_data(data.copy())
                self.data = data

            # Send ACK
            if len(packet) >= 24:
                await self.send_ack(writer, packet)
            else:
                _LOGGER.warning("Packet too short for ACK, not sent")

        self.online = False
        self.reset_data()

    async def get_packet_from_buffer(self, buffer: bytes) -> Optional[bytes]:
        """Extract a valid packet from the buffer."""
        start = buffer.find(b"\x68\x00")
        if start == -1:
            return None
        end = buffer.find(b"\x16", start)
        if end == -1:
            return None
        return buffer[start : end + 1]

    async def send_ack(self, writer: asyncio.StreamWriter, packet: bytes) -> None:
        """Send an ACK packet back to the EVT-800 device."""
        sn = packet[20:24]
        ack = bytearray([0x68, 0x00, 0x10, 0x68, 0x10, 0x50])
        ack.extend(sn)
        ack.extend([0x00, 0x00, 0x00, 0x00, 0x78, 0x16])
        writer.write(bytes(ack))
        await writer.drain()
        _LOGGER.debug("Sent ACK: %s", ack.hex())

    def reset_data(self) -> None:
        """Reset the data dictionary to its initial state."""
        self.data["input_voltage_1"] = None
        self.data["input_voltage_2"] = None
        self.data["power_1"] = None
        self.data["power_2"] = None
        self.data["ac_voltage_1"] = None
        self.data["ac_voltage_2"] = None
        self.data["ac_frequency_1"] = None
        self.data["ac_frequency_2"] = None
        self.data["temperature_1"] = None
        self.data["temperature_2"] = None
        self.data["total_energy_1"] = None
        self.data["total_energy_2"] = None
        # Extra data
        self.data["current_1"] = None
        self.data["current_2"] = None


def parse_poll_message_packet(data: bytes) -> str:
    """Parsing a poll message packet.

    That looks like this: 68001068107732323232000000009f16
    """
    if len(data) != 32:
        return ""
    return data.hex()[12:20]


def parse_data_packet(data: bytes) -> dict[str, Any]:
    """Parse a data packet from the EVT-800 device.

    The packet should be at least 39 bytes long.
    """
    if len(data) < 39:
        return {}

    result: dict[str, Any] = {}
    result["timestamp"] = (
        round(time.time() * 1000),
    )  # Use current time in milliseconds
    result["id_1"] = data[20] * 1000000 + data[21] * 10000 + data[22] * 100 + data[23]
    # Extract sw_version (firmware) from packet, e.g. bytes 24-25 (typical for EVT800)
    result["sw_version"] = f"{data[24]:02X}.{data[25]:02X}"
    result["input_voltage_1"] = bytes_to_u16(data[26], data[27]) * 64 / 32768
    result["power_1"] = bytes_to_u16(data[28], data[29]) * 512 / 32768
    result["ac_voltage_1"] = bytes_to_u16(data[36], data[37]) * 512 / 32768
    result["ac_frequency_1"] = bytes_to_u16(data[38], data[39]) * 128 / 32768
    result["temperature_1"] = (bytes_to_u16(data[34], data[35]) * 256 / 32768) - 40
    result["total_energy_1"] = (
        bytes_to_u32(data[30], data[31], data[32], data[33]) * 4 / 32768
    )
    # Extra data
    result["current_1"] = safe_divide(result["power_1"], result["ac_voltage_1"])

    if len(data) > 71:
        result["id_2"] = (
            data[52] * 1000000 + data[53] * 10000 + data[54] * 100 + data[55]
        )
        result["total_energy_2"] = (
            bytes_to_u32(data[62], data[63], data[64], data[65]) * 4 / 32768
        )
        result["input_voltage_2"] = bytes_to_u16(data[58], data[59]) * 64 / 32768
        result["power_2"] = bytes_to_u16(data[60], data[61]) * 512 / 32768
        result["ac_voltage_2"] = bytes_to_u16(data[68], data[69]) * 512 / 32768
        result["ac_frequency_2"] = bytes_to_u16(data[70], data[71]) * 128 / 32768

        result["temperature_2"] = (bytes_to_u16(data[66], data[67]) * 256 / 32768) - 40
        # Extra data
        result["current_2"] = safe_divide(result["power_2"], result["ac_voltage_2"])
    else:
        result["id_2"] = None
        result["total_energy_2"] = None
        result["input_voltage_2"] = None
        result["power_2"] = None
        result["ac_voltage_2"] = None
        result["ac_frequency_2"] = None
        result["temperature_2"] = None
        result["current_2"] = None

    return result


def bytes_to_u16(b1: int, b2: int) -> int:
    """Convert two bytes to an unsigned 16-bit integer."""
    return (b1 << 8) | b2


def bytes_to_u32(b1: int, b2: int, b3: int, b4: int) -> int:
    """Convert four bytes to an unsigned 32-bit integer."""
    return (b1 << 24) | (b2 << 16) | (b3 << 8) | b4


def safe_divide(numerator: float, denominator: float) -> float:
    """Returns numerator / denominator or 0 if invalid or zero division."""
    try:
        if numerator is None or denominator in (None, 0):
            return 0
        return numerator / denominator
    except ZeroDivisionError:
        return 0
