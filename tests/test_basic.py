#!/usr/bin/env python3

import unittest
import sys
import os
import re

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "."))
import scripts.patch_context.context_changes as context
import scripts.patch_apply.patchParser as parse
from scripts.enums import precheckStatus

def GenerateTestName(filename):
    if filename.endswith('.patch'):
        filename = filename[:-6]

    filename = filename.replace('-', '_')
    filename = re.sub( r'[^\w]+', '', filename, flags=re.ASCII )
    return filename

class AppliedPatchTests(type):
    def __new__(mcls, name, bases, attrs):
        obj = super().__new__(mcls, name, bases, attrs)

        patchpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'patches', 'applied'))

        for filename in os.listdir(patchpath):
            if not filename.endswith('.patch'):
                continue

            testname = GenerateTestName(filename)
            filename = os.path.join(patchpath, filename)
            if not hasattr(obj, 'test_' + testname):
                setattr(obj, 'test_' + testname, mcls.build_test(filename))

        return obj

    def build_test(test_filename):
        def f(self):
            patch_file = parse.PatchFile(test_filename)
            patch_file.getPatch()

            # There should only be one hunk in this file.
            self.assertEqual( len(patch_file.patches), 1 )

            testcase = self.id().split('.')[-1]
            if testcase in self.errors:
                expected = self.errors[testcase]
            else:
                expected = {
                    'message': r'No context related issues found.',
                    'canApply': precheckStatus.ALREADY_APPLIED
                }

            for hunk in patch_file.patches:
                result = context.context_changes(hunk)
                self.assertEqual(result.messages, expected['message'])

            for hunk in patch_file.patches:
                filename = os.path.join( os.getcwd(), hunk.getFileName() )
                self.assertTrue( os.path.isfile(filename), filename )
                result = hunk.canApply()
                self.assertEqual( result, expected['canApply'], hunk )

        return f

class TestApplied(unittest.TestCase, metaclass=AppliedPatchTests):
    def setUp(self):
        self.oldcwd=os.getcwd()
        os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self.oldcwd)

    errors = {
        'test_remove_offset': {
            'message': r'A context match was not found.',
            'canApply': precheckStatus.ALREADY_APPLIED
        },
        'test_remove_offset_similar2': {
            'message': r'A context match was not found.',
            'canApply': precheckStatus.ALREADY_APPLIED
        },
    }

class PatchTests(type):
    def __new__(mcls, name, bases, attrs):
        obj = super().__new__(mcls, name, bases, attrs)

        patchpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'patches', 'clean'))

        for filename in os.listdir(patchpath):
            if not filename.endswith('.patch'):
                continue

            testname = GenerateTestName(filename)
            filename = os.path.join(patchpath, filename)
            if not hasattr(obj, 'test_' + testname):
                setattr(obj, 'test_' + testname, mcls.build_test(filename))

        return obj

    def build_test(test_filename):
        def f(self):
            patch_file = parse.PatchFile(test_filename)
            patch_file.getPatch()

            # There should only be one hunk in this file.
            self.assertEqual( len(patch_file.patches), 1 )

            for hunk in patch_file.patches:
                result = context.context_changes(hunk)
                self.assertEqual(result.messages, "No context related issues found.")

            for hunk in patch_file.patches:
                filename = os.path.join( os.getcwd(), hunk.getFileName() )
                if not hunk.isNewFile():
                    self.assertTrue( os.path.isfile(filename), filename )
                self.assertTrue( hunk.canApply(), hunk )

        return f

class TestPatches(unittest.TestCase, metaclass=PatchTests):
    def setUp(self):
        self.oldcwd=os.getcwd()
        os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self.oldcwd)

    def test_no_patch(self):
        patch_file = parse.PatchFile("patches/does-not-exist.patch")
        self.assertRaises( FileNotFoundError, patch_file.getPatch )

    def test_no_file(self):
        patch_file = parse.PatchFile("patches/no-file.patch")
        patch_file.getPatch()

        # There should only be one hunk in this file.
        self.assertEqual( len(patch_file.patches), 1 )

        for hunk in patch_file.patches:
            result = context.context_changes(hunk)
            self.assertRegex(result.messages, r'^The file .* does not exist$')

    def test_name_change(self):
        patch_file = parse.PatchFile("patches/name-change.patch")
        patch_file.getPatch()

        # There should only be one hunk in this file.
        self.assertEqual( len(patch_file.patches), 1 )

        for hunk in patch_file.patches:
            result = context.context_changes(hunk)
            self.assertRegex(result.messages, r'^The file .* does not exist$')

    def test_two_changes(self):
        patch_file = parse.PatchFile("patches/clean/two-changes.patch")
        patch_file.getPatch()

        # There should only be one hunk in this file.
        self.assertEqual( len(patch_file.patches), 2 )

if __name__ == "__main__":
    unittest.main()
