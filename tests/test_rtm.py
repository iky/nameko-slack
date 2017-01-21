from eventlet import sleep
from eventlet.event import Event
from mock import call, Mock, patch
import pytest

from nameko_slack import rtm


@pytest.fixture
def tracker():
    yield Mock()


@pytest.fixture
def config():
    return {}


@pytest.fixture
def service_runner(container_factory, config):
    """
    Service runner

    Return a utility test function which runs the given service
    and sets mocked Slack client to "publish" a given set of events

    """

    def _runner(service_class, events):

        with patch('nameko_slack.rtm.SlackClient') as SlackClient:
            SlackClient.return_value.rtm_read.return_value = events
            container = container_factory(service_class, config)
            container.start()
            sleep(0.1)  # enough to handle all the test events

    return _runner


@pytest.fixture
def make_message_event():
    """ Sample message event maker
    """
    def _make(**overrides):
        event = {
            'type': 'message',
            'user': 'U11',
            'text': 'spam',
            'channel': 'D11',
            'ts': '1480798992.000002',
            'team': 'T11',
        }
        event.update(overrides)
        return event
    return _make


@pytest.fixture
def events(make_message_event):
    return [
        {'type': 'hello'},
        {'type': 'presence_change', 'presence': 'active', 'user': 'U11'},
        make_message_event(text='spam ham'),
        {'type': 'presence_change', 'presence': 'away', 'user': 'U00'},
        make_message_event(text='ham spam'),
        {},  # emtpy event, no type specified
        make_message_event(text='spam egg'),
    ]


class TestHandleEvents:

    def test_handle_any_event(self, events, service_runner, tracker):

        class Service:

            name = 'sample'

            @rtm.handle_event
            def handle_event(self, event):
                tracker.handle_event(event)

        service_runner(Service, events)

        assert (
            [call(event) for event in events] ==
            tracker.handle_event.call_args_list)

    def test_handle_event_by_type(self, events, service_runner, tracker):

        class Service:

            name = 'sample'

            @rtm.handle_event('presence_change')
            def handle_event(self, event):
                tracker.handle_event(event)

        service_runner(Service, events)

        assert (
            [
                call(event) for event in events
                if event.get('type') == 'presence_change'
            ] ==
            tracker.handle_event.call_args_list)

    def test_handle_any_message(self, events, service_runner, tracker):

        class Service:

            name = 'sample'

            @rtm.handle_message
            def handle_event(self, event, message):
                tracker.handle_event(event, message)

        service_runner(Service, events)

        assert (
            [
                call(event, event.get('text')) for event in events
                if event.get('type') == 'message'
            ] ==
            tracker.handle_event.call_args_list)

    def test_handle_message_matching_regex(
        self, make_message_event, service_runner, tracker
    ):

        class Service:

            name = 'sample'

            @rtm.handle_message('^spam')
            def handle_event(self, event, message):
                tracker.handle_event(event, message)

        events = [
            {'type': 'hello'},
            {'type': 'presence_change', 'presence': 'active', 'user': 'U11'},
            make_message_event(text='spam ham'),
            {'type': 'presence_change', 'presence': 'away', 'user': 'U00'},
            make_message_event(text='ham spam'),
            make_message_event(text='spam egg'),
            {},  # no type specified
            {'type': 'message'},  # no text of a message
        ]

        service_runner(Service, events)

        assert (
            [
                call(make_message_event(text='spam ham'), 'spam ham'),
                call(make_message_event(text='spam egg'), 'spam egg'),
            ] ==
            tracker.handle_event.call_args_list)

    def test_handle_message_with_grouping_regex(
        self, make_message_event, service_runner, tracker
    ):

        class Service:

            name = 'sample'

            @rtm.handle_message('^spam (\d+)')
            def handle_event(self, event, message, number):
                tracker.handle_event(event, message, number)

        events = [
            make_message_event(text='spam 100'),
            make_message_event(text='spam egg'),
            make_message_event(text='spam 200'),
        ]

        service_runner(Service, events)

        assert (
            [
                call(make_message_event(text='spam 100'), 'spam 100', '100'),
                call(make_message_event(text='spam 200'), 'spam 200', '200'),
            ] ==
            tracker.handle_event.call_args_list)

    def test_handle_message_with_named_group_regex(
        self, make_message_event, service_runner, tracker
    ):

        class Service:

            name = 'sample'

            @rtm.handle_message('^spam (?P<ham>\d+)(\w*)')
            def handle_event(self, event, message, ham):
                tracker.handle_event(event, message, ham=ham)

        events = [
            make_message_event(text='spam 100'),
            make_message_event(text='spam egg'),
            make_message_event(text='spam 200spam'),
        ]

        service_runner(Service, events)

        assert (
            [
                call(
                    make_message_event(text='spam 100'),
                    'spam 100',
                    ham='100'),
                call(
                    make_message_event(text='spam 200spam'),
                    'spam 200spam',
                    ham='200'),
            ] ==
            tracker.handle_event.call_args_list)

    def test_multiple_handlers(
        self, events, make_message_event, service_runner, tracker
    ):

        class Service:

            name = 'test'

            @rtm.handle_event
            def handle_all_events(self, event):
                tracker.handle_all_events(event)

            @rtm.handle_event('presence_change')
            def handle_presence_changes(self, event):
                tracker.handle_presence_changes(event)

            @rtm.handle_message
            def handle_all_messages(self, event, message):
                tracker.handle_all_messages(event, message)

            @rtm.handle_message('^ham')
            @rtm.handle_message('^spam ham')
            def handle_spam_messages(self, event, message):
                tracker.handle_spam_messages(event, message)

        service_runner(Service, events)

        assert (
            [call(event) for event in events] ==
            tracker.handle_all_events.call_args_list)

        assert (
            [
                call(event) for event in events
                if event.get('type') == 'presence_change'
            ] ==
            tracker.handle_presence_changes.call_args_list)

        assert (
            [
                call(event, event.get('text')) for event in events
                if event.get('type') == 'message'
            ] ==
            tracker.handle_all_messages.call_args_list)

        assert (
            [
                call(make_message_event(text='spam ham'), 'spam ham'),
                call(make_message_event(text='ham spam'), 'ham spam'),
            ] ==
            tracker.handle_spam_messages.call_args_list)


