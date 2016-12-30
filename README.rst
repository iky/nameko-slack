===========================
Slack Extensions for Nameko
===========================

`Nameko`_ extension for interaction with `Slack APIs`_. Uses
`Slack Developer Kit for Python`_

.. _Nameko: http://nameko.readthedocs.org
.. _Slack APIs: https://api.slack.com
.. _Slack Developer Kit for Python: http://slackapi.github.io/python-slackclient


Real Time Messaging Client
==========================

The RTM extension is a Websocket client for Sack's `Real Time Messaging API`_
that allows you to receive events from Slack in real time. The `rtm` module
contains for handling such events.

.. _Real Time Messaging API: https://api.slack.com/rtm


Provide Slack bot API token in your Nameko service config file::

    # config.yml

    SLACK:
        TOKEN: "xoxb-abc-1232"

Or using environment variable within your config::

    # config.yml

    SLACK:
        TOKEN: ${SLACK_BOT_TOKEN}

nameko run --config ./foobar.yaml

Define your service with an entrypoint which will listen for and fire on any
event coming from Slack::

    # service.py

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_event
        def on_any_event(self, event):
            print(event)

Finally, run the service::

    $ SLACK_BOT_TOKEN=xoxb-abc-1232 nameko run --config ./config.yaml service

Listen for events of a particular type::

    @rtm.handle_event(rtm.Event.PRESENCE_CHANGE)
    def on_presence_change(self, event):
        pass

Listen for any message type event::

    @rtm.handle_message
    def on_any_message(self, event, message):
        pass

Use regular expressions to fire on matching messages only::

    @rtm.handle_message('^spam')
    def on_message_starting_with(self, event, message):
        pass

Parse message and pass ``args`` or ``kwargs`` straight to entrypoint::

    @rtm.handle_message('^spam (\w*)'):
    def on_message(self, event, message, egg):
        pass

    @rtm.handle_message('^spam (?P<ham>\w+)'):
    def on_message(self, event, message, ham=None):
        pass
