"""
Netmiko SCP operations.

Supports file get and file put operations.

SCP requires a separate SSH connection for a control channel.
"""

from typing import AnyStr, Optional, Callable, Any, Dict
from typing import TYPE_CHECKING
from netmiko.scp_handler import BaseFileTransfer
from netmiko.ssh_dispatcher import FileTransfer
from netmiko.cisco.cisco_ios import InLineTransfer

if TYPE_CHECKING:
    from netmiko.base_connection import BaseConnection


def progress_bar(
    filename: AnyStr, size: int, sent: int, peername: Optional[str] = None
) -> None:
    max_width = 50
    if isinstance(filename, bytes):
        filename_str = filename.decode()
    else:
        filename_str = filename
    clear_screen = chr(27) + "[2J"
    terminating_char = "|"

    # Percentage done
    percent_complete = sent / size
    percent_str = f"{percent_complete * 100:.2f}%"
    hash_count = int(percent_complete * max_width)
    progress = hash_count * ">"

    if peername is None:
        header_msg = f"Transferring file: {filename_str}\n"
    else:
        header_msg = f"Transferring file to {peername}: {filename_str}\n"

    msg = f"{progress:<50}{terminating_char:1} ({percent_str})"
    print(clear_screen)
    print(header_msg)
    print(msg)


def verifyspace_and_transferfile(scp_transfer: BaseFileTransfer) -> None:
    """Verify space and transfer file."""
    if not scp_transfer.verify_space_available():
        raise ValueError("Insufficient space available on remote device")
    scp_transfer.transfer_file()


def file_transfer(
    ssh_conn: "BaseConnection",
    source_file: str,
    dest_file: str,
    file_system: Optional[str] = None,
    direction: str = "put",
    disable_md5: bool = False,
    inline_transfer: bool = False,
    overwrite_file: bool = False,
    socket_timeout: float = 10.0,
    progress: Optional[Callable[..., Any]] = None,
    progress4: Optional[Callable[..., Any]] = None,
    verify_file: Optional[bool] = None,
) -> Dict[str, bool]:
    """Use Secure Copy or Inline (IOS-only) to transfer files to/from network devices.

    inline_transfer ONLY SUPPORTS TEXT FILES and will not support binary file transfers.

    return {
        'file_exists': boolean,
        'file_transferred': boolean,
        'file_verified': boolean,
    }
    """
    transferred_and_verified = {
        "file_exists": True,
        "file_transferred": True,
        "file_verified": True,
    }
    transferred_and_notverified = {
        "file_exists": True,
        "file_transferred": True,
        "file_verified": False,
    }
    nottransferred_but_verified = {
        "file_exists": True,
        "file_transferred": False,
        "file_verified": True,
    }

    if "cisco_ios" in ssh_conn.device_type or "cisco_xe" in ssh_conn.device_type:
        cisco_ios = True
    else:
        cisco_ios = False
    if not cisco_ios and inline_transfer:
        raise ValueError("Inline Transfer only supported for Cisco IOS/Cisco IOS-XE")

    # Replace disable_md5 argument with verify_file argument across time
    if verify_file is None:
        verify_file = not disable_md5

    scp_args = {
        "ssh_conn": ssh_conn,
        "source_file": source_file,
        "dest_file": dest_file,
        "direction": direction,
        "socket_timeout": socket_timeout,
        "progress": progress,
        "progress4": progress4,
    }
    if file_system is not None:
        scp_args["file_system"] = file_system

    TransferClass: Callable[..., BaseFileTransfer]
    if inline_transfer:
        TransferClass = InLineTransfer
    else:
        TransferClass = FileTransfer

    with TransferClass(**scp_args) as scp_transfer:
        if scp_transfer.check_file_exists():
            if overwrite_file:
                if verify_file:
                    if scp_transfer.verify_file():
                        return nottransferred_but_verified
                    else:
                        # File exists, you can overwrite it, MD5 is wrong (transfer file)
                        verifyspace_and_transferfile(scp_transfer)
                        if scp_transfer.verify_file():
                            return transferred_and_verified
                        else:
                            raise ValueError(
                                "MD5 failure between source and destination files"
                            )
                else:
                    # File exists, you can overwrite it, but MD5 not allowed (transfer file)
                    verifyspace_and_transferfile(scp_transfer)
                    return transferred_and_notverified
            else:
                # File exists, but you can't overwrite it.
                if verify_file:
                    if scp_transfer.verify_file():
                        return nottransferred_but_verified
                msg = "File already exists and overwrite_file is disabled"
                raise ValueError(msg)
        else:
            verifyspace_and_transferfile(scp_transfer)
            # File doesn't exist
            if verify_file:
                if scp_transfer.verify_file():
                    return transferred_and_verified
                else:
                    raise ValueError("MD5 failure between source and destination files")
            else:
                return transferred_and_notverified
