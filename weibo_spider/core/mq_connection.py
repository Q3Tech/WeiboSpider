# -*- coding: utf-8 -*-
import aioamqp
import settings

connection = None
protocol = None


async def disconnected(exception):
    global connection, protocol
    connection = None
    protocol = None
    print(exception)


async def get_channel():
    global connection, protocol
    if not connection or not protocol:
        try:
            connection, protocol = await aioamqp.connect(
                host=settings.RABBITMQ_SETTINGS['host'],
                virtualhost=settings.RABBITMQ_SETTINGS['virtualhost'],
                on_error=disconnected,
            )
        except aioamqp.AmqpClosedConnection as e:
            await disconnected(e)
    channel = await protocol.channel()
    return channel
