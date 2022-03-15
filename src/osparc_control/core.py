from collections import deque
from queue import Queue
from threading import Thread
from time import sleep
from typing import Any, Dict, Optional, Tuple, Union
from uuid import getnode, uuid4

from pydantic import ValidationError
from tenacity import RetryError, Retrying
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

from osparc_control.transport.zeromq import ZeroMQTransport

from .errors import NoReplyException
from .models import (
    CommandManifest,
    CommandReply,
    CommandRequest,
    CommnadType,
    RequestsTracker,
    TrackedRequest,
)
from .transport.base_transport import SenderReceiverPair

WAIT_FOR_MESSAGES: float = 0.01
WAIT_BETWEEN_CHECKS: float = 0.1


def _generate_request_id() -> str:
    unique_hardware_id: int = getnode()
    return f"{unique_hardware_id}_{uuid4()}"


def _get_sender_receiver_pair(
    listen_port: int, remote_host: str, remote_port: int
) -> SenderReceiverPair:
    sender = ZeroMQTransport(
        listen_port=listen_port, remote_host=remote_host, remote_port=remote_port
    )
    receiver = ZeroMQTransport(
        listen_port=listen_port, remote_host=remote_host, remote_port=remote_port
    )
    return SenderReceiverPair(sender=sender, receiver=receiver)


class SomeEntryPoint:
    def __init__(
        self, remote_host: str, remote_port: int = 7426, listen_port: int = 7426
    ) -> None:

        self._sender_receiver_pair: SenderReceiverPair = _get_sender_receiver_pair(
            remote_host=remote_host, remote_port=remote_port, listen_port=listen_port
        )

        self._request_tracker: RequestsTracker = {}
        # TODO: below must be protected by a lock
        self._incoming_request_tracker = deque()

        self._out_queue: Queue = Queue()

        # sending and receving threads
        self._sender_thread: Thread = Thread(target=self._sender_worker)
        self._receiver_thread: Thread = Thread(target=self._receiver_worker)
        self._continue: bool = True

    def _sender_worker(self) -> None:
        self._sender_receiver_pair.sender_init()

        while self._continue:
            message = self._out_queue.get()
            message: Optional[Union[CommandRequest, CommandReply]] = message
            if message is None:
                # exit worker
                break

            print("Message to deliver", message)
            # send message
            self._sender_receiver_pair.send_bytes(message.to_bytes())

        self._sender_receiver_pair.sender_cleanup()

    def _receiver_worker(self) -> None:
        self._sender_receiver_pair.receiver_init()

        while self._continue:
            # this is blocking should be under timeout block
            response: Optional[bytes] = self._sender_receiver_pair.receive_bytes()
            if response is None:
                # no messages available
                continue

            # NOTE: pydantic does not support polymorphism
            # SEE https://github.com/samuelcolvin/pydantic/issues/503

            # check if is CommandRequest
            try:
                command_request = CommandRequest.from_bytes(response)
                assert command_request
                self._incoming_request_tracker.append(command_request)
            except ValidationError:
                pass

            # check if is CommandReply
            try:
                command_reply = CommandReply.from_bytes(response)
                assert command_reply
                tracked_request: TrackedRequest = self._request_tracker[
                    command_reply.reply_id
                ]
                tracked_request.reply = command_reply
            except ValidationError:
                pass

            sleep(WAIT_FOR_MESSAGES)

        self._sender_receiver_pair.receiver_cleanup()

    def _enqueue_call(
        self,
        manifest: CommandManifest,
        params: Optional[Dict[str, Any]],
        expected_command_type: CommnadType,
    ) -> CommandRequest:
        """validates and enqueues the call for delivery to remote"""
        request = CommandRequest.from_manifest(
            manifest=manifest, request_id=_generate_request_id(), params=params
        )

        if request.command_type != expected_command_type:
            raise RuntimeError(
                f"Request {request} was expected to have command_type={expected_command_type}"
            )

        self._request_tracker[request.request_id] = TrackedRequest(
            request=request, reply=None
        )

        self._out_queue.put(request)

        return request

    def start_background_sync(self) -> None:
        """starts workers handling data transfer"""
        self._continue = True
        self._sender_thread.start()
        self._receiver_thread.start()

    def stop_background_sync(self) -> None:
        """stops workers handling data transfer"""
        self._continue = False

        # stopping workers
        self._out_queue.put(None)

        self._sender_thread.join()
        self._receiver_thread.join()

    def request_and_forget(
        self, manifest: CommandManifest, params: Optional[Dict[str, Any]] = None
    ) -> None:
        """No reply will be provided by remote side for this command"""
        self._enqueue_call(manifest, params, CommnadType.WITHOUT_REPLY)

    def request_and_check(
        self, manifest: CommandManifest, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        returns a `request_id` to be used with `check_for_reply` to monitor
        if a reply to the request was returned.
        """
        request = self._enqueue_call(manifest, params, CommnadType.WITH_REPLAY)
        return request.request_id

    def check_for_reply(self, request_id: str) -> Tuple[bool, Optional[Any]]:
        """
        Checks if a reply to for the request_id provided by `request_and_check`
        is available.

        returns a tuple where:
        - first entry is True if the reply to the request was returned
        - second element is the actual returned value of the reply
        """
        tracked_request: Optional[TrackedRequest] = self._request_tracker.get(
            request_id, None
        )
        if tracked_request is None:
            return False, None

        # check for the correct type of request
        if not tracked_request.request.command_type != CommnadType.WAIT_FOR_REPLY:
            raise RuntimeError(
                (
                    f"Request {tracked_request.request} not expect a "
                    f"reply, found reply {tracked_request.reply}"
                )
            )

        # check if reply was received
        if tracked_request.reply is None:
            return False, None

        return True, tracked_request.reply.payload

    def request_and_wait(
        self,
        manifest: CommandManifest,
        timeout: float,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Requests and awaits for the response from remote.
        A timeout for this function is required. If the timeout is reached `None` will
        be returned.
        """
        request = self._enqueue_call(manifest, params, CommnadType.WAIT_FOR_REPLY)

        try:
            for attempt in Retrying(
                stop=stop_after_delay(timeout), wait=wait_fixed(WAIT_BETWEEN_CHECKS)
            ):
                with attempt:
                    reply_received, result = self.check_for_reply(request.request_id)
                    if not reply_received:
                        raise NoReplyException()

                    return result
        except RetryError:
            return None

    def get_incoming_request(self) -> Optional[CommandRequest]:
        """will try to fetch an incoming request, returns None if nothing is present"""
        try:
            return self._incoming_request_tracker.pop()
        except IndexError:
            return None

    def reply_to_command(self, request_id: str, payload: Any) -> None:
        """provide the reply back to a command"""
        self._out_queue.put(CommandReply(reply_id=request_id, payload=payload))
