# -*- coding: utf-8 -*-
import aioamqp
import settings

connection = None
protocol = None

async def declare_queues(channel):
    """声明所有的公用队列."""

    # worker_heartbeat
    await channel.queue_declare(queue_name='worker_heartbeat', durable=False)
    await channel.queue_bind(
        queue_name='worker_heartbeat', exchange_name='amq.direct', routing_key='worker_heartbeat')

    # worker_report
    await channel.queue_declare(queue_name='worker_report', durable=False)
    await channel.queue_bind(
        queue_name='worker_report', exchange_name='amq.direct', routing_key='worker_report')

    # weibo_data
    await channel.queue_declare(queue_name='weibo_data', durable=True)
    await channel.queue_bind(
        queue_name='weibo_data', exchange_name='amq.direct', routing_key='weibo_data')

    # worker_task
    await channel.queue_declare(queue_name='worker_task', durable=False)
    await channel.queue_bind(
        queue_name='worker_task', exchange_name='amq.direct', routing_key='worker_task')


async def disconnected(exception):
    global connection, protocol
    connection = None
    protocol = None
    print(exception)
    raise exception

async def get_channel():
    global connection, protocol
    if not connection or not protocol:
        try:
            connection, protocol = await aioamqp.connect(
                host=settings.RABBITMQ_SETTINGS['host'],
                virtualhost=settings.RABBITMQ_SETTINGS['virtualhost'],
                on_error=disconnected,
                # heartbeat=20,
            )
        except aioamqp.AmqpClosedConnection as e:
            await disconnected(e)
            raise
        channel = await protocol.channel()
        await declare_queues(channel)
    return channel
