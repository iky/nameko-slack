===========================
Slack Extensions for Nameko
===========================

`Nameko`_ extension for interaction with `Slack APIs`_.

.. _Nameko: http://nameko.readthedocs.org
.. _Slack APIs: https://api.slack.com


Real Time Messaging Client
==========================

The RTM extension is a Websocket client for Sack's `Real Time Messaging API`_
that allows you to receive events from Slack in real time.

.. _Real Time Messaging API: https://api.slack.com/rtm


Listen for and fire entrypoint on any event coming from Slack::

    from nameko_slack import rtm

    class Service:

        name = 'some-service'

        @rtm.handle_event
        def on_any_event(self, event):
            pass

Listen for and fire entrypoint on event of a particular type::

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
