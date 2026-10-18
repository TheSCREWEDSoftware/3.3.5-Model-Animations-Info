r"""Read-only access to a WoW 3.3.5a client's archives, through StormLib (https://github.com/ladislav-zezula/StormLib).

    client = Client(r"...\World of Warcraft\Data", "path/to/libstorm.so or StormLib.dll")
    data = client.read("DBFilesClient\\AnimationData.dbc")

Archives are searched in the order the client itself uses, so a file in a patch wins over the base archives.
"""
import ctypes, os
from ctypes import c_void_p, c_char_p, c_uint, c_int, byref, POINTER

# lowest -> highest priority
ORDER = ["common.MPQ", "common-2.MPQ", "expansion.MPQ", "lichking.MPQ",
         "enGB/locale-enGB.MPQ", "enGB/speech-enGB.MPQ", "enGB/expansion-locale-enGB.MPQ", "enGB/lichking-locale-enGB.MPQ",
         "enGB/expansion-speech-enGB.MPQ", "enGB/lichking-speech-enGB.MPQ",
         "patch.MPQ", "patch-2.MPQ", "patch-3.MPQ", "patch-W.mpq", "patch-Z.mpq",
         "enGB/patch-enGB.MPQ", "enGB/patch-enGB-2.MPQ", "enGB/patch-enGB-3.MPQ", "enGB/patch-enGB-M.MPQ", "enGB/patch-enGB-N.MPQ",
         "enGB/patch-enGB-y.mpq"]
READ_ONLY = 0x100


class _Folder:
    """A patch that is a plain folder on disk (the client loads those too)."""
    def __init__(self, root):
        self.index = {}
        for folder, _, files in os.walk(root):
            for f in files:
                full = os.path.join(folder, f)
                self.index[os.path.relpath(full, root).replace("/", "\\").lower()] = full

    def read(self, name, offset=0, size=None):
        path = self.index.get(name.lower())
        if not path:
            return None
        with open(path, "rb") as f:
            f.seek(offset)
            return f.read() if size is None else f.read(size)


class _Archive:
    def __init__(self, storm, path):
        self.storm, self.handle = storm, c_void_p()
        if not storm.SFileOpenArchive(path.encode(), 0, READ_ONLY, byref(self.handle)):
            raise OSError("cannot open " + path)

    def read(self, name, offset=0, size=None):
        s, f = self.storm, c_void_p()
        if not s.SFileOpenFileEx(self.handle, name.encode("latin-1"), 0, byref(f)):
            return None
        try:
            total = s.SFileGetFileSize(f, None)
            if total == 0xFFFFFFFF:
                return None
            size = max(0, min(total - offset if size is None else size, total - offset))
            if offset:
                s.SFileSetFilePointer(f, offset, None, 0)
            buf, got = ctypes.create_string_buffer(size), c_uint(0)
            s.SFileReadFile(f, buf, size, byref(got), None)
            return buf.raw[:got.value]
        finally:
            s.SFileCloseFile(f)


class Client:
    def __init__(self, data_dir, stormlib):
        s = ctypes.CDLL(stormlib)
        s.SFileOpenArchive.argtypes = [c_char_p, c_uint, c_uint, POINTER(c_void_p)]; s.SFileOpenArchive.restype = ctypes.c_bool
        s.SFileOpenFileEx.argtypes = [c_void_p, c_char_p, c_uint, POINTER(c_void_p)]; s.SFileOpenFileEx.restype = ctypes.c_bool
        s.SFileGetFileSize.argtypes = [c_void_p, POINTER(c_uint)]; s.SFileGetFileSize.restype = c_uint
        s.SFileSetFilePointer.argtypes = [c_void_p, c_int, POINTER(c_int), c_uint]; s.SFileSetFilePointer.restype = c_uint
        s.SFileReadFile.argtypes = [c_void_p, c_void_p, c_uint, POINTER(c_uint), c_void_p]; s.SFileReadFile.restype = ctypes.c_bool
        s.SFileCloseFile.argtypes = [c_void_p]; s.SFileCloseFile.restype = ctypes.c_bool
        self.archives = []                                   # highest priority first
        for rel in reversed(ORDER):
            path = os.path.join(data_dir, rel)
            if os.path.isdir(path):
                self.archives.append((rel, _Folder(path)))
            elif os.path.isfile(path):
                self.archives.append((rel, _Archive(s, path)))

    def find(self, name):
        """-> (name of the archive that wins, that archive) or (None, None)"""
        for rel, archive in self.archives:
            if archive.read(name, 0, 4):
                return rel, archive
        return None, None

    def read(self, name, offset=0, size=None):
        _, archive = self.find(name)
        return archive.read(name, offset, size) if archive else None
