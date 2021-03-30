#!/usr/bin/env python3

import argparse
import sys
import os
import copy
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import scripts.patch_apply.patchParser as parse

# import check_file_exists_elsewhere as fileCheck
import scripts.patch_match.test_match as tm
import scripts.patch_context.context_changes as cc
import scripts.patch_apply.check_file_exists_elsewhere as check_exist
from scripts.enums import MatchStatus, natureOfChange, CONTEXT_DECISION

def findGitPrefix(path):
    prefix=''
    resolved=False

    while True:
        if path == os.path.dirname(path) and not resolved:
            path = os.path.realpath(path)
            resolved = True

        if os.path.isdir(path):
            if os.path.isdir(os.path.join(path, ".git")):
                if os.path.isfile(os.path.join(path, ".git", "config")):
                    return prefix

        if path == os.path.dirname(path):
            break

        if resolved:
            prefix=os.path.join(prefix, os.path.basename(path))
        path=os.path.dirname(path)
    return ''

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reverse",
        help="Apply a patch in reverse files and/or to the index.",
        action="store_true",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        help="Increase debugging information",
        default=0,
        action="count",
    )

    parser.add_argument(
        "--dry-run",
        help="Print statistics but don't actually apply the patch.",
        action="store_true",
    )

    parser.add_argument(
        "pathToPatch", help="Path to the patch that needs to be applied."
    )

    args = parser.parse_args()
    return args


def apply_reverse(pathToPatch, **kwargs):
    print("Apply in reverse called.  Unimplemented")


def calculate_percentage(diff_lines, line_count, is_removed=False):
    if line_count == 0:
        percentage = 100.0
    else:
        difference_amount = 0
        for line_diff_obj in diff_lines:
            if is_removed:
                difference_amount += line_diff_obj.match_ratio
            else:
                if line_diff_obj.is_missing:
                    difference_amount += 1
                else:
                    difference_amount += 1 - line_diff_obj.match_ratio

        percentage = 100 * (1 - difference_amount / line_count)

    return percentage


def match_found_helper(
    patch,
    diff_obj,
    already_applied_subpatches,
    failed_subpatches_with_matched_code,
    subpatch_name,
    context_decision,
    fileName,
    successful_subpatches,
    context_decision_msg,
):
    added_line_count = 0
    removed_line_count = 0
    context_line_count = 0
    patch_lines = patch.getLines()

    for line in patch_lines:
        if line[0] == natureOfChange.ADDED:
            added_line_count += 1
        elif line[0] == natureOfChange.REMOVED:
            removed_line_count += 1
        else:
            context_line_count += 1

    added_line_applied_percentage = calculate_percentage(
        diff_obj.added_diffs, added_line_count
    )
    removed_line_applied_percentage = calculate_percentage(
        diff_obj.removed_diffs, removed_line_count, is_removed=True
    )
    context_line_match_percentage = calculate_percentage(
        diff_obj.context_diffs, context_line_count
    )

    percentages = [
        added_line_applied_percentage,
        removed_line_applied_percentage,
        context_line_match_percentage,
    ]

    # Exact Patch Has Already Been Applied
    if (
        len(diff_obj.context_diffs) == 0
        and len(diff_obj.added_diffs) == 0
        and len(diff_obj.removed_diffs) == 0
        and len(diff_obj.additional_lines) == 0
    ):
        already_applied_subpatches.append(subpatch_name)

    # No lines between the context lines other than parts of the patch (currently only case where we can apply patches)
    elif len(diff_obj.additional_lines) == 0:
        # We should not apply the patch, context changes affect the code
        if context_decision == CONTEXT_DECISION.DONT_RUN:
            failed_subpatches_with_matched_code.append(
                (
                    percentages,
                    subpatch_name,
                    diff_obj.match_start_line,
                )
            )

        # We try to apply the patch, context changes are not important
        # The case below is only for cases where the context is the only thing that is changed or a line has been completely added or removed with no similar lines
        else:
            new_patch_lines = [patch_lines[0]]
            context_diff_index = 0
            added_diff_index = 0
            removed_diff_index = 0
            for line in patch_lines[1:]:
                if line[0] == natureOfChange.CONTEXT:
                    if (
                        context_diff_index < len(diff_obj.context_diffs)
                        and diff_obj.context_diffs[
                            context_diff_index
                        ].patch_line.strip()
                        == line[1].strip()
                    ):
                        if diff_obj.context_diffs[context_diff_index].is_missing:
                            context_diff_index += 1
                            continue
                        new_context_line = diff_obj.context_diffs[
                            context_diff_index
                        ].file_line
                        new_patch_lines.append(
                            (
                                natureOfChange.CONTEXT,
                                new_context_line,
                            )
                        )
                        context_diff_index += 1
                    else:
                        new_patch_lines.append(line)
                elif line[0] == natureOfChange.ADDED:
                    new_patch_lines.append(line)
                    # if added_diff_index < len(diff_obj.added_diffs) and diff_obj.added_diffs[added_diff_index].patch_line.strip() == line[1].strip():
                    #     new_patch_lines.append(line)
                    #     added_diff_index += 1
                    # else:
                    #     new_patch_lines.append((parse.natureOfChange.CONTEXT, line[1]))
                elif line[0] == natureOfChange.REMOVED:
                    if (
                        removed_diff_index < len(diff_obj.removed_diffs)
                        and diff_obj.removed_diffs[
                            removed_diff_index
                        ].patch_line.strip()
                        == line[1].strip()
                    ):
                        new_patch_lines.append(line)
                        removed_diff_index += 1

            old_patch_lines = patch._lines
            patch._lines = new_patch_lines
            if patch.canApply(fileName):
                successful_subpatches.append([patch, subpatch_name])
            else:
                # print("Issue with current assumption in terms of what patches can be applied")
                failed_subpatches_with_matched_code.append(
                    (
                        percentages,
                        subpatch_name,
                        diff_obj.match_start_line,
                        context_decision_msg,
                        patch
                    )
                )

    else:
        failed_subpatches_with_matched_code.append(
            (
                percentages,
                subpatch_name,
                diff_obj.match_start_line,
                context_decision_msg,
                patch,
            )
        )