@patch('nameko_slack.rtm.SlackClient')
def test_handlers_do_not_block(
    SlackClient, container_factory, config, tracker
):

    work_1 = Event()
    work_2 = Event()

    class Service:

        name = 'sample'

        @rtm.handle_event
        def handle_1(self, event):
            work_1.wait()
            tracker.handle_1(event)

        @rtm.handle_event
        def handle_2(self, event):
            work_2.wait()
            tracker.handle_2(event)

    events = [{'spam': 'ham'}]

    def rtm_read():
        if events:
            return [events.pop(0)]
        else:
            return []

    SlackClient.return_value.rtm_read.side_effect = rtm_read
    container = container_factory(Service, config)
    container.start()

    try:

        # both handlers are still working
        assert (
            [] ==
            tracker.handle_1.call_args_list)
        assert (
            [] ==
            tracker.handle_2.call_args_list)

        # finish work of the second handler
        work_2.send()
        sleep(0.1)

        # second handler is done
        assert (
            [] ==
            tracker.handle_1.call_args_list)
        assert (
            [call({'spam': 'ham'})] ==
            tracker.handle_2.call_args_list)

        # finish work of the first handler
        work_1.send()
        sleep(0.1)

        # first handler is done
        assert (
            [call({'spam': 'ham'})] ==
            tracker.handle_1.call_args_list)
        assert (
            [call({'spam': 'ham'})] ==
            tracker.handle_2.call_args_list)
    finally:
        if not work_1.ready():
            work_1.send()
        if not work_2.ready():
            work_2.send()

    container.stop()
