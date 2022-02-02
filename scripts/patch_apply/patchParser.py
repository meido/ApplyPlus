from enum import Enum
import re
import os
import subprocess
from scripts.enums import natureOfChange, precheckStatus


class Patch:
    def __init__(self, filename):
        """
        Constructor
        --------------------------
        Gets patch name as input
        --------------------------
        _lines is a list of tuples of the format-
        [(<nature_of_change>, <change>),(<nature_of_change>, <change>),...,]
        Nature of Change can be one of the enums defined in natureOfChange (ADDED, REMOVED, CONTEXT)
        _lineschanged stores the lines changed info for a patch. ie- The data found between @@s
        """
        self._fileName = filename
        self._lines = []
        self._lineschanged = [-1, -1, -1, -1]

    def __str__(self):
        """
        Overloaded print function
        """
        toReturn = "filename: {} \n".format(self._fileName)
        for line in self._lines:
            if line[0] == natureOfChange.ADDED:
                toReturn += "Type: {}   ||{}\n".format(line[0].name, line[1])
            else:
                toReturn += "Type: {} ||{}\n".format(line[0].name, line[1])
        return toReturn

    def addLines(self, lineType, lineToAdd):
        """
        Method used to add a line to a patch file
        """
        self._lines.append((lineType, lineToAdd))

    def getLines(self):
        """
        Accessor to get lines stored in patch
        --------------------------
        Returns a list of tuples of the format-
        [(<nature_of_change>, <change>),(<nature_of_change>, <change>),...,]
        Nature of Change can be one of the enums defined in natureOfChange (ADDED, REMOVED, CONTEXT)
        """
        return self._lines

    def getFileName(self):
        """
        Accessor to get file name
        """
        return self._fileName

    def setLinesChanged(self, rawData):
        """
        Method used to add lines changed info for a patch
        """
        match = re.fullmatch(r'@@ -([0-9]+),([0-9]+) *\+([0-9]+),([0-9]+) @@.*', rawData)
        if match is not None:
            self._lineschanged[0] = int(match.group(1))
            self._lineschanged[1] = int(match.group(2))
            self._lineschanged[2] = int(match.group(3))
            self._lineschanged[3] = int(match.group(4))
            return

        match = re.fullmatch(r'@@ -([0-9]+) *\+([0-9]+),([0-9]+) @@.*', rawData)
        if match is not None:
            self._lineschanged[0] = int(match.group(1))
            self._lineschanged[1] = 1
            self._lineschanged[2] = int(match.group(2))
            self._lineschanged[3] = int(match.group(3))
            return

        match = re.fullmatch(r'@@ -([0-9]+),([0-9]+) *\+([0-9]+) @@.*', rawData)
        if match is not None:
            self._lineschanged[0] = int(match.group(1))
            self._lineschanged[1] = int(match.group(2))
            self._lineschanged[2] = int(match.group(3))
            self._lineschanged[3] = 1
            return

        match = re.fullmatch(r'@@ -([0-9]+) *\+([0-9]+) @@.*', rawData)
        if match is not None:
            self._lineschanged[0] = int(match.group(1))
            self._lineschanged[1] = 1
            self._lineschanged[2] = int(match.group(2))
            self._lineschanged[3] = 1
            return

        raise ValueError( "Don't know how to handle context line %s" % rawData)

    def getLinesChanged(self):
        """
        Access the lines changed info for a patch
        return: A list of length 4.
        Eg: For @@ -20,7 +20,6 @@,
        this method returns [-20, 7, 20, 6]
        """
        return self._lineschanged

    def _to_raw(self, string):
        """ Private helper method to return raw string"""
        return str(string)

    def canApply(self, applyTo=None):
        """
            Returns a enum precheckStatus:
                CAN_APPLY: We found the exact match, and we found that some lines in the patch haven't been applied
                ALREADY_APPLIED: We found the exact match, and all lines in the patch have been applied
                NO_MATCH_FOUND: We cannot find the exact match, need fuzzy check in the future
        """

        if applyTo is None:
            applyTo = os.path.join( os.getcwd(), self.getFileName())

        if not os.path.isfile(applyTo):
            return False

        orgPatch = []
        with open(applyTo, "r", encoding="utf-8") as srcfile:
            while True:
                line = srcfile.readline()
                if not line:
                    break

                line = line.strip("\n")
                orgPatch.append(line)
        removedFlag = [ True for i in range(len(self._lines))]
        for checkLines in range(len(orgPatch)):
            # Check if first line of patch exists
            if orgPatch[checkLines].strip() == self._to_raw(self._lines[1][1]).strip():
                patch_found_flag = True
                blank_line_offset_file = 0
                added_offset = 0
                ite = 2

                # Check if the following lines match
                while ite < len(self._lines):
                    original_patch_offset = (
                        checkLines + ite - 1 - blank_line_offset_file - added_offset
                    )

                    if original_patch_offset >= len(orgPatch):
                        patch_found_flag = False
                        break
                    if self._lines[ite][0] == natureOfChange.ADDED:
                        if (
                            orgPatch[original_patch_offset].strip()
                            == self._lines[ite][1].strip()
                        ):
                            self._lines[ite] = (
                                natureOfChange.CONTEXT,
                                self._lines[ite][1],
                            )
                        else:
                            added_offset += 1
                    elif self._lines[ite][0] == natureOfChange.REMOVED:
                        if (
                            orgPatch[original_patch_offset].strip()
                            == self._lines[ite][1].strip()
                        ):  # removed line still present
                            removedFlag[ite] = False
                        else:
                            # line removed, do not increase the orgPatch index.
                            added_offset += 1
                    elif (
                        orgPatch[original_patch_offset].strip()
                        != self._lines[ite][1].strip()
                    ):
                        if len(orgPatch[original_patch_offset].strip()) == 0:
                            # orgPatch empty line. keep ite the same but check next line of orgPatch
                            blank_line_offset_file -= 1
                            ite -= 1
                        elif len(self._lines[ite][1].strip()) == 0 and self._lines[ite][0] != natureOfChange.REMOVED:
                            # hunk empty line. go to next line of hunk
                            blank_line_offset_file += 1
                        else:
                            # doesn't match
                            patch_found_flag = False
                            break
                    ite += 1
                if patch_found_flag:
                    # If they are all context lines now, this patch
                    # has already been applied and shouldn't be
                    # applied again.

                    for ite_line in self._lines:
                        if ite_line[0] == natureOfChange.ADDED:
                            # the lines to be added hasn't beed added yet
                            return precheckStatus.CAN_APPLY
                    for removed in removedFlag:
                        if not removed:
                            # the lines to be removed present in the file
                            return precheckStatus.CAN_APPLY
                    return precheckStatus.ALREADY_APPLIED
                else:
                    for removed in removedFlag:
                        if not removed:
                            # We found some lines should be removed presented in the file
                            # But we cannot find the exact match of this patch
                            # This is the case when, we might partially find some removed line presented in the file in the firse checkLines chunk
                            # But then the following lines did not match the patch
                            # We kept those records in the array. We cannot keep it towards the next checkLines chunk check. Discard that change will also result in false positive
                            # see msm-3.10: CVE-2016-3672.patch
                            return precheckStatus.NO_MATCH_FOUND

        return precheckStatus.NO_MATCH_FOUND

    def Apply(self, applyTo, dry_run=False):
        """
        If patch can be applied, this method
        applies it.
        """
        if self.canApply(applyTo) == precheckStatus.CAN_APPLY:
            orgPatch = []
            with open(applyTo, "r", encoding="utf-8") as srcfile:
                while True:
                    line = srcfile.readline()
                    if not line:
                        break
                    orgPatch.append(line.strip("\n"))

            # start by assuming all lines to be removed are removed
            removedFlag = [ True for i in range(len(self._lines))]
            for checkLines in range(len(orgPatch)):
                # Check if first line of patch exists
                if (
                    orgPatch[checkLines].strip()
                    == self._to_raw(self._lines[1][1]).strip()
                ):
                    patch_found_flag = True
                    blank_line_offset_file = 0
                    added_offset = 0
                    ite = 2
                    # check the following lines after matched the first line
                    while ite < len(self._lines):
                        original_patch_offset = (
                            checkLines + ite - 1 - blank_line_offset_file - added_offset
                        )
                        if original_patch_offset >= len(orgPatch):
                            patch_found_flag = False
                            break
                        if (
                            self._lines[ite][0] == natureOfChange.ADDED
                            and orgPatch[original_patch_offset].strip()
                        ):
                            if (
                                orgPatch[original_patch_offset].strip()
                                == self._lines[ite][1].strip()
                            ):
                                self._lines[ite] = (
                                    natureOfChange.CONTEXT,
                                    self._lines[ite][1],
                                )
                            else:
                                added_offset += 1
                        elif (
                            self._lines[ite][0] == natureOfChange.REMOVED
                        ):
                            if (
                                orgPatch[original_patch_offset].strip()
                                == self._lines[ite][1].strip()
                            ):
                                # find presence of a removed line
                                removedFlag[ite] = False
                            else:
                                added_offset += 1
                        elif (
                            orgPatch[original_patch_offset].strip()
                            != self._lines[ite][1].strip()
                        ):
                            if len(orgPatch[original_patch_offset].strip()) == 0:
                                blank_line_offset_file -= 1
                                ite -= 1
                            elif len(self._lines[ite][1].strip()) == 0:
                                blank_line_offset_file += 1
                            else:
                                patch_found_flag = False
                                break
                        ite += 1
                    if patch_found_flag:
                        # If the next line runs, we know the patch is applied here
                        ite2 = 0
                        ite3 = 1
                        goal = len(self._lines)
                        while ite2 < goal and ite3 < len(self._lines):
                            if self._lines[ite3][0] == natureOfChange.REMOVED:
                                if not removedFlag[ite3]:
                                    goal -= 1
                                    orgPatch.pop(checkLines + ite2)
                                ite3 += 1
                            elif self._lines[ite3][0] == natureOfChange.ADDED:
                                orgPatch.insert(checkLines + ite2, self._lines[ite3][1])
                                ite2 += 1
                                ite3 += 1
                            elif self._lines[ite3][0] == natureOfChange.CONTEXT:
                                if (
                                    self._lines[ite3][1].strip()
                                    != orgPatch[checkLines + ite2].strip()
                                ):
                                    if len(self._lines[ite3][1].strip()) == 0:
                                        ite3 += 1
                                    else:
                                        ite2 += 1
                                else:
                                    ite2 += 1
                                    ite3 += 1

                        # if not dry_run:
                        if False: # test
                            writeobj = open(applyTo, "w")
                            for i in orgPatch:
                                i = i.replace("\n", "\\n")
                                writeobj.write(i + "\n")
                            writeobj.close()
                        return True

        return False


