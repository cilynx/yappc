import unittest
import time
from app.pentair import Packet, Pump

PAYLOAD_HEADER  = 0xA5
SRC             = 0x21
DST             = 0x60
GET_PUMP_STATUS = 0x07
REMOTE_CONTROL  = 0x04
ON              = 0xFF
PUMP_PROGRAM    = 0x01
SET             = 0x02
RPM             = 0xC4
VERSION         = 0x00

class TestPumpMethods(unittest.TestCase):

    def test_get_power(self):
        self.assertIn(Pump(1).power, [True, False])

    def test_get_rpm(self):
        self.assertGreaterEqual(Pump(1).rpm, 0)

    def test_get_watts(self):
        self.assertGreaterEqual(Pump(1).watts, 0)

class TestPacketMethods(unittest.TestCase):

### Data Length, because incoming data can have several formats

    def test_data_length_with_no_data(self):
        packet = Packet(dst=DST, action=GET_PUMP_STATUS)
        self.assertEqual(packet.data_length, 0)

    def test_data_length_with_single_data_byte(self):
        packet = Packet(dst=DST, action=REMOTE_CONTROL, data=ON)
        self.assertEqual(packet.data_length, 1)

    def test_data_length_with_single_data_byte_list(self):
        packet = Packet(dst=DST, action=REMOTE_CONTROL, data=[ON])
        self.assertEqual(packet.data_length, 1)

    def test_data_length_with_multiple_data_bytes(self):
        packet = Packet(dst=DST, action=PUMP_PROGRAM, data=[SET, RPM, 5, 220])
        self.assertEqual(packet.data_length, 4)

### Payload, as above, mostly checking various input format handling

    def test_payload_with_no_data(self):
        packet = Packet(dst=DST, action=GET_PUMP_STATUS)
        self.assertEqual(packet.payload, [PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0])

    def test_payload_with_single_data_byte(self):
        packet = Packet(dst=DST, action=REMOTE_CONTROL, data=ON)
        self.assertEqual(packet.payload, [PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON])

    def test_payload_with_single_data_byte_list(self):
        packet = Packet(dst=DST, action=REMOTE_CONTROL, data=[ON])
        self.assertEqual(packet.payload, [PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON])

    def test_payload_with_multiple_data_bytes(self):
        packet = Packet(dst=DST, action=PUMP_PROGRAM, data=[SET, RPM, 5, 220])
        self.assertEqual(packet.payload, [PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220])

### Checksums and Such

    def test_checkbytes(self):
        packet = Packet(dst=DST, action=PUMP_PROGRAM, data=[SET, RPM, 5, 220])
        self.assertEqual(packet.checkbytes, [2, 210])

    def test_checksum(self):
        packet = Packet(dst=DST, action=PUMP_PROGRAM, data=[SET, RPM, 5, 220])
        self.assertEqual(packet.checksum, 2*256 + 210)

### Key=Value Construction

    def test_kv_construction_no_data(self):
        packet = Packet(dst=DST, action=GET_PUMP_STATUS)
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, GET_PUMP_STATUS)
        self.assertEqual(packet.data_length, 0)
        self.assertEqual(packet.data, None)
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0, 1, 45])

    def test_kv_construction_single_data_byte(self):
        packet = Packet(dst=DST, action=REMOTE_CONTROL, data=ON)
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, REMOTE_CONTROL)
        self.assertEqual(packet.data_length, 1)
        self.assertEqual(packet.data, [ON])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])

    def test_kv_construction_single_data_byte_list(self):
        packet = Packet(dst=DST, action=REMOTE_CONTROL, data=[ON])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, REMOTE_CONTROL)
        self.assertEqual(packet.data_length, 1)
        self.assertEqual(packet.data, [ON])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])

    def test_kv_construction_multiple_data_bytes(self):
        packet = Packet(dst=DST, action=PUMP_PROGRAM, data=[SET, RPM, 5, 220])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, PUMP_PROGRAM)
        self.assertEqual(packet.data_length, 4)
        self.assertEqual(packet.data, [SET, RPM, 5, 220])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 210])

### Byte Construction, No Header, No Data

    def test_byte_construction_no_header_no_data_no_checksum(self):
        packet = Packet([DST, SRC, GET_PUMP_STATUS, 0])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, GET_PUMP_STATUS)
        self.assertEqual(packet.data_length, 0)
        self.assertEqual(packet.data, None)
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0, 1, 45])

    def test_byte_construction_no_header_no_data_valid_checksum(self):
        packet = Packet([DST, SRC, GET_PUMP_STATUS, 0, 1, 45])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, GET_PUMP_STATUS)
        self.assertEqual(packet.data_length, 0)
        self.assertEqual(packet.data, None)
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0, 1, 45])

    def test_byte_construction_no_header_no_data_invalid_checksum(self):
        with self.assertRaises(ValueError):
            Packet([DST, SRC, GET_PUMP_STATUS, 0, 1, 46])

