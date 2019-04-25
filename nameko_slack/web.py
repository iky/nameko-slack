# -*- coding: utf-8 -*-
from nameko.exceptions import ConfigurationError
from nameko.extensions import DependencyProvider
from slackclient import SlackClient

from nameko_slack import constants


class Slack(DependencyProvider):
    def __init__(self, bot_name=None):
        self.bot_name = bot_name
        self.client = None

    def setup(self):

        try:
            config = self.container.config[constants.CONFIG_KEY]
        except KeyError:
            raise ConfigurationError(
                "`{}` config key not found".format(constants.CONFIG_KEY)
            )

        if self.bot_name:
            try:
                token = config["BOTS"][self.bot_name]
            except KeyError:
                raise ConfigurationError(
                    "No token for `{}` bot in `{}` config".format(
                        self.bot_name, constants.CONFIG_KEY
                    )
                )
        else:
            token = config.get("BOTS", {}).get(
                constants.DEFAULT_BOT_NAME
            ) or config.get("TOKEN")
        if not token:
            raise ConfigurationError(
                "No token provided by `{}` config".format(constants.CONFIG_KEY)
            )

        self.client = SlackClient(token)

    def get_dependency(self, worker_ctx):
        return self.client
