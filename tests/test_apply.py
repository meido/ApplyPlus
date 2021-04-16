#!/usr/bin/env python3

import unittest
import sys
import os
import re

from io import StringIO
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".")))
import scripts.patch_apply.apply as apply

class TestApplied(unittest.TestCase):
    def setUp(self):
        self.oldcwd=os.getcwd()
        os.chdir(os.path.dirname(__file__))

    def tearDown(self):
        os.chdir(self.oldcwd)

    def test_no_file(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            apply.main( pathToPatch='patches/does-not-exist.patch',
                        dry_run=True
            )

            self.assertRegex(fakeOutput.getvalue().strip(),
                             '^Invalid path or filename')

    def test_multiple_patches(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            apply.main( pathToPatch='patches/clean',
                        dry_run=True,
                        reverse=False,
                        verbose=0,
            )

            # How many files are in the directory?
            numPatches=0
            for filename in os.listdir('patches/clean'):
                if filename.endswith('~'):
                    continue
                numPatches += 1

            self.assertEqual( fakeOutput.getvalue().count('Examining patch:'),
                              numPatches )

    def test_applied(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            apply.main( pathToPatch='patches/applied/add-line.patch',
                        dry_run=True,
                        reverse=False,
                        verbose=0,
            )

            self.assertRegex( fakeOutput.getvalue(), 'Patch failed to apply with git apply' )

    def test_context_comment(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            apply.main( pathToPatch='patches/context/comment.patch',
                        dry_run=True,
                        reverse=False,
                        verbose=0,
            )

            self.assertRegex( fakeOutput.getvalue(), 'Patch failed to apply with git apply' )
            self.assertRegex( fakeOutput.getvalue(), '1 subpatches can be applied successfully:' )
            self.assertRegex( fakeOutput.getvalue(), 'would have been successfully applied \(dry run\)' )

    def test_context_function(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            apply.main( pathToPatch='patches/context/function.patch',
                        dry_run=True,
                        reverse=False,
                        verbose=0,
            )

            self.assertRegex( fakeOutput.getvalue(), 'Patch failed to apply with git apply' )
            self.assertRegex( fakeOutput.getvalue(), '1 subpatches can be applied successfully:' )
            self.assertRegex( fakeOutput.getvalue(), 'would have been successfully applied \(dry run\)' )

    def test_applied_offset(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            apply.main( pathToPatch='patches/applied/remove-offset.patch',
                        dry_run=True,
                        reverse=False,
                        verbose=0,
            )

            self.assertRegex( fakeOutput.getvalue(), 'Patch failed to apply with git apply' )
            self.assertRegex( fakeOutput.getvalue(), 'Subpatches that were already applied:' )

    def test_findGitPrefix(self):
        paths = [
            'patches',
            'test_apply.py',
            'non-existant-file',
            'non-existant-dir/non-existant-file'
        ]
        for path in paths:
            self.assertEqual( apply.findGitPrefix(path), "tests", path )

    def test_bad_index(self):
        with patch('sys.stdout', new=StringIO()) as fakeOutput:
            apply.main( pathToPatch='patches/git/bad-index.patch',
                        dry_run=True,
                        reverse=False,
                        verbose=2,
            )

            self.assertNotRegex( fakeOutput.getvalue(), 'Subpatches that were applied by git apply:' )
            self.assertRegex( fakeOutput.getvalue(), 'Subpatches that did not apply, and we could not find where the patch should be applied' )


if __name__ == "__main__":
    unittest.main()
