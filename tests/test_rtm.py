# -*- coding: utf-8 -*-
import pytest
from eventlet import sleep
from eventlet.event import Event
from mock import Mock, call, patch
from nameko.exceptions import ConfigurationError
from nameko.testing.utils import get_extension
from nameko_slack import constants, rtm


def test_client_manager_setup_missing_config_key():

    config = {}

    client_manager = rtm.SlackRTMClientManager()
    client_manager.container = Mock(config=config)

    with pytest.raises(ConfigurationError) as exc:
        client_manager.setup()

    assert str(exc.value) == "`SLACK` config key not found"


def test_client_manager_setup_missing_mandatory_connection_keys():

    config = {"SLACK": {}}

    client_manager = rtm.SlackRTMClientManager()
    client_manager.container = Mock(config=config)

    with pytest.raises(ConfigurationError) as exc:
        client_manager.setup()

    assert str(exc.value) == "At least one token must be provided in `SLACK` config"


@pytest.mark.parametrize(
    "config",
    (
        {"SLACK": {"TOKEN": "abc-123"}},
        {"SLACK": {"BOTS": {constants.DEFAULT_BOT_NAME: "abc-123"}}},
    ),
)
@patch("nameko_slack.rtm.SlackClient")
def test_client_manager_setup_with_default_bot_token(mocked_slack_client, config):

    client_manager = rtm.SlackRTMClientManager()
    client_manager.container = Mock(config=config)

    client_manager.setup()

    assert constants.DEFAULT_BOT_NAME in client_manager.clients
    assert (
        client_manager.clients[constants.DEFAULT_BOT_NAME]
        == mocked_slack_client.return_value
    )
    assert mocked_slack_client.call_args == call("abc-123")


@patch("nameko_slack.rtm.SlackClient")
def test_client_manager_setup_with_multiple_bot_tokens(mocked_slack_client):

    config = {"SLACK": {"BOTS": {"spam": "abc-123", "ham": "def-456"}}}

    client_manager = rtm.SlackRTMClientManager()
    client_manager.container = Mock(config=config)

    client_manager.setup()

    assert "spam" in client_manager.clients
    assert "ham" in client_manager.clients
    assert client_manager.clients["spam"] == mocked_slack_client.return_value
    assert client_manager.clients["ham"] == mocked_slack_client.return_value

    assert call("abc-123") in mocked_slack_client.call_args_list
    assert call("def-456") in mocked_slack_client.call_args_list


@pytest.fixture
def tracker():
    yield Mock()


@pytest.fixture
def service_runner(container_factory, config):
    """
    Service runner

    Return a utility test function which runs the given service
    and sets mocked Slack client to "publish" a given set of events

    """

    def _runner(service_class, events):

        with patch("nameko_slack.rtm.SlackClient") as SlackClient:
            SlackClient.return_value.rtm_read.return_value = events
            container = container_factory(service_class, config)
            container.start()
            sleep(0.1)  # enough to handle all the test events

        # return reply calls
        return SlackClient.return_value.rtm_send_message.call_args_list

    return _runner


@pytest.fixture
def make_message_event():
    """ Sample message event maker
    """

    def _make(**overrides):
        event = {
            "type": "message",
            "user": "U11",
            "text": "spam",
            "channel": "D11",
            "ts": "1480798992.000002",
            "team": "T11",
        }
        event.update(overrides)
        return event

    return _make


@pytest.fixture
def events(make_message_event):
    return [
        {"type": "hello"},
        {"type": "presence_change", "presence": "active", "user": "U11"},
        make_message_event(text="spam ham"),
        {"type": "presence_change", "presence": "away", "user": "U00"},
        make_message_event(text="ham spam"),
        {},  # emtpy event, no type specified
        make_message_event(text="spam egg"),
    ]


