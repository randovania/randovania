from __future__ import annotations

import asyncio
import struct

next_client_id = 0


def create_client_id():
    global next_client_id
    next_client_id += 1
    return next_client_id


_hard_coded_reads = {
    # Is this Prime 2 NTSC? Yes.
    b"\x01\x01\x01\x01\x80:\xc3\xb0\x806": b"\x01!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32",
    b"\x01\x01\x01\x01\x80A\x8e\xb8\xb0\x00\x04": b"\x01\x3b\xfa\x3e\xff",
}


async def client_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    client_id = create_client_id()

    print(f"[{client_id: 3}] Client connected")
    while True:
        command = await reader.read(1024)
        command_as_str = command.hex()
        try:
            command_id, keep_alive = struct.unpack_from(">BB", command)
        except:
            print(f"Cannot parse following command: {command_as_str}")
            raise

        print(f"[{client_id: 3}] Received request", command_id, keep_alive)

        await asyncio.sleep(1)
        if command_id == 0:
            writer.write(struct.pack(">6I", 2, 100, 100, 4, 0, 0))
        elif command_id == 1:
            num_ops, num_addresses = struct.unpack_from(">8xII", command)
            print(f"Num ops: {num_ops} , num addresses: {num_addresses}")
            if command in _hard_coded_reads:
                writer.write(_hard_coded_reads[command])
            else:
                print(f"[{client_id: 3}] Received command: {command_as_str}")
                writer.write(b"\x00\x00")
        elif command_id == 2:
            print("ReadArray Memop not implemented yet")
        else:
            print(f"Unknown command id: {command_id}")

        await writer.drain()
        if not bool(keep_alive):
            writer.close()
            print("Not meant to keep alive, exiting")
            break
        else:
            print("Keeping alive")


async def main():
    print("start_server")
    server = await asyncio.start_server(client_handler, port=43673)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