class PatchFile:
    def __init__(self, pathToFile=""):
        """
        Constructor
        --------------------------
        Takes path to patch file as input
        --------------------------
        Patches is a list of objects of type patch
        """
        self.pathToFile = pathToFile
        self.patches = []
        self.runSuccess = False
        self.runResult = "Patch has not been run yet"

    def runPatch(self, reverse=False, dry_run=False):
        """
        Returns an empty string if patch successfully runs
        else returns the exact error message as a string

        If revert=True arg is provided, git apply --reverse is run.
        """
        cmdline = ['git', 'apply']
        if reverse == True:
            cmdline.append( '--reverse' )
        if dry_run == True:
            cmdline.append( '--check' )
        cmdline.append( '--verbose' )
        cmdline.append( self.pathToFile )

        result = subprocess.run( cmdline, capture_output=True, text=True )
        if result.returncode == 0:
            # Need to make sure that GIT didn't skip any patches.
            if re.search( '^Skipped patch', result.stderr ) is None:
                self.runSuccess = True
                self.runResult = "Patch ran successfully"
            else:
                self.runSuccess = False
                self.runResult = ''
                for line in result.stderr.splitlines():
                    m = re.search(r"Skipped patch '([^']*)'.", line)
                    if m is not None:
                        self.runResult += "error:%s:skipped\n" % m.group(1)
        else:
            self.runResult = result.stderr

    def getPatch(self):
        """
        A patch file has multiple patches.
        This method returns a list of patch objects
        each representing one patch
        """

        with open(self.pathToFile) as fileObj:
            file = fileObj.read().rstrip()
            file = file.split("\n")

        patchObj = None

        for line in file:
            # print( "Line: %s" % line)
            # print("________________")

            # This is a HACK.  In general, we should probably not be
            # modifying the file name in the patch.  In this case
            # though, GIT always adds a "b/" to the name of the file
            # being modified.  It also turns out that the unit tests
            # do this (not that we want to have specific code just for
            # the unit tests).
            if line[0:6] == "+++ b/":
                if patchObj is not None:
                    assert( len(patchObj.getLines()) > 0)
                    self.patches.append(patchObj)

                if patchObj is None:
                    filename = line.split()[1][2:]
                    patchObj = Patch(filename)

            elif line[0:3] == '+++':
                if patchObj is not None:
                    assert( len(patchObj.getLines()) > 0)
                    self.patches.append(patchObj)

                if patchObj is None:
                    filename = "./" + line.split()[1]
                    patchObj = Patch(filename)

            elif line[0:3] == '---':
                if patchObj is not None:
                    self.patches.append(patchObj)
                    patchObj = None

            elif line[0:3] == "@@ ":
                contextline = line[2:].split(" @@ ")[-1]
                assert( patchObj is not None )

                if len(patchObj.getLines()) != 0:
                    filename = patchObj.getFileName()
                    self.patches.append(patchObj)
                    patchObj = Patch(filename)
                    patchObj.setLinesChanged(line)
                else:
                    patchObj.setLinesChanged(line)

                patchObj.addLines(
                    natureOfChange.CONTEXT,
                    contextline,
                )

            elif line[0:1] == "-" and patchObj is not None:
                contextline = line[1:]
                patchObj.addLines(natureOfChange.REMOVED, contextline)

            elif line[0:1] == "+" and patchObj is not None:
                contextline = line[1:]
                patchObj.addLines(natureOfChange.ADDED, contextline)

            elif line[0:1] == ' ' and patchObj is not None:
                contextline = line[1:]
                patchObj.addLines(natureOfChange.CONTEXT, contextline)

            else:
                # A patch can have lots of lines in it that are added
                # by tools like GIT.  These lines have no particular
                # format, other than the fact that they are not within
                # hunks.
                pass

        self.patches.append(patchObj)
