from osparc_control import PairedTransmitter


def main() -> None:
    paired_transmitter = PairedTransmitter(
        remote_host="localhost",
        exposed_commands=[],  # not required to define an interface
        # since both `PairedTransmitter`s run on the same host ports need to different
        remote_port=2345,
        listen_port=2346,
    )

    # using a context manager allows to avoid calling
    # paired_transmitter.start_background_sync() before making/receiving requests
    # paired_transmitter.stop_background_sync() to close and cleanup when done
    with paired_transmitter:
        random_int = paired_transmitter.request_with_immediate_reply(
            "random_in_range", timeout=10.0, params={"a": 1, "b": 10}
        )
        print(random_int)
        assert random_int is not None  # noqa: S101
        assert 1 <= random_int <= 10  # noqa: S101


if __name__ == "__main__":
    main()
