import hashlib
from dataclasses import dataclass
from datetime import datetime
import plistlib
from pathlib import Path
from base64 import b64decode
from random import randbytes
from typing import Optional, List
from . import mbdb
from .mbdb import _FileMode

# RWX:RX:RX
DEFAULT_MODE = (
    _FileMode.S_IRUSR | _FileMode.S_IWUSR | _FileMode.S_IXUSR |
    _FileMode.S_IRGRP | _FileMode.S_IXGRP |
    _FileMode.S_IROTH | _FileMode.S_IXOTH
)


@dataclass
class BackupFile:
    """Represents a generic file in the backup."""
    path: str
    domain: str

    def to_record(self) -> mbdb.MbdbRecord:
        """Convert the file to an MbdbRecord."""
        raise NotImplementedError("Subclasses must implement this method.")


@dataclass
class ConcreteFile(BackupFile):
    contents: bytes
    owner: int = 0
    group: int = 0
    inode: Optional[int] = None
    mode: _FileMode = DEFAULT_MODE

    def to_record(self) -> mbdb.MbdbRecord:
        return create_record(
            domain=self.domain,
            path=self.path,
            inode=self.inode or int.from_bytes(randbytes(8), "big"),
            mode=self.mode | _FileMode.S_IFREG,
            size=len(self.contents),
            user_id=self.owner,
            group_id=self.group,
            hash_value=hashlib.sha256(self.contents).digest()
        )


@dataclass
class Directory(BackupFile):
    owner: int = 0
    group: int = 0
    mode: _FileMode = DEFAULT_MODE

    def to_record(self) -> mbdb.MbdbRecord:
        return create_record(
            domain=self.domain,
            path=self.path,
            mode=self.mode | _FileMode.S_IFDIR,
            user_id=self.owner,
            group_id=self.group
        )


@dataclass
class SymbolicLink(BackupFile):
    target: str
    owner: int = 0
    group: int = 0
    inode: Optional[int] = None
    mode: _FileMode = DEFAULT_MODE

    def to_record(self) -> mbdb.MbdbRecord:
        return create_record(
            domain=self.domain,
            path=self.path,
            inode=self.inode or int.from_bytes(randbytes(8), "big"),
            mode=self.mode | _FileMode.S_IFLNK,
            user_id=self.owner,
            group_id=self.group,
            link=self.target
        )


def create_record(
    domain: str, path: str, mode: _FileMode, user_id: int,
    group_id: int, inode: Optional[int] = 0, size: int = 0,
    hash_value: bytes = b"", link: str = ""
) -> mbdb.MbdbRecord:
    """Utility function to create an MbdbRecord with common fields."""
    timestamp = int(datetime.now().timestamp())
    return mbdb.MbdbRecord(
        domain=domain,
        filename=path,
        link=link,
        hash=hash_value,
        key=b"",
        mode=mode,
        inode=inode,
        user_id=user_id,
        group_id=group_id,
        mtime=timestamp,
        atime=timestamp,
        ctime=timestamp,
        size=size,
        flags=4,
        properties=[]
    )


@dataclass
class Backup:
    files: List[BackupFile]

    def write_to_directory(self, directory: Path):
        """Write backup files and metadata to a directory."""
        try:
            for file in self.files:
                if isinstance(file, ConcreteFile):
                    hashed_name = hashlib.sha256(
                        f"{file.domain}-{file.path}".encode()
                    ).hexdigest()
                    with open(directory / hashed_name, "wb") as f:
                        f.write(file.contents)

            self._write_metadata(directory)
        except OSError as e:
            print(f"Failed to write backup: {e}")
            raise

    def _write_metadata(self, directory: Path):
        """Write metadata files to the backup directory."""
        metadata_files = {
            "Manifest.mbdb": self.generate_manifest_db().to_bytes(),
            "Status.plist": self.generate_status(),
            "Manifest.plist": self.generate_manifest(),
            "Info.plist": plistlib.dumps({})
        }
        for filename, content in metadata_files.items():
            with open(directory / filename, "wb") as f:
                f.write(content)

    def generate_manifest_db(self) -> mbdb.Mbdb:
        """Generate the manifest database."""
        return mbdb.Mbdb(records=[file.to_record() for file in self.files])

    def generate_status(self) -> bytes:
        """Generate the status plist."""
        return plistlib.dumps({
            "BackupState": "new",
            "Date": datetime(1970, 1, 1, tzinfo=None),
            "IsFullBackup": False,
            "SnapshotState": "finished",
            "UUID": "00000000-0000-0000-0000-000000000000",
            "Version": "2.4"
        })

    def generate_manifest(self) -> bytes:
        """Generate the manifest plist."""
        return plistlib.dumps({
            "BackupKeyBag": b64decode("""
                VkVSUwAAAAQAAAAFVFlQRQAAAAQAAAAB...
            """),
            "Lockdown": {},
            "SystemDomainsVersion": "20.0",
            "Version": "9.1"
        })