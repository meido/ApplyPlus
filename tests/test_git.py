#!/usr/bin/env python3

import unittest
import sys
import os
import re

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "."))
import scripts.patch_context.context_changes as context
import scripts.patch_apply.patchParser as parse

def GenerateTestName(filename):
    if filename.endswith('.patch'):
        filename = filename[:-6]

    filename = filename.replace('-', '_')
    filename = re.sub( r'[^\w]+', '', filename, flags=re.ASCII )
    return filename

class PatchTests(type):
    def __new__(mcls, name, bases, attrs):
        obj = super().__new__(mcls, name, bases, attrs)

        patchpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'patches', 'git'))

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

            testcase = self.id().split('.')[-1]
            if testcase in self.errors:
                expected = self.errors[testcase]
            else:
                expected = {
                    'result': '^$',
                    'success': True
                }

            patch_file.runPatch(dry_run=True)
            self.assertEqual( patch_file.runSuccess, expected['success'] )
            self.assertRegex( patch_file.runResult, expected['result'] )

        return f

class TestPatches(unittest.TestCase, metaclass=PatchTests):
    errors = {
        'test_name_change': {
            'result': 'No such file or directory',
            'success': False
        },
        'test_not_apply': {
            'result': 'patch does not apply',
            'success': False
        },
        'test_already_applied': {
            'result': 'patch does not apply',
            'success': False
        },
        'test_bad_index': {
            'result': 'Patch contains hunks that were skipped',
            'success': False
        }
    }

    def setUp(self):
        self.oldcwd=os.getcwd()
        os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self.oldcwd)


if __name__ == "__main__":
    unittest.main()
