import argparse
import struct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("hexstring")
    args = parser.parse_args()

    b = bytes.fromhex(args.hexstring)

    op_type, num_ops, num_addresses, keep_alive = struct.unpack_from(">BBBB", b, 0)
    print(f"> Operation type: {op_type}")
    print(f"> Keep Alive: {bool(keep_alive)}")
    print(f"> Num addresses: {num_addresses}")

    if op_type == 1:
        return

    offset = 4
    addresses = struct.unpack_from(f">{num_addresses}I", b, offset)

    for i, address in enumerate(addresses):
        print(f"  * Address {i}: 0x{address:08x}")

    offset += num_addresses * 4

    print(f"> Num operations: {num_ops}")
    for i in range(num_ops):
        op_byte = struct.unpack_from(">B", b, offset)[0]
        offset += 1

        operation_pretty = []

        if bool(op_byte & 0x20):
            byte_count = 4
        else:
            byte_count = struct.unpack_from(">B", b, offset)[0]
            offset += 1

        # Has read
        if bool(op_byte & 0x80):
            operation_pretty.append(f"read {byte_count} bytes")

        address = addresses[op_byte & 0x7]
        address_text = f"0x{address:08x}"

        # Has offset
        if bool(op_byte & 0x10):
            address_offset = struct.unpack_from(">h", b, offset)[0]
            offset += 2
            address_text = f"*{address_text} {address_offset:+05x}"

        # Has write
        if bool(op_byte & 0x40):
            write_data = b[offset:offset + byte_count]
            offset += byte_count
            if len(write_data) != byte_count:
                raise ValueError(f"At op {i}, expected {byte_count} bytes. Got {len(write_data)}")
            operation_pretty.append(f"write {write_data.hex()}")
            if byte_count == 4:
                operation_pretty[-1] += f" ({int.from_bytes(write_data, 'big')})"

        print(f"  * At {address_text}, {' and '.join(operation_pretty)}.")


if __name__ == '__main__':
    main()
