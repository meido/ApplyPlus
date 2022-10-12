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

class ContextPatchTests(type):
    def __new__(mcls, name, bases, attrs):
        obj = super().__new__(mcls, name, bases, attrs)

        patchpath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'patches', 'context'))

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
                        'canApply': precheckStatus.NO_MATCH_FOUND
                    }

                self.assertRegex(result.messages, expected['message'])

                filename = os.path.join( os.getcwd(), hunk.getFileName() )
                self.assertTrue( os.path.isfile(filename), filename )
                result = hunk.canApply()
                self.assertEqual( result, expected['canApply'], hunk )

        return f

class TestContext(unittest.TestCase, metaclass=ContextPatchTests):

    errors = {
        'test_string': {
            'message': r'^This patch can be applied\.$',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_array_index': {
            'message': r'function call on the RHS of an expression\.',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_function': {
            'message': r'represents a function definition\.',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_function_hint': {
            'message': r'^No context related issues found\.$',
            'canApply': precheckStatus.CAN_APPLY
        },
        'test_function_call': {
            'message': r'^This patch can be applied\.$',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_variable_change': {
            'message': r'recommend to not run this patch',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_variable_change_declaration': {
            'message': r'recommend to not run this patch',
            'canApply': precheckStatus.NO_MATCH_FOUND
        },
        'test_variable_change_LHS': {
            'message': r'Since the value on the LHS of the expression may have',
            'canApply': precheckStatus.NO_MATCH_FOUND
        }
    }

    def setUp(self):
        self.oldcwd=os.getcwd()
        os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self.oldcwd)

if __name__ == "__main__":
    unittest.main()
