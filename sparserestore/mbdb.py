from dataclasses import dataclass
from io import BytesIO
from enum import IntFlag

# Enum for file mode, mimicking Unix-like file permissions and types.
class _FileMode(IntFlag):
    S_IFMT   = 0o0170000  # File type mask
    S_IFIFO  = 0o0010000  # Named pipe (FIFO)
    S_IFCHR  = 0o0020000  # Character device
    S_IFDIR  = 0o0040000  # Directory
    S_IFBLK  = 0o0060000  # Block device
    S_IFREG  = 0o0100000  # Regular file
    S_IFLNK  = 0o0120000  # Symbolic link
    S_IFSOCK = 0o0140000  # Socket

    S_IRUSR  = 0o0000400  # Owner read permission
    S_IWUSR  = 0o0000200  # Owner write permission
    S_IXUSR  = 0o0000100  # Owner execute permission

    S_IRGRP  = 0o0000040  # Group read permission
    S_IWGRP  = 0o0000020  # Group write permission
    S_IXGRP  = 0o0000010  # Group execute permission

    S_IROTH  = 0o0000004  # Others read permission
    S_IWOTH  = 0o0000002  # Others write permission
    S_IXOTH  = 0o0000001  # Others execute permission

    S_ISUID  = 0o0004000  # Set-user-ID bit
    S_ISGID  = 0o0002000  # Set-group-ID bit
    S_ISVTX  = 0o0001000  # Sticky bit

@dataclass
class MbdbRecord:
    domain: str
    filename: str
    link: str
    hash: bytes
    key: bytes
    mode: _FileMode
    inode: int
    user_id: int
    group_id: int
    mtime: int
    atime: int
    ctime: int
    size: int
    flags: int
    properties: list

    @classmethod
    def from_stream(cls, stream: BytesIO):
        """Parse an MBDB record from a binary stream."""
        domain_len = int.from_bytes(stream.read(2), "big")
        domain = stream.read(domain_len).decode("utf-8")

        filename_len = int.from_bytes(stream.read(2), "big")
        filename = stream.read(filename_len).decode("utf-8")

        link_len = int.from_bytes(stream.read(2), "big")
        link = stream.read(link_len).decode("utf-8") if link_len != 0xFFFF else ""

        hash_len = int.from_bytes(stream.read(2), "big")
        hash_value = stream.read(hash_len) if hash_len != 0xFFFF else b""

        key_len = int.from_bytes(stream.read(2), "big")
        key = stream.read(key_len) if key_len != 0xFFFF else b""

        mode = _FileMode(int.from_bytes(stream.read(2), "big"))
        inode = int.from_bytes(stream.read(8), "big")
        user_id = int.from_bytes(stream.read(4), "big")
        group_id = int.from_bytes(stream.read(4), "big")
        mtime = int.from_bytes(stream.read(4), "big")
        atime = int.from_bytes(stream.read(4), "big")
        ctime = int.from_bytes(stream.read(4), "big")
        size = int.from_bytes(stream.read(8), "big")
        flags = int.from_bytes(stream.read(1), "big")

        properties_count = int.from_bytes(stream.read(1), "big")
        properties = []

        for _ in range(properties_count):
            name_len = int.from_bytes(stream.read(2), "big")
            name = stream.read(name_len).decode("utf-8") if name_len != 0xFFFF else ""

            value_len = int.from_bytes(stream.read(2), "big")
            value = stream.read(value_len).decode("utf-8") if value_len != 0xFFFF else ""

            properties.append((name, value))

        return cls(domain, filename, link, hash_value, key, mode, inode, user_id, group_id, mtime, atime, ctime, size, flags, properties)

    def to_bytes(self) -> bytes:
        """Convert the record into binary format."""
        stream = BytesIO()

        stream.write(len(self.domain).to_bytes(2, "big"))
        stream.write(self.domain.encode("utf-8"))

        stream.write(len(self.filename).to_bytes(2, "big"))
        stream.write(self.filename.encode("utf-8"))

        stream.write(len(self.link).to_bytes(2, "big"))
        stream.write(self.link.encode("utf-8"))

        stream.write(len(self.hash).to_bytes(2, "big"))
        stream.write(self.hash)

        stream.write(len(self.key).to_bytes(2, "big"))
        stream.write(self.key)

        stream.write(self.mode.to_bytes(2, "big"))
        stream.write(self.inode.to_bytes(8, "big"))
        stream.write(self.user_id.to_bytes(4, "big"))
        stream.write(self.group_id.to_bytes(4, "big"))
        stream.write(self.mtime.to_bytes(4, "big"))
        stream.write(self.atime.to_bytes(4, "big"))
        stream.write(self.ctime.to_bytes(4, "big"))
        stream.write(self.size.to_bytes(8, "big"))
        stream.write(self.flags.to_bytes(1, "big"))

        stream.write(len(self.properties).to_bytes(1, "big"))

        for name, value in self.properties:
            stream.write(len(name).to_bytes(2, "big"))
            stream.write(name.encode("utf-8"))

            stream.write(len(value).to_bytes(2, "big"))
            stream.write(value.encode("utf-8"))

        return stream.getvalue()

@dataclass
class Mbdb:
    records: list[MbdbRecord]

    @classmethod
    def from_bytes(cls, data: bytes):
        """Parse the entire MBDB file from binary data."""
        stream = BytesIO(data)

        # Validate MBDB header
        if stream.read(4) != b"mbdb":
            raise ValueError("Invalid MBDB file: missing magic header")

        if stream.read(2) != b"\x05\x00":
            raise ValueError("Invalid MBDB version: expected version 5")

        records = []
        while stream.tell() < len(data):
            records.append(MbdbRecord.from_stream(stream))

        return cls(records)

    def to_bytes(self) -> bytes:
        """Convert the entire MBDB structure back to binary format."""
        stream = BytesIO()

        # Write MBDB header
        stream.write(b"mbdb")
        stream.write(b"\x05\x00")

        for record in self.records:
            stream.write(record.to_bytes())

        return stream.getvalue()