class TestHandleEvents:
    def test_handle_any_event(self, events, service_runner, tracker):
        class Service:

            name = "sample"

            @rtm.handle_event
            def handle_event(self, event):
                tracker.handle_event(event)

        service_runner(Service, events)

        assert tracker.handle_event.call_args_list == [call(event) for event in events]

    def test_handle_event_by_type(self, events, service_runner, tracker):
        class Service:

            name = "sample"

            @rtm.handle_event("presence_change")
            def handle_event(self, event):
                tracker.handle_event(event)

        service_runner(Service, events)

        assert tracker.handle_event.call_args_list == [
            call(event) for event in events if event.get("type") == "presence_change"
        ]

    def test_handle_any_message(self, events, service_runner, tracker):
        class Service:

            name = "sample"

            @rtm.handle_message
            def handle_event(self, event, message):
                tracker.handle_event(event, message)

        service_runner(Service, events)

        assert tracker.handle_event.call_args_list == [
            call(event, event.get("text"))
            for event in events
            if event.get("type") == "message"
        ]

    def test_handle_message_matching_regex(
        self, make_message_event, service_runner, tracker
    ):
        class Service:

            name = "sample"

            @rtm.handle_message("^spam")
            def handle_event(self, event, message):
                tracker.handle_event(event, message)

        events = [
            {"type": "hello"},
            {"type": "presence_change", "presence": "active", "user": "U11"},
            make_message_event(text="spam ham"),
            {"type": "presence_change", "presence": "away", "user": "U00"},
            make_message_event(text="ham spam"),
            make_message_event(text="spam egg"),
            {},  # no type specified
            {"type": "message"},  # no text of a message
        ]

        service_runner(Service, events)

        assert tracker.handle_event.call_args_list == [
            call(make_message_event(text="spam ham"), "spam ham"),
            call(make_message_event(text="spam egg"), "spam egg"),
        ]

    def test_handle_message_with_grouping_regex(
        self, make_message_event, service_runner, tracker
    ):
        class Service:

            name = "sample"

            @rtm.handle_message("^spam (\\d+)")
            def handle_event(self, event, message, number):
                tracker.handle_event(event, message, number)

        events = [
            make_message_event(text="spam 100"),
            make_message_event(text="spam egg"),
            make_message_event(text="spam 200"),
        ]

        service_runner(Service, events)

        assert tracker.handle_event.call_args_list == [
            call(make_message_event(text="spam 100"), "spam 100", "100"),
            call(make_message_event(text="spam 200"), "spam 200", "200"),
        ]

    def test_handle_message_with_named_group_regex(
        self, make_message_event, service_runner, tracker
    ):
        class Service:

            name = "sample"

            @rtm.handle_message("^spam (?P<ham>\\d+)(\\w*)")
            def handle_event(self, event, message, ham):
                tracker.handle_event(event, message, ham=ham)

        events = [
            make_message_event(text="spam 100"),
            make_message_event(text="spam egg"),
            make_message_event(text="spam 200spam"),
        ]

        service_runner(Service, events)

        assert tracker.handle_event.call_args_list == [
            call(make_message_event(text="spam 100"), "spam 100", ham="100"),
            call(make_message_event(text="spam 200spam"), "spam 200spam", ham="200"),
        ]

    def test_multiple_handlers(
        self, events, make_message_event, service_runner, tracker
    ):
        class Service:

            name = "test"

            @rtm.handle_event
            def handle_all_events(self, event):
                tracker.handle_all_events(event)

            @rtm.handle_event("presence_change")
            def handle_presence_changes(self, event):
                tracker.handle_presence_changes(event)

            @rtm.handle_message
            def handle_all_messages(self, event, message):
                tracker.handle_all_messages(event, message)

            @rtm.handle_message("^ham")
            @rtm.handle_message("^spam ham")
            def handle_spam_messages(self, event, message):
                tracker.handle_spam_messages(event, message)

        service_runner(Service, events)

        assert tracker.handle_all_events.call_args_list == [
            call(event) for event in events
        ]

        assert tracker.handle_presence_changes.call_args_list == [
            call(event) for event in events if event.get("type") == "presence_change"
        ]

        assert tracker.handle_all_messages.call_args_list == [
            call(event, event.get("text"))
            for event in events
            if event.get("type") == "message"
        ]

        assert tracker.handle_spam_messages.call_args_list == [
            call(make_message_event(text="spam ham"), "spam ham"),
            call(make_message_event(text="ham spam"), "ham spam"),
        ]


