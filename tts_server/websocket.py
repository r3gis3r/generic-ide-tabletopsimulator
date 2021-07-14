"""
Websocket plugin server
"""

import asyncio
import json
import logging

from tts_client.direct_ide import IDECommunication

logger = logging.getLogger("wsconnector")
USERS = set()


async def notify_message(message):
    if USERS:  # asyncio.wait doesn't accept an empty list
        await asyncio.wait([user.send(json.dumps(message)) for user in USERS])


async def websocket_main(websocket, path, tts_host="127.0.0.1", tts_port=39999, **_):
    # register(websocket) sends user_event() to websocket
    USERS.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            messageID = data.get("messageID")
            if messageID is None:
                logger.error("Invalid message : %s", message)
            elif messageID == 101:
                # reserved for ide com
                pass
            else:
                ide_com = IDECommunication(host=tts_host, port=tts_port)
                await ide_com.send(data)

    finally:
        USERS.remove(websocket)
