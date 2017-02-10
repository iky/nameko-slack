import re

import eventlet
from nameko.extensions import Entrypoint, ProviderCollector, SharedExtension
from slackclient import SlackClient


EVENT_TYPE_MESSAGE = 'message'


class SlackRTMClient(SharedExtension, ProviderCollector):
    """
    Slack Real Time Messaging API Client

    """

    def __init__(self):

        super(SlackRTMClient, self).__init__()

        self.read_interval = 1

        self.token = None

        self._client = None
        self._handlers = set()

    def setup(self):
        config = self.container.config.get('SLACK', {})
        self.token = config.get('TOKEN')

    def start(self):
        self._register_handlers()
        self._connect()
        self.container.spawn_managed_thread(self.run)

    def run(self):
        while True:
            for event in self._client.rtm_read():
                self.handle(event)
            eventlet.sleep(self.read_interval)

    def _register_handlers(self):
        for provider in self._providers:
            self._handlers.add(provider.handle_event)

    def _connect(self):
        self._client = SlackClient(self.token)
        self._client.server.rtm_connect()

    def handle(self, event):
        for handle_event in self._handlers:
            handle_event(event)


class RTMEventHandlerEntrypoint(Entrypoint):

    client = SlackRTMClient()

    def __init__(self, event_type=None):
        self.event_type = event_type

    def setup(self):
        self.client.register_provider(self)

    def stop(self):
        self.client.unregister_provider(self)

    def handle_event(self, event):
        if self.event_type and event.get('type') != self.event_type:
            return
        args = (event,)
        kwargs = {}
        context_data = {}
        self.container.spawn_worker(
            self, args, kwargs, context_data=context_data)


handle_event = RTMEventHandlerEntrypoint.decorator


class RTMMessageHandlerEntrypoint(RTMEventHandlerEntrypoint):

    def __init__(self, message_pattern=None):
        if message_pattern:
            self.message_pattern = re.compile(message_pattern)
        else:
            self.message_pattern = None

    def handle_event(self, event):
        if event.get('type') == EVENT_TYPE_MESSAGE:
            if self.message_pattern:
                match = self.message_pattern.match(event.get('text', ''))
                if match:
                    kwargs = match.groupdict()
                    args = () if kwargs else match.groups()
                    args = (event, event.get('text')) + args
                else:
                    return
            else:
                args = (event, event.get('text'))
                kwargs = {}
            context_data = {}
            self.container.spawn_worker(
                self, args, kwargs, context_data=context_data)


handle_message = RTMMessageHandlerEntrypoint.decorator
