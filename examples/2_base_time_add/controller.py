from osparc_control import PairedTransmitter


def main() -> None:
    paired_transmitter = PairedTransmitter(
        remote_host="localhost", exposed_commands=[], remote_port=1234, listen_port=1235
    )

    # using a context manager allows to avoid calling
    # paired_transmitter.start_background_sync() before making/receiving requests
    # paired_transmitter.stop_background_sync() to close and cleanup when done
    with paired_transmitter:

        # call remote `add_internal_time`:
        # - the user is required to `poll` for the result
        # - returns: the internal time plus the provided parameter `a`
        add_params = {"a": 10}
        print(f"Will add internal time to parameter {add_params}")
        request_id = paired_transmitter.request_with_delayed_reply(
            "add_internal_time", params=add_params
        )
        # very basic way of polling for expected result
        has_result = False
        result = None
        while not has_result:
            has_result, result = paired_transmitter.check_for_reply(
                request_id=request_id
            )
        print(f"result of `add_internal_time` with input {add_params}: {result}")

        # call remote `get_time`:
        # - will block until the result is received
        # - NOTE: timeout parameter is required and should be proportional
        #   to the mount of time the user expects the remote to reply in
        # - returns: the server internal time
        print("getting solver time")
        solver_time = paired_transmitter.request_with_immediate_reply(
            "get_time", timeout=1.0
        )
        print(f"solver time= {solver_time}")

        # call remote `close_solver`:
        # - does not return anything
        # - will cause the solver.py to close
        print("sending command to close remote")
        paired_transmitter.request_without_reply("close_solver")

    print("finished")


if __name__ == "__main__":
    main()
