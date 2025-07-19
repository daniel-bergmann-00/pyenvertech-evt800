import asyncio

import pytest

from pyenvertechevt800 import (
    EnvertechEVT800,
    bytes_to_u16,
    bytes_to_u32,
    parse_data_packet,
    safe_divide,
)


class Test_EVT800_class:
    @pytest.mark.asyncio
    async def test_envertech_evt800_data_package_lifecycle(monkeypatch):
        # Dummy callback
        received = []

        def on_data(data):
            received.append(data)

        # Patch asyncio.open_connection to simulate connection
        class DummyReader:
            def __init__(self, packets):
                self.packets = packets
                self.index = 0

            async def read(self, n):
                if self.index < len(self.packets):
                    pkt = self.packets[self.index]
                    self.index += 1
                    return pkt
                await asyncio.sleep(0.01)
                return b""

        class DummyWriter:
            def write(self, data):
                pass

            async def drain(self):
                pass

            def close(self):
                pass

        async def dummy_open_connection(ip, port):
            # Simulate a valid packet
            packet = bytes.fromhex(
                "680056681004315258207a007a01000000000000315258207a7a40b02d860000bafb2e8c3c4931fe000000000000000000000000315258217a7a3131017b00000e4a2ab33c4931fe020200000000000000000000ef16"
            )
            return DummyReader([packet]), DummyWriter()

        monkeypatch.setattr(asyncio, "open_connection", dummy_open_connection)

        evt = EnvertechEVT800("127.0.0.1", 1234, on_data)
        evt.start()
        await asyncio.sleep(0.05)
        await evt.stop()
        assert evt.online is False
        assert received
        expected = {
            "id_1": 49828832,
            "id_2": 49828833,
            "sw_version": "7A.7A",
            "input_voltage_1": 32.34375,
            "input_voltage_2": 24.595703125,
            "power_1": 182.09375,
            "power_2": 5.921875,
            "ac_voltage_1": 241.140625,
            "ac_voltage_2": 241.140625,
            "ac_frequency_1": 49.9921875,
            "ac_frequency_2": 49.9921875,
            "temperature_1": 53.09375,
            "temperature_2": 45.3984375,
            "total_energy_1": 5.8431396484375,
            "total_energy_2": 0.446533203125,
            "current_1": 0.7551351001101536,
            "current_2": 0.024557765826475734,
        }
        for k, v in expected.items():
            actual = received[0][k]
            if isinstance(v, float):
                assert abs(actual - v) < 1e-6, (
                    f"Key '{k}': {actual} != {v} (delta={abs(actual - v)})"
                )
            else:
                assert actual == v, f"Key '{k}': {actual} != {v}"

    @pytest.mark.asyncio
    async def test_envertech_evt800_pool_message_lifecycle(monkeypatch):
        # Patch asyncio.open_connection to simulate connection
        class DummyReader:
            def __init__(self, packets):
                self.packets = packets
                self.index = 0

            async def read(self, n):
                if self.index < len(self.packets):
                    pkt = self.packets[self.index]
                    self.index += 1
                    return pkt
                await asyncio.sleep(0.01)
                return b""

        class DummyWriter:
            def write(self, data):
                pass

            async def drain(self):
                pass

            def close(self):
                pass

        async def dummy_open_connection(ip, port):
            # Simulate a valid packet
            packet = bytes.fromhex(
                "680020681006315258200000000000014b0000e7010000010500000000009016"
            )
            return DummyReader([packet]), DummyWriter()

        monkeypatch.setattr(asyncio, "open_connection", dummy_open_connection)

        def on_data(data):
            return

        evt = EnvertechEVT800("127.0.0.1", 1234, on_data)
        evt.start()
        await asyncio.sleep(0.05)
        await evt.stop()
        assert evt.online is False
        assert evt.serial_number == "31525820"

    def test_parse_inverter_packet_min_length():
        # Too short
        assert parse_data_packet(b"\x00" * 10) == {}

    def test_bytes_to_u16_and_u32():
        assert bytes_to_u16(0x12, 0x34) == 0x1234
        assert bytes_to_u32(0x01, 0x02, 0x03, 0x04) == 0x01020304

    def test_safe_divide():
        assert safe_divide(10, 2) == 5
        assert safe_divide(10, 0) == 0
        assert safe_divide(None, 2) == 0
        assert safe_divide(10, None) == 0
