.. image:: https://travis-ci.org/iky/nameko-slack.svg?branch=master
    :target: https://travis-ci.org/iky/nameko-slack


===========================
Slack Extensions for Nameko
===========================

`Nameko`_ extension for interaction with `Slack APIs`_. Uses
`Slack Developer Kit for Python`_.

.. _Nameko: http://nameko.readthedocs.org
.. _Slack APIs: https://api.slack.com
.. _Slack Developer Kit for Python: http://slackapi.github.io/python-slackclient


Real Time Messaging Client
==========================

The RTM extension is a Websocket client for Slack's `Real Time Messaging API`_
that allows you to receive events from Slack in real time. The ``rtm`` module
contains two Nameko entrypoints for handling such events - ``handle_event`` and
``handle_message``.

.. _Real Time Messaging API: https://api.slack.com/rtm


Usage
-----

Provide Slack bot API token in your Nameko service config file:

.. code:: yaml

    # config.yml

    SLACK:
        TOKEN: "xoxb-abc-1232"

Or using environment variable within your config:

.. code:: yaml

    # config.yml

    SLACK:
        TOKEN: ${SLACK_BOT_TOKEN}

Define your service with an entrypoint which will listen for and fire on any
event coming from Slack:

.. code:: python

    # service.py

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_event
        def on_any_event(self, event):
            print(event)

Finally, run the service:

.. code::

    $ SLACK_BOT_TOKEN=xoxb-abc-1232 nameko run --config ./config.yaml service
    starting services: some-service
    {'type': 'hello'}
    {'type': 'presence_change', 'user': 'ABCDE1234', 'presence': 'active'}
    {'type': 'user_typing', 'user': 'ABCDE1234', 'channel': 'ABCDE1234'}
    {'type': 'message', 'text': 'spam', 'channel': 'ABCDE1234', 'user': 'ABC...
    {'type': 'presence_change', 'user': 'ABCDE1234', 'presence': 'active'}
    ...


More Examples
-------------

Listen for events of a particular type:

.. code:: python

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_event('presence_change')
        def on_presence_change(self, event):
            pass

Listen for any message type event:

.. code:: python

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_message
        def on_any_message(self, event, message):
            pass

Use regular expressions to fire on matching messages only:

.. code:: python

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_message('^spam')
        def on_message_starting_with(self, event, message):
            pass

Parse message and pass matching groups as positional or named arguments
to the entrypoint:

.. code:: python

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_message('^spam (\w*)')
        def on_spam(self, event, message, egg):
            pass

        @rtm.handle_message('^egg (?P<ham>\w+)')
        def on_egg(self, event, message, ham=None):
            pass

Respond back to the channel by returning a string in the message handling
entrypoint:

.. code:: python

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_message
        def sure(self, event, message):
            return 'sure, {}'.format(message)


WEB API Client
==============

A very simple dependency provider wrapping the Slack WEB API client.


Usage
-----

The dependency provider uses the same config key as the Real Time Messaging Client entrypoint:

.. code:: yaml

    # config.yml

    SLACK:
        TOKEN: ${SLACK_BOT_TOKEN}

.. code:: python

    # service.py

    import calendar
    from nameko_slack import rtm, web


    months = [m for m in calendar.month_name if m]


    class Service:

        name = 'some-service'

        slack = web.Slack()

        @rtm.handle_message(".*give.*{} report.*".format()
        def handle_message(self, event, message):
            self.slack.api_call('chat.postMessage')
            d
            print(event)

re.match(".*give.*(?P<month_name>{}) report.*".format('|'.join([m for m in calendar.month_name if m])), 'Hi, can you please give me a July report? Thanks
    ...: ').groupdict()
