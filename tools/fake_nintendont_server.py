import asyncio
import struct

next_client_id = 0


def create_client_id():
    global next_client_id
    next_client_id += 1
    return next_client_id


_hard_coded_reads = {
    # Is this Prime 2 NTSC? Yes.
    b'\x00\x01\x01\x01\x80:\xc3\xb0\x806': b"\x01!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32",
    b'\x00\x01\x01\x01\x80A\x8e\xb8\xb0\x00\x04': b"\x01\x3B\xFA\x3E\xFF",
}


async def client_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    client_id = create_client_id()

    print(f"[{client_id: 3}] Client connected")
    while True:
        command = await reader.read(1024)
        command_id, num_ops, num_addresses, keep_alive = struct.unpack_from(">BBBB", command)
        print(f"[{client_id: 3}] Received request", command_id, num_ops, num_addresses, keep_alive)

        await asyncio.sleep(1)
        if command_id == 1:
            writer.write(struct.pack(">IIII", 2, 100, 100, 4))
        elif command_id == 0:
            if command in _hard_coded_reads:
                writer.write(_hard_coded_reads[command])
            else:
                print(f"[{client_id: 3}] Received command: {command}")
                writer.write(b"\x00\x00")

        await writer.drain()
        if not bool(keep_alive):
            writer.close()
            break


async def main():
    print("start_server")
    server = await asyncio.start_server(client_handler, port=43673)

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