### Byte Construction, With Header, No Data

    def test_byte_construction_with_header_no_data_no_checksum(self):
        packet = Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, GET_PUMP_STATUS)
        self.assertEqual(packet.data_length, 0)
        self.assertEqual(packet.data, None)
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0, 1, 45])

    def test_byte_construction_with_header_no_data_valid_checksum(self):
        packet = Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0, 1, 45])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, GET_PUMP_STATUS)
        self.assertEqual(packet.data_length, 0)
        self.assertEqual(packet.data, None)
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0, 1, 45])

    def test_byte_construction_with_header_no_data_invalid_checksum(self):
        with self.assertRaises(ValueError):
            Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, GET_PUMP_STATUS, 0, 1, 46])

### Byte Construction, No Header, Single Data Byte

    def test_byte_construction_no_header_single_data_byte_no_checksum(self):
        packet = Packet([DST, SRC, REMOTE_CONTROL, 1, ON])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, REMOTE_CONTROL)
        self.assertEqual(packet.data_length, 1)
        self.assertEqual(packet.data, [ON])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])

    def test_byte_construction_no_header_single_data_byte_valid_checksum(self):
        packet = Packet([DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, REMOTE_CONTROL)
        self.assertEqual(packet.data_length, 1)
        self.assertEqual(packet.data, [ON])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])

    def test_byte_construction_no_header_single_data_byte_invalid_checksum(self):
        with self.assertRaises(ValueError):
            Packet([DST, SRC, REMOTE_CONTROL, 1, ON, 2, 43])

### Byte Construction, With Header, Single Data Byte

    def test_byte_construction_with_header_single_data_byte_no_checksum(self):
        packet = Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, REMOTE_CONTROL)
        self.assertEqual(packet.data_length, 1)
        self.assertEqual(packet.data, [ON])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])

    def test_byte_construction_with_header_single_data_byte_valid_checksum(self):
        packet = Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, REMOTE_CONTROL)
        self.assertEqual(packet.data_length, 1)
        self.assertEqual(packet.data, [ON])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 42])

    def test_byte_construction_with_header_single_data_byte_invalid_checksum(self):
        with self.assertRaises(ValueError):
            Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, REMOTE_CONTROL, 1, ON, 2, 43])

### Byte Construction, No Header, Multiple Data Bytes

    def test_byte_construction_no_header_multiple_data_bytes_no_checksum(self):
        packet = Packet([DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, PUMP_PROGRAM)
        self.assertEqual(packet.data_length, 4)
        self.assertEqual(packet.data, [SET, RPM, 5, 220])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 210])

    def test_byte_construction_no_header_multiple_data_bytes_valid_checksum(self):
        packet = Packet([DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 210])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, PUMP_PROGRAM)
        self.assertEqual(packet.data_length, 4)
        self.assertEqual(packet.data, [SET, RPM, 5, 220])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 210])

    def test_byte_construction_no_header_multiple_data_bytes_invalid_checksum(self):
        with self.assertRaises(ValueError):
            Packet([DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 211])

### Byte Construction, With Header, Multiple Data Bytes

    def test_byte_construction_with_header_multiple_data_bytes_no_checksum(self):
        packet = Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, PUMP_PROGRAM)
        self.assertEqual(packet.data_length, 4)
        self.assertEqual(packet.data, [SET, RPM, 5, 220])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 210])

    def test_byte_construction_with_header_multiple_data_bytes_valid_checksum(self):
        packet = Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 210])
        self.assertEqual(packet.dst, DST)
        self.assertEqual(packet.src, SRC)
        self.assertEqual(packet.action, PUMP_PROGRAM)
        self.assertEqual(packet.data_length, 4)
        self.assertEqual(packet.data, [SET, RPM, 5, 220])
        self.assertEqual(packet.bytes, [0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 210])

    def test_byte_construction_with_header_multiple_data_bytes_invalid_checksum(self):
        with self.assertRaises(ValueError):
            Packet([0xFF, 0x00, 0xFF, PAYLOAD_HEADER, VERSION, DST, SRC, PUMP_PROGRAM, 4, SET, RPM, 5, 220, 2, 211])
