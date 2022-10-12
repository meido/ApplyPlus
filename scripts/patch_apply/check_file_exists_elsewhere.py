import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import scripts.patch_apply.patchParser as parse
from scripts.enums import SliceFields


def checkFileExistsElsewhere(patch):
    """
    A small percentage of patches fail because the file has changed locations within the repo.
    If the file were in its original location, the patch would have applied without issues.
    
    To try to avoid this error, this method goes through all the directories
    from current dirrectory and checks to see if this file exists.

    If it does, it warns the user that the file has moved.
    NOTE: This method assumes the patch has failed and we are looking for solutions
    """

    toFind = patch.getFileName().split("/")[-1]
    currentdir = os.getcwd()
    matched_file_locations = []
    for subdir, dirs, files in os.walk(currentdir):
        for file in files:
            if file == toFind:
                matched_file_locations.append(
                    os.path.relpath(os.path.join(subdir, file))
                )

    if len(matched_file_locations) == 0:
        return None
    elif sys.stdout.isatty():
        print("-" * 70)
        print(
            "Here are the locations of files with the same filename as the following missing file: {}".format(
                toFind
            )
        )
        for i in range(len(matched_file_locations)):
            print("{} : {}".format(i, matched_file_locations[i]))

        to_apply_file_index = input(
            "Select the file you would like to apply the patch to by entering the number next to it. Enter anything else to do nothing\n"
        )

        print("-" * 70)
        try:
            to_apply_file_index = int(to_apply_file_index)
            if 0 <= to_apply_file_index and to_apply_file_index < len(
                matched_file_locations
            ):
                return matched_file_locations[to_apply_file_index]
        except ValueError:
            return None
    else:
        print(f"Possible files to apply the patch for {toFind} to:")
        for i in matched_file_locations:
            print(f"  {i}")

# Testing
# patch_file = parse.PatchFile("../vulnerableforks/patches/CVE-2014-8172.patch")
# patch_file.getPatch()
# checkFileExistsElsewhere(patch_file.patches[0])
