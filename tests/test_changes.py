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

class PatchTests(type):
    def __new__(mcls, name, bases, attrs):
        obj = super().__new__(mcls, name, bases, attrs)

        patchpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'patches', 'changed'))

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

                testcase = self.id().split('.')[-1]

                if testcase in self.errors:
                    expected = self.errors[testcase]
                else:
                    expected = {
                        'message': r'This patch can be applied\.',
                        'canApply': False
                    }

                self.assertRegex(result.messages, expected['message'])

                filename = os.path.join( os.getcwd(), hunk.getFileName() )
                self.assertTrue( os.path.isfile(filename), filename )
                result = hunk.canApply()
                self.assertEqual( result, expected['canApply'], hunk )

        return f

class TestChanges(unittest.TestCase, metaclass=PatchTests):

    errors = {
        'test_function_removed': {
            'message': r'A context match was not found\.',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_string': {
            'message': r'^No context related issues found\.$',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_code_missing': {
            'message': r'^A context match was not found\.$',
            'canApply': precheckStatus.CAN_APPLY
        },
    }

    def setUp(self):
        self.oldcwd=os.getcwd()
        os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self.oldcwd)

if __name__ == "__main__":
    unittest.main()
