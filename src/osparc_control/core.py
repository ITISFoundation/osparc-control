from collections import deque
from queue import Queue, Empty
from threading import Thread
from time import sleep
from typing import Any, Dict, Optional, Tuple, Union, List
from uuid import getnode, uuid4

from pydantic import ValidationError
from tenacity import RetryError, Retrying
from tenacity.stop import stop_after_delay
from tenacity.wait import wait_fixed

from osparc_control.transport.zeromq import ZeroMQTransport

from .errors import (
    NoReplyException,
    CommnadNotAcceptedException,
    NoCommandReceivedArrivedException,
)
from .models import (
    CommandReceived,
    CommandManifest,
    CommandReply,
    CommandRequest,
    CommnadType,
    RequestsTracker,
    TrackedRequest,
)
from .transport.base_transport import SenderReceiverPair


_MINUTE: float = 60.0

WAIT_FOR_MESSAGES: float = 0.01
WAIT_BETWEEN_CHECKS: float = 0.1
# NOTE: this effectively limits the time between when
# the two remote sides can start to communicate
WAIT_FOR_RECEIVED: float = 1 * _MINUTE

DEFAULT_LISTEN_PORT: int = 7426


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


class Engine:
    def __init__(
        self,
        remote_host: str,
        exposed_interface: List[CommandManifest],
        remote_port: int = DEFAULT_LISTEN_PORT,
        listen_port: int = DEFAULT_LISTEN_PORT,
    ) -> None:

        self._sender_receiver_pair: SenderReceiverPair = _get_sender_receiver_pair(
            remote_host=remote_host, remote_port=remote_port, listen_port=listen_port
        )

        def _process_manifest(manifest: CommandManifest) -> CommandManifest:
            manifest._remapped_params = {x.name: x for x in manifest.params}
            return manifest

        # map by action name for
        self._exposed_interface: Dict[str, CommandManifest] = {
            x.action: _process_manifest(x) for x in exposed_interface
        }
        if len(self._exposed_interface) != len(exposed_interface):
            raise ValueError(
                (
                    f"Provided exposed_interface={exposed_interface} "
                    "contains CommandManifest with same action name."
                )
            )

        self._request_tracker: RequestsTracker = {}
        # NOTE: deque is thread safe only when used with appends and pops
        self._incoming_request_tracker = deque()

        self._out_queue: Queue = Queue()
        self._incoming_command_queue: Queue = Queue()

        # sending and receiving threads
        self._sender_thread: Thread = Thread(target=self._sender_worker, daemon=True)
        self._receiver_thread: Thread = Thread(
            target=self._receiver_worker, daemon=True
        )
        self._continue: bool = True

    def _sender_worker(self) -> None:
        self._sender_receiver_pair.sender_init()

        while self._continue:
            message = self._out_queue.get()
            message: Optional[Union[CommandRequest, CommandReply]] = message
            if message is None:
                # exit worker
                break

            # send message
            self._sender_receiver_pair.send_bytes(message.to_bytes())

        self._sender_receiver_pair.sender_cleanup()

    def _handle_command_request(self, response: bytes) -> None:
        command_request: Optional[CommandRequest] = CommandRequest.from_bytes(response)
        assert command_request

        def _refuse_and_return(error_message: str) -> None:
            self._out_queue.put(
                CommandReceived(
                    request_id=command_request.request_id,
                    accepted=False,
                    error_message=error_message,
                )
            )
            return

        # check if command exists
        if command_request.action not in self._exposed_interface:
            error_message = (
                f"No registered command found for action={command_request.action}. "
                f"Supported actions {list(self._exposed_interface.keys())}"
            )
            _refuse_and_return(error_message)

        manifest = self._exposed_interface[command_request.action]

        # check command_type matches the one declared in the manifest
        if command_request.command_type != manifest.command_type:
            error_message = (
                f"Incoming request command_type {command_request.command_type} do not match "
                f"manifest's command_type {manifest.command_type} for command "
                f"{command_request.action}"
            )
            _refuse_and_return(error_message)

        # check if provided parametes match manifest
        incoming_params_set = set(command_request.params.keys())
        manifest_params_set = set(manifest._remapped_params.keys())
        if incoming_params_set != manifest_params_set:
            error_message = (
                f"Incoming request params {command_request.params} do not match "
                f"manifest's params {manifest.params}"
            )
            _refuse_and_return(error_message)

        # accept command
        self._out_queue.put(
            CommandReceived(
                request_id=command_request.request_id,
                accepted=True,
                error_message=None,
            )
        )

        self._incoming_request_tracker.append(command_request)

    def _handle_command_reply(self, response: bytes) -> None:
        command_reply: Optional[CommandReply] = CommandReply.from_bytes(response)
        assert command_reply

        tracked_request: TrackedRequest = self._request_tracker[command_reply.reply_id]
        tracked_request.reply = command_reply

    def _handle_command_received(self, response: bytes) -> None:
        command_received: Optional[CommandReceived] = CommandReceived.from_bytes(
            response
        )
        assert command_received

        self._incoming_command_queue.put_nowait(command_received)

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

            # case CommandReceived
            try:
                self._handle_command_received(response)
            except ValidationError:
                pass

            # case CommandRequest
            try:
                self._handle_command_request(response)
            except ValidationError:
                pass

            # case CommandReply
            try:
                self._handle_command_reply(response)
            except ValidationError:
                pass

            sleep(WAIT_FOR_MESSAGES)

        self._sender_receiver_pair.receiver_cleanup()

    def _enqueue_call(
        self,
        action: str,
        params: Optional[Dict[str, Any]],
        expected_command_type: CommnadType,
    ) -> CommandRequest:
        """validates and enqueues the call for delivery to remote"""
        request = CommandRequest(
            request_id=_generate_request_id(),
            action=action,
            params={} if params is None else params,
            command_type=expected_command_type,
        )

        self._request_tracker[request.request_id] = TrackedRequest(
            request=request, reply=None
        )

        self._out_queue.put(request)

        # check command_received status
        command_received: Optional[CommandReceived] = None
        try:
            for attempt in Retrying(
                stop=stop_after_delay(WAIT_FOR_RECEIVED),
                wait=wait_fixed(WAIT_BETWEEN_CHECKS),
                retry_error_cls=Empty,
            ):
                with attempt:
                    command_received = self._incoming_command_queue.get(block=False)
        except RetryError:
            raise NoCommandReceivedArrivedException()

        assert command_received

        if not command_received.accepted:
            raise CommnadNotAcceptedException(command_received.error_message)

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
        self, action: str, params: Optional[Dict[str, Any]] = None
    ) -> None:
        """No reply will be provided by remote side for this command"""
        self._enqueue_call(action, params, CommnadType.WITHOUT_REPLY)

    def request_and_check(
        self, action: str, params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        returns a `request_id` to be used with `check_for_reply` to monitor
        if a reply to the request was returned.
        """
        request = self._enqueue_call(action, params, CommnadType.WITH_REPLAY)
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
        if tracked_request.request.command_type not in {
            CommnadType.WAIT_FOR_REPLY,
            CommnadType.WITH_REPLAY,
        }:
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
        action: str,
        timeout: float,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Requests and awaits for the response from remote.
        A timeout for this function is required. If the timeout is reached `None` will
        be returned.
        """
        request = self._enqueue_call(action, params, CommnadType.WAIT_FOR_REPLY)

        try:
            for attempt in Retrying(
                stop=stop_after_delay(timeout),
                wait=wait_fixed(WAIT_BETWEEN_CHECKS),
                retry_error_cls=NoReplyException,
            ):
                with attempt:
                    reply_received, result = self.check_for_reply(request.request_id)
                    if not reply_received:
                        raise NoReplyException()

                    return result
        except RetryError:
            return None

    def get_incoming_requests(self) -> List[CommandRequest]:
        """retruns all accumulated CommandRequests"""
        results = deque()

        # fetch all elements empty
        # below implementation is thread-safe
        try:
            while True:
                results.append(self._incoming_request_tracker.pop())
        except IndexError:
            pass

        return list(results)

    def reply_to_command(self, request_id: str, payload: Any) -> None:
        """provide the reply back to a command"""
        self._out_queue.put(CommandReply(reply_id=request_id, payload=payload))