class TestMultipleBotAccounts:
    @pytest.fixture
    def config(self):
        return {constants.CONFIG_KEY: {"BOTS": {"Alice": "aaa-111", "Bob": "bbb-222"}}}

    @pytest.fixture
    def make_client(self):
        def make(bot_name, token, events):
            client = Mock(bot_name=bot_name, token=token)
            client.rtm_read.return_value = events
            return client

        return make

    @pytest.fixture
    def service_runner(self, container_factory, config):
        def _runner(service_class, clients):

            clients_by_token = {client.token: client for client in clients}

            with patch("nameko_slack.rtm.SlackClient") as SlackClient:
                SlackClient.side_effect = lambda token: clients_by_token[token]
                container = container_factory(service_class, config)
                container.start()
                sleep(0.1)  # enough to handle all the test events

        return _runner

    def test_multiple_handlers(
        self, events, make_client, make_message_event, service_runner, tracker
    ):
        class Service:

            name = "test"

            @rtm.handle_event(bot_name="Alice")
            def handle_all_events(self, event):
                tracker.alice.handle_all_events(event)

            @rtm.handle_event("presence_change", bot_name="Bob")
            def handle_presence_changes(self, event):
                tracker.bob.handle_presence_changes(event)

            @rtm.handle_message(bot_name="Alice")
            def handle_all_messages(self, event, message):
                tracker.alice.handle_all_messages(event, message)

            @rtm.handle_message("^ham", bot_name="Alice")
            def handle_ham_messages(self, event, message):
                tracker.alice.handle_ham_messages(event, message)

            @rtm.handle_message("^spam", bot_name="Bob")
            def handle_spam_messages(self, event, message):
                tracker.bob.handle_spam_messages(event, message)

            @rtm.handle_message("^ham", bot_name="Alice")
            @rtm.handle_message("^spam", bot_name="Bob")
            def handle_ham_and_spam_messages(self, event, message):
                tracker.handle_spam_and_ham_messages(message)

        alices_events = [
            {"type": "hello"},
            make_message_event(text="spam ham"),
            make_message_event(text="spam egg"),
            {"type": "presence_change", "presence": "active", "user": "A11"},
            {"type": "presence_change", "presence": "away", "user": "A00"},
            make_message_event(text="ham spam"),
        ]

        bobs_events = [
            {"type": "hello"},
            {"type": "presence_change", "presence": "active", "user": "B11"},
            make_message_event(text="spam ham"),
            {"type": "presence_change", "presence": "away", "user": "B00"},
            make_message_event(text="ham spam"),
            make_message_event(text="spam egg"),
        ]

        alice = make_client("Alice", "aaa-111", alices_events)
        bob = make_client("Bob", "bbb-222", bobs_events)

        service_runner(Service, [alice, bob])

        assert tracker.alice.handle_all_events.call_args_list == [
            call(event) for event in alices_events
        ]

        assert tracker.bob.handle_presence_changes.call_args_list == [
            call(event)
            for event in bobs_events
            if event.get("type") == "presence_change"
        ]

        assert tracker.alice.handle_all_messages.call_args_list == [
            call(event, event.get("text"))
            for event in alices_events
            if event.get("type") == "message"
        ]

        assert tracker.alice.handle_ham_messages.call_args_list == [
            call(make_message_event(text="ham spam"), "ham spam")
        ]

        assert tracker.bob.handle_spam_messages.call_args_list == [
            call(make_message_event(text="spam ham"), "spam ham"),
            call(make_message_event(text="spam egg"), "spam egg"),
        ]

        call_args_list = tracker.handle_spam_and_ham_messages.call_args_list
        messages = [message for args, _ in call_args_list for message in args]
        assert sorted(messages) == ["ham spam", "spam egg", "spam ham"]


