#!/usr/bin/env python

from typing import Optional, Generator
import os
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))


class WireguardEndpointsException(Exception):
    pass


class WireguardEndpointsError(WireguardEndpointsException):
    pass


class ParseError(WireguardEndpointsError):
    pass


def sh(
    cmd: str, args: Optional[list[str]] = None, working_directory: Optional[str] = None
) -> str:
    if not isinstance(cmd, str):
        raise TypeError("`cmd` must be str")
    if args is not None:
        if not isinstance(args, list):
            raise TypeError("`args` must be list")
        for arg in args:
            if not isinstance(arg, str):
                raise TypeError("`args` must contain only values of type str")

    if working_directory is None:
        raise ValueError("`working_directory` is required")
    if not isinstance(working_directory, str):
        raise TypeError("`working_directory` must be str")
    if not os.path.isabs(working_directory):
        raise ValueError("`working_directory` must be an absolute path")

    if args is None:
        args = []

    completed_process = subprocess.run(
        [cmd, *args],
        check=True,
        cwd=working_directory,
        stdout=subprocess.PIPE,
    )

    decoded_output: str = completed_process.stdout.decode("utf-8")

    return decoded_output


def parse_ip_address(input: str) -> str:
    parsed_url = urllib.parse.urlparse(f"//{input}")

    ip_address = parsed_url.hostname
    if not ip_address:
        raise ParseError(f"Could not parse IP address: {input}")

    return ip_address


def extract_ip_addresses_from_wireguard() -> Generator[str, None, None]:
    wg_dump = sh("wg", ["show", "all", "dump"], working_directory=HERE)
    current_device: Optional[str] = None
    for line in wg_dump.split("\n"):
        parts = line.split("\t")
        if not current_device or parts[0] != current_device:
            current_device = parts[0]

            continue

        endpoint = parts[3]
        ip_address = parse_ip_address(endpoint)

        yield ip_address


def main() -> int:
    ip_addresses = set(extract_ip_addresses_from_wireguard())
    for addr in sorted(ip_addresses):
        print(addr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
