# -*- coding: utf-8 -*-
import re
from functools import partial

import eventlet
from nameko.exceptions import ConfigurationError
from nameko.extensions import Entrypoint, ProviderCollector, SharedExtension
from slackclient import SlackClient

from nameko_slack import constants


EVENT_TYPE_MESSAGE = "message"


class SlackRTMClientManager(SharedExtension, ProviderCollector):
    def __init__(self):

        super(SlackRTMClientManager, self).__init__()

        self.read_interval = 1

        self.clients = {}

    def setup(self):

        try:
            config = self.container.config[constants.CONFIG_KEY]
        except KeyError:
            raise ConfigurationError(
                "`{}` config key not found".format(constants.CONFIG_KEY)
            )

        token = config.get("TOKEN")
        clients = config.get("BOTS")
        if token:
            self.clients[constants.DEFAULT_BOT_NAME] = SlackClient(token)
        if clients:
            for bot_name, token in clients.items():
                self.clients[bot_name] = SlackClient(token)

        if not self.clients:
            raise ConfigurationError(
                "At least one token must be provided in `{}` config".format(
                    constants.CONFIG_KEY
                )
            )

    def start(self):
        for bot_name, client in self.clients.items():
            client.server.rtm_connect()
            run = partial(self.run, bot_name, client)
            self.container.spawn_managed_thread(run)

    def run(self, bot_name, client):
        while True:
            for event in client.rtm_read():
                self.handle(bot_name, event)
            eventlet.sleep(self.read_interval)

    def handle(self, bot_name, event):
        for provider in self._providers:
            if provider.bot_name == bot_name:
                provider.handle_event(event)

    def reply(self, bot_name, event, message):
        client = self.clients[bot_name]
        client.rtm_send_message(event["channel"], message)


class RTMEventHandlerEntrypoint(Entrypoint):

    clients = SlackRTMClientManager()

    def __init__(self, event_type=None, bot_name=None, **kwargs):
        self.bot_name = bot_name or constants.DEFAULT_BOT_NAME
        self.event_type = event_type
        super(RTMEventHandlerEntrypoint, self).__init__(**kwargs)

    def setup(self):
        self.clients.register_provider(self)

    def stop(self):
        self.clients.unregister_provider(self)

    def handle_event(self, event):
        if self.event_type and event.get("type") != self.event_type:
            return
        args = (event,)
        kwargs = {}
        context_data = {}
        self.container.spawn_worker(self, args, kwargs, context_data=context_data)


handle_event = RTMEventHandlerEntrypoint.decorator


class RTMMessageHandlerEntrypoint(RTMEventHandlerEntrypoint):
    def __init__(self, message_pattern=None, **kwargs):
        if message_pattern:
            self.message_pattern = re.compile(message_pattern)
        else:
            self.message_pattern = None
        super(RTMMessageHandlerEntrypoint, self).__init__(**kwargs)

    def handle_event(self, event):
        if event.get("type") == EVENT_TYPE_MESSAGE:
            if self.message_pattern:
                match = self.message_pattern.match(event.get("text", ""))
                if match:
                    kwargs = match.groupdict()
                    args = () if kwargs else match.groups()
                    args = (event, event.get("text")) + args
                else:
                    return
            else:
                args = (event, event.get("text"))
                kwargs = {}
            context_data = {}
            handle_result = partial(self.handle_result, event)
            self.container.spawn_worker(
                self,
                args,
                kwargs,
                context_data=context_data,
                handle_result=handle_result,
            )

    def handle_result(self, event, worker_ctx, result, exc_info):
        if result:
            self.clients.reply(self.bot_name, event, result)
        return result, exc_info


handle_message = RTMMessageHandlerEntrypoint.decorator
