"""
Netmiko SCP operations.

Supports file get and file put operations.

SCP requires a separate SSH connection for a control channel.

Currently only supports Cisco IOS and Cisco ASA.
"""
from netmiko import FileTransfer, InLineTransfer


def verifyspace_and_transferfile(scp_transfer):
    """Verify space and transfer file."""
    if not scp_transfer.verify_space_available():
        raise ValueError("Insufficient space available on remote device")
    scp_transfer.transfer_file()


def file_transfer(
    ssh_conn,
    source_file,
    dest_file,
    file_system=None,
    direction="put",
    disable_md5=False,
    inline_transfer=False,
    overwrite_file=False,
    socket_timeout=10.0,
):
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

    scp_args = {
        "ssh_conn": ssh_conn,
        "source_file": source_file,
        "dest_file": dest_file,
        "direction": direction,
        "socket_timeout": socket_timeout,
    }
    if file_system is not None:
        scp_args["file_system"] = file_system

    TransferClass = InLineTransfer if inline_transfer else FileTransfer

    with TransferClass(**scp_args) as scp_transfer:
        if scp_transfer.check_file_exists():
            if overwrite_file:
                if not disable_md5:
                    if scp_transfer.compare_md5():
                        return nottransferred_but_verified
                    else:
                        # File exists, you can overwrite it, MD5 is wrong (transfer file)
                        verifyspace_and_transferfile(scp_transfer)
                        if scp_transfer.compare_md5():
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
                if not disable_md5:
                    if scp_transfer.compare_md5():
                        return nottransferred_but_verified
                msg = "File already exists and overwrite_file is disabled"
                raise ValueError(msg)
        else:
            verifyspace_and_transferfile(scp_transfer)
            # File doesn't exist
            if not disable_md5:
                if scp_transfer.compare_md5():
                    return transferred_and_verified
                else:
                    raise ValueError("MD5 failure between source and destination files")
            else:
                return transferred_and_notverified
