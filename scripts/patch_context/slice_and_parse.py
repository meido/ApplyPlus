import os, subprocess, threading, sys
import tempfile as tfile
import re
from enum import Enum

src_slice_path = os.path.dirname(os.path.abspath(__file__))
if sys.platform.startswith("darwin"):
    src_slice_path += "/srcSliceBuilds/macOS/srcslice-mac"
else:
    src_slice_path += "/srcSliceBuilds/ubuntu/srcslice-ubuntu"

class RunWithTimeout(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.out = None
        self.err = None

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen( args=self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            self.out, self.err = self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        for i in range(0, timeout, 5):
            thread.join(5)
            if not thread.is_alive():
                break

            print( f"Waited {i} seconds for {self.cmd} to exit." )

        if thread.is_alive():
            print( f"Timeout waiting for {self.cmd} to exit." )
            self.process.terminate()
            thread.join()
            self.err += f"Timeout waiting for {self.cmd} to exit.".encode('ascii')

class SliceParser:
    def __init__(self, file):
        self.file = file

    def slice_parse(self):

        srcml = RunWithTimeout(["srcml", f"{self.file}", "--position"])
        srcml.run(timeout=120)

        if srcml.err:
            return None

        fd, path = tfile.mkstemp(suffix=".xml", prefix="temp")
        try:
            with os.fdopen(fd, "w") as tmpo:
                tmpo.write(str(srcml.out, "utf-8"))

            srcslice = RunWithTimeout([src_slice_path, f"{path}"])
            srcslice.run(timeout=120)

            # Remove the "Time is: ...." line from the error output.
            srcslice.err = re.sub(b'Time is: [0-9.]*\n', b'', srcslice.err)

            if srcslice.err:
                return None

            str_out = srcslice.out.decode("utf-8")
            slice_dict = {}
            for line in str_out.splitlines():

                # TODO: observe issue that arrises for patch CVE-2014-9710

                file_data = re.split(",\s*(?![^{}]*\})", line)
                if len(file_data) == 8:

                    slice_dict[file_data[1]] = {}

                    slice_dict[file_data[1]][file_data[2]] = []

                    slice_dict[file_data[1]][file_data[2]].append(file_data[0])
                    slice_dict[file_data[1]][file_data[2]].append(file_data[1])
                    slice_dict[file_data[1]][file_data[2]].append(file_data[2])

                    slice_dict[file_data[1]][file_data[2]].append(
                        (file_data[3].split("{", 1)[1].split("}")[0])
                    )
                    slice_dict[file_data[1]][file_data[2]].append(
                        (file_data[4].split("{", 1)[1].split("}")[0])
                    )
                    slice_dict[file_data[1]][file_data[2]].append(
                        (file_data[5].split("{", 1)[1].split("}")[0])
                    )
                    slice_dict[file_data[1]][file_data[2]].append(
                        (file_data[6].split("{", 1)[1].split("}")[0])
                    )
                    slice_dict[file_data[1]][file_data[2]].append(
                        (file_data[7].split("{", 1)[1].rsplit("}", 1)[0])
                    )

            return slice_dict

        finally:
            os.remove(path)
