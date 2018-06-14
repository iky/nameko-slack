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


Run multiple RTM bots:

.. code:: yaml

    # config.yml

    SLACK:
        BOTS:
            alice: ${ALICE_BOT_TOKEN}
            bob: ${BOB_BOT_TOKEN}

.. code:: python

    # service.py
    
    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_message(bot_name='alice')
        def listen_as_alice(self, event, message):
            pass

        @rtm.handle_message(bot_name='bob')
        def listen_as_bob(self, event, message):
            pass

.. code::

    $ ALICE_BOT_TOKEN=xoxb-aaa-111 BOB_BOT_TOKEN=xoxb-bbb-222 nameko run --config ./config.yaml service
    starting services: some-service



WEB API Client
==============

A simple dependency provider wrapping `Slack WEB API client`_.


.. _Slack WEB API client: http://slackapi.github.io/python-slackclient/basic_usage.html#sending-a-message


Usage
-----

The dependency provider uses the same config key as the RTM extension:

.. code:: yaml

    # config.yml

    AMQP_URI: 'pyamqp://guest:guest@localhost'
    SLACK:
        TOKEN: ${SLACK_BOT_TOKEN}

.. code:: python

    # service.py

    from nameko.rpc import rpc
    from nameko_slack import web


    class Service:

        name = 'some-service'

        slack = web.Slack()

        @rpc
        def say_hello(self, name):
            self.slack.api_call(
                'chat.postMessage',
                channel="#nameko",
                text="Hello from Nameko! :tada:")


You can also use multiple bots:

.. code:: yaml

    # config.yml

    AMQP_URI: 'pyamqp://guest:guest@localhost'
    SLACK:
        BOTS:
            alice: ${ALICE_BOT_TOKEN}
            bob: ${BOB_BOT_TOKEN}

.. code:: python

    # service.py

    from nameko.rpc import rpc
    from nameko_slack import web


    class Service:

        name = 'some-service'

        alice = web.Slack('alice')
        bob = web.Slack('bob')

        @rpc
        def say_hello(self):
            self.alice.api_call(
                'chat.postMessage',
                channel="#nameko",
                text="Hello from Alice! :tada:")
            self.bob.api_call(
                'chat.postMessage',
                channel="#nameko",
                text="Hello from Bob! :tada:")