def test_replies_on_handle_message(events, service_runner):
    class Service:

        name = "sample"

        @rtm.handle_message
        def handle_message(self, event, message):
            return "sure, {}".format(message)

    reply_calls = service_runner(Service, events)

    assert reply_calls == [
        call("D11", "sure, spam ham"),
        call("D11", "sure, ham spam"),
        call("D11", "sure, spam egg"),
    ]


@patch("nameko_slack.rtm.SlackClient")
def test_handlers_do_not_block(SlackClient, container_factory, config, tracker):

    work_1 = Event()
    work_2 = Event()

    class Service:

        name = "sample"

        @rtm.handle_event
        def handle_1(self, event):
            work_1.wait()
            tracker.handle_1(event)

        @rtm.handle_event
        def handle_2(self, event):
            work_2.wait()
            tracker.handle_2(event)

    events = [{"spam": "ham"}]

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
        assert tracker.handle_1.call_args_list == []
        assert tracker.handle_2.call_args_list == []

        # finish work of the second handler
        work_2.send()
        sleep(0.1)

        # second handler is done
        assert tracker.handle_1.call_args_list == []
        assert tracker.handle_2.call_args_list == [call({"spam": "ham"})]

        # finish work of the first handler
        work_1.send()
        sleep(0.1)

        # first handler is done
        assert tracker.handle_1.call_args_list == [call({"spam": "ham"})]
        assert tracker.handle_2.call_args_list == [call({"spam": "ham"})]
    finally:
        if not work_1.ready():
            work_1.send()
        if not work_2.ready():
            work_2.send()


@patch.object(rtm.RTMEventHandlerEntrypoint, "clients")
def test_entrypoints_lifecycle(clients, container_factory, config):
    class Service:

        name = "sample"

        @rtm.handle_event
        def handle_event(self, event):
            pass

        @rtm.handle_message
        def handle_message(self, event, message):
            pass

    container = container_factory(Service, config)

    event_handler = get_extension(container, rtm.RTMEventHandlerEntrypoint)
    message_handler = get_extension(container, rtm.RTMMessageHandlerEntrypoint)

    container.start()
    assert call(event_handler) in clients.register_provider.mock_calls
    assert call(message_handler) in clients.register_provider.mock_calls

    container.stop()
    assert call(event_handler) in clients.unregister_provider.mock_calls
    assert call(message_handler) in clients.unregister_provider.mock_calls


def test_expected_exceptions(container_factory, config):
    class Boom(Exception):
        pass

    class Service:

        name = "sample"

        @rtm.handle_event(expected_exceptions=Boom)
        def handle_event(self, event):
            pass

        @rtm.handle_message(expected_exceptions=Boom)
        def handle_message(self, event, message):
            pass

    container = container_factory(Service, config)

    event_handler = get_extension(container, rtm.RTMEventHandlerEntrypoint)
    assert event_handler.expected_exceptions == Boom

    message_handler = get_extension(container, rtm.RTMMessageHandlerEntrypoint)
    assert message_handler.expected_exceptions == Boom


def test_sensitive_arguments(container_factory, config):
    class Boom(Exception):
        pass

    class Service:

        name = "sample"

        @rtm.handle_event(sensitive_arguments="event.user")
        def handle_event(self, event):
            pass

        @rtm.handle_message(sensitive_arguments="event.user")
        def handle_message(self, event, message):
            pass

    container = container_factory(Service, config)

    event_handler = get_extension(container, rtm.RTMEventHandlerEntrypoint)
    assert event_handler.sensitive_arguments == "event.user"

    message_handler = get_extension(container, rtm.RTMMessageHandlerEntrypoint)
    assert message_handler.sensitive_arguments == "event.user"