def apply(pathToPatch, **kwargs):
    patch_file = parse.PatchFile(pathToPatch)
    patch_file.runPatch(reverse=kwargs['reverse'], dry_run=kwargs['dry_run'])
    if patch_file.runSuccess == True:
        print("Successfully applied")
        return 0
    else:
        error_message = patch_file.runResult
        if kwargs['verbose'] > 0:
            print("Patch failed while it was run with git apply with error:")
            print(error_message)
        else:
            print("Patch failed to apply with git apply.")

        error_message_lines = error_message.split("\n")
        already_exists = set()
        file_not_found = set()
        does_not_apply = set()

        for line in error_message_lines:
            split_line = [s.strip() for s in line.split(":")]
            if line[0:2] == "  ":
                pass
            elif split_line[0] == "error":
                if split_line[2] == "patch does not apply":
                    does_not_apply.add(split_line[1])
                elif split_line[2] == "already exists":
                    already_exists.add(split_line[1])
                elif split_line[2] == "No such file or directory":
                    file_not_found.add(split_line[1])
                elif split_line[2] == 'skipped':
                    # GIT does not translate the file name in this case.
                    filename = os.path.join( findGitPrefix(split_line[1]), split_line[1] )
                    does_not_apply.add(filename)

        patch_file.getPatch()

        # TODO: Handle file that already exists

        # Handling sub patches do not apply
        # try_all_subpatches_input = input("Would you like to try and apply all subpatches? [Y/n] ")
        try_all_subpatches = True
        successful_subpatches = []
        already_applied_subpatches = []
        failed_subpatches_with_matched_code = []
        subpatches_without_matched_code = []
        no_match_patches = []
        applied_by_git_apply = []
        # not_tried_subpatches = []
        if not kwargs['dry_run']:
            see_patches = input(
                "We have found {} subpatches in the patch file. Would you like to see them? [Y/n] ".format(
                    len(patch_file.patches)
                )
            )
            see_patches = see_patches.upper() == "Y"
        else:
            see_patches = False

        for patch in patch_file.patches:
            fileName = patch.getFileName()

            # GIT has the behaviour where it prepends elements to the
            # path in order to get up to the root of the GIT
            # repository.  This means that the output of git apply is
            # not going to have the same file names as the patch file
            # itself.  We need to fix up the name we pulled from the
            # file so it matches the name returned by GIT.
            gitFileName = os.path.join( findGitPrefix(fileName), fileName )

            if see_patches:
                print("\n" + ":".join([fileName, str(patch._lineschanged[0])]))
                print(patch)

            subpatch_name = ":".join([fileName, str(patch._lineschanged[0])])

            if gitFileName in file_not_found:
                correct_loc = check_exist.checkFileExistsElsewhere(patch)
                if correct_loc != None:
                    does_not_apply.add(correct_loc)
                    file_not_found.remove(fileName)
                    fileName = correct_loc
                    patch._fileName = "/" + correct_loc
            elif gitFileName in does_not_apply:
                # [1:] is used to remove the leading slash

                # skip_current_patch = True
                # if not try_all_subpatches:
                #     print("\nFailed Subpatch : {}\n".format(subpatch_name))

                #     print(patch)
                #     skip_current_patch = (input("\nWould you like to try apply this subpatch? [Y/n] ").upper() != "Y")

                # if not try_all_subpatches and skip_current_patch:
                #     not_tried_subpatches.append(subpatch_name)
                #     continue

                # Try applying the subpatch as normal
                subpatch_run_success = patch.canApply(fileName)
                if subpatch_run_success:
                    successful_subpatches.append([patch, subpatch_name])
                else:
                    context_change_obj = cc.context_changes(patch)
                    diff_obj = context_change_obj.diff_obj
                    context_decision = context_change_obj.status
                    context_decision_msg = context_change_obj.messages

                    if diff_obj and diff_obj.match_status == MatchStatus.MATCH_FOUND:
                        match_found_helper(
                            patch,
                            diff_obj,
                            already_applied_subpatches,
                            failed_subpatches_with_matched_code,
                            subpatch_name,
                            context_decision,
                            fileName,
                            successful_subpatches,
                            context_decision_msg,
                        )

                    else:
                        subpatches_without_matched_code.append(subpatch_name)
                        no_match_patches.append(patch)
            elif gitFileName not in already_exists:
                applied_by_git_apply.append(subpatch_name)

        if len(successful_subpatches) > 0:
            print( "-" * 70 )
            print(
                "{} subpatches can be applied successfully:\n".format(
                    len(successful_subpatches)
                )
            )
            if not kwargs['dry_run']:
                start_apply = input(
                    "Would you like to see these patches and try applying them? [Y/n] "
                )
                start_apply = start_apply.upper() == "Y"
            else:
                start_apply = True

            if start_apply:
                for patch in successful_subpatches:
                    if kwargs['verbose'] >= 1:
                        print()
                        print(patch[1])
                        print(patch[0])

                    if not kwargs['dry_run']:
                        apply_subpatch_input = input(
                            "The above subpatch can be applied successfully. Would you like to apply? [Y/n] "
                        )
                        apply_subpatch_input = apply_subpatch_input.upper() == "Y"
                    else:
                        apply_subpatch_input = True

                    success = False
                    if apply_subpatch_input:
                        fileName = patch[0]._fileName
                        patchObj = patch[0]
                        success = patchObj.Apply(fileName, dry_run=kwargs['dry_run'])
                    if success:
                        if kwargs['dry_run']:
                            print( "%s would have been successfully applied (dry run)." % patch[1] )
                        else:
                            print( "%s successfully applied!" % patch[1] )
                    else:
                        print("%s Ignored" % patch[1] )

        if len(failed_subpatches_with_matched_code) > 0:
            # failed_subpatches_with_matched_code.sort()
            print( '\n' + '-' * 70 )
            print(
                "Subpatches that we can't automatically apply, but think we have found where the patch should be applied:\n"
            )

            for (
                percentages,
                sp_name,
                line_number,
                context_decision_msg,
                patch
            ) in failed_subpatches_with_matched_code:
                add_percent, removed_percent, context_percent = percentages
                print("{} - Line Number: {}".format(sp_name, line_number))
                if kwargs['verbose'] >= 2:
                    print( patch )
                print("  Percentage of Added Lines Applied:   {:>6.2f}%".format(add_percent))
                print("  Percentage of Removed Lines Applied: {:>6.2f}%".format(removed_percent))
                print("  Percentage of Context Lines Found:   {:>6.2f}%".format(context_percent))
                print(f"  Context related reason for not applying the patch: {context_decision_msg}")

            print(
                "\nNote that if all added lines are added and removed lines are removed, that means that the context may have changed in ways that affect the code"
            )

        if len(applied_by_git_apply) > 0:
            print("\n" + "-" * 70 )
            print("Subpatches that were applied by git apply:")
            print("\n".join(applied_by_git_apply))

        if len(already_applied_subpatches) > 0:
            print("\n" + "-" * 70 )
            print("Subpatches that were already applied:")
            print("\n".join(already_applied_subpatches))

        if len(subpatches_without_matched_code) > 0:
            print("\n" + "-" * 70 )
            print(
                "Subpatches that did not apply, and we could not find where the patch should be applied:"
            )
            print("\n".join(subpatches_without_matched_code))

        if len(file_not_found) > 0:
            print("\n" + '-' * 70 )
            print("The following files could not be found:")
            print("\n".join(file_not_found))

        # if len(not_tried_subpatches) > 0:
        #     print("\nSubpatches that we did not try and apply:")
        #     print("\n".join(not_tried_subpatches))

        return 1


def main( **kwargs ):
    # If it's a directory full of patches, we are going to run through each file in the directory.
    if not os.path.exists(kwargs['pathToPatch']):
        print( "Invalid path or filename: %s" % kwargs['pathToPatch'] )
        return 1

    if os.path.isdir(kwargs['pathToPatch']):
        arguments = copy.copy(kwargs)
        for file in os.listdir(kwargs['pathToPatch']):
            filename = os.fsdecode(file)
            if filename.endswith("~"):
                continue

            arguments['pathToPatch']=os.path.join(kwargs['pathToPatch'], filename)
            print( "=" * 70 )
            print( "Examining patch: %s\n" % arguments['pathToPatch'] )
            apply( **arguments )
            print( "\n" )
    elif os.path.isfile:
        apply( **kwargs )
    else:
        print( "Not a regular file: %s" % args.pathToPatch )
        return 1


if __name__ == "__main__":
    args = get_args()
    main( **vars(args) )
