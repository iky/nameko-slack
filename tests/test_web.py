# -*- coding: utf-8 -*-
import pytest
from mock import Mock
from nameko.containers import ServiceContainer
from nameko.exceptions import ConfigurationError
from nameko.testing.services import dummy
from nameko.testing.utils import get_extension
from nameko_slack import constants
from nameko_slack.web import Slack


@pytest.fixture
def make_slack_provider(config):

    containers = []
    default_config = config

    def factory(config=None, bot_name=None):

        class Service(object):

            name = "service"

            slack_api = Slack(bot_name)

            @dummy
            def dummy(self):
                pass

        container = ServiceContainer(Service, config or default_config)
        containers.append(container)

        return get_extension(container, Slack)

    yield factory

    del containers[:]


def test_setup_main_config_key_missing(config, make_slack_provider):

    config.pop(constants.CONFIG_KEY)

    slack_provider = make_slack_provider()

    with pytest.raises(ConfigurationError) as exc:
        slack_provider.setup()

    assert str(exc.value) == '`SLACK` config key not found'


def test_setup_default_bot_token_missing(config, make_slack_provider):

    config[constants.CONFIG_KEY] = {}

    slack_provider = make_slack_provider(config)

    with pytest.raises(ConfigurationError) as exc:
        slack_provider.setup()

    assert str(exc.value) == 'No token provided by `SLACK` config'


def test_setup_named_bot_token__missing(config, make_slack_provider):

    config[constants.CONFIG_KEY] = {'BOTS': {'Bob': 'bbb-222'}}

    slack_provider = make_slack_provider(config, 'Alice')

    with pytest.raises(ConfigurationError) as exc:
        slack_provider.setup()

    assert str(exc.value) == 'No token for `Alice` bot in `SLACK` config'


@pytest.mark.parametrize(
    ('slack_config', 'bot_name', 'expected_token'),
    (
        (
            {'TOKEN': 'xxx-000'},
            None,
            'xxx-000',
        ),
        (
            {
                'TOKEN': 'xxx-000',
                'BOTS': {'Alice': 'aaa-111', 'Bob': 'bbb-222'},
            },
            None,
            'xxx-000',
        ),
        (
            {
                'BOTS': {
                    'Alice': 'aaa-111',
                    'Bob': 'bbb-222',
                    constants.DEFAULT_BOT_NAME: 'xxx-000'
                },
            },
            None,
            'xxx-000',
        ),
        (
            {
                'TOKEN': 'xxx-000',
                'BOTS': {'Alice': 'aaa-111', 'Bob': 'bbb-222'},
            },
            'Alice',
            'aaa-111',
        ),
    )
)
def test_setup(make_slack_provider, slack_config, bot_name, expected_token):

    config = {constants.CONFIG_KEY: slack_config}

    slack_provider = make_slack_provider(config, bot_name)
    slack_provider.setup()

    assert slack_provider.client.token == expected_token


def test_get_dependency(config, make_slack_provider):
    slack_provider = make_slack_provider()
    slack_provider.setup()
    worker_ctx = Mock()
    assert (
        slack_provider.get_dependency(worker_ctx) ==
        slack_provider.client)
