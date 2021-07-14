import contextlib
import json
import logging
import asyncio
import tempfile
from functools import partial

from .websocket import websocket_main, notify_message

from .handlers import process_message

log = logging.getLogger("ttsserver")

clients = {}  # task -> (reader, writer)


def accept_client(client_reader, client_writer, **kwargs):
    task = asyncio.Task(handle_request(client_reader, client_writer, **kwargs))
    clients[task] = (client_reader, client_writer)

    def client_done(task):
        del clients[task]
        client_writer.close()
        # log.debug("End Connection")

    # log.debug("New Connection")
    task.add_done_callback(client_done)


async def handle_request(client_reader, client_writer, **kwargs):
    # send a hello to let the client know they are connected
    data_cache = ""
    log.debug("Start handling client")
    while True:
        # wait for input from client
        data = await asyncio.wait_for(client_reader.readline(), timeout=10.0)
        # log.info("Has data %s", data)
        if not data:
            break
        data_cache += data.decode()
        try:
            parsed = json.loads(data_cache)
            data_cache = ""
            process_message(parsed, **kwargs)
            # Forward to websocket server -- does nothing if no server there
            await notify_message(parsed)
        except json.decoder.JSONDecodeError:
            pass
        except Exception as e:
            log.info("Retrieve error %s", data_cache, exc_info=e)


async def tts_serve(
    host=None,
    port=39998,
    tts_port=39999,
    tts_host="127.0.0.1",
    export_dir=None,
    websocket_port=None,
    **kwargs
):
    if export_dir:
        export_dir_ctxt = contextlib.nullcontext(export_dir)
    else:
        export_dir_ctxt = tempfile.TemporaryDirectory(prefix="tts_")

    with export_dir_ctxt as out_dir:
        servers_coro = []
        server = await asyncio.start_server(
            partial(accept_client, export_dir=out_dir, **kwargs),
            host=host,
            port=port,
            limit=10 * 1024 * 1024,
        )
        servers_coro.append(server.serve_forever())
        if websocket_port:
            import websockets as websockets

            servers_coro.append(
                websockets.serve(
                    partial(websocket_main, tts_port=tts_port, tts_host=tts_host),
                    host=host,
                    port=websocket_port,
                    # limit=10 * 1024 * 1024,
                )
            )
        await asyncio.gather(*servers_coro)
