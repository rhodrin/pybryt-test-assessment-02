import pybryt
from pybryt.annotations.invariants import invariant
from textwrap import indent
import sys
import os
import torch

import nbformat
import ast
from IPython.core.inputtransformer2 import TransformerManager


header = """---
title: Feedback
---
"""

class wrap:

    def __init__(self, tensor):

        self._data = tensor

    def __eq__(self, val):
        if not isinstance(val, wrap):
            return False
        try:
            if self._data.size() == val._data.size():
                return self._data.tolist() == val._data.tolist()
            return False
        except RuntimeError:
            return False

class tensor_invariant(invariant):

    @staticmethod
    def run(values):
        """
        Returns a list of values in which all strings have been lowercased.

        Args:
            values (``list[object]``): acceptable values, either from the initial constructor call
                of the annotation or from the results of other invariants
        
        Returns:
            ``list[object]``: the elements of ``values`` with all strings lowercased
        """
        ret = []
        for v in values:
            if not isinstance(v, torch.Tensor):
                ret.append(v)
            else:
                ret.append(wrap(v))
        return ret






def run_checks(nb_filename, ref_filename, report=None, prefix='', suffix=''):

    if __name__ != "__main__":
        pybryt.utils.save_notebook(nb_filename)

    ref = pybryt.ReferenceImplementation.load(ref_filename)
    nb = nbformat.read(nb_filename, nbformat.NO_CONVERT)

    ### can do surgery here, eg following

    syntax_errors = []
    transformer_mgr = TransformerManager()
    for c in nb.cells:
        if c['cell_type'] == 'code':
            try:
                code = c['source']
                code = transformer_mgr.transform_cell(code)
                ast.parse(code)
            except SyntaxError as e:
                syntax_errors.append(f"\n  - Syntax error: {e.msg}\n    ```\n{indent(e.text, '    ')}\n    ```")
                nb.cells.remove(c)
        if hasattr(c.metadata, 'tags'):
            if 'pybryt_drop' in c.metadata.tags:
                nb.cells.remove(c)

    #nb.cells.insert(0,nbformat.v4.new_code_cell(source='_funcs = set([k for f, k in locals().items() if callable(k)])'))

    for p in prefix:
        nb.cells.insert(0, nbformat.v4.new_code_cell(source=p))
    for s in suffix:
        nb.cells.append(nbformat.v4.new_code_cell(source=s))

    subm = pybryt.StudentImplementation(nb)
    result = subm.check(ref)


    print(f"SUBMISSION: {nb_filename}")

    # res.messages is a list of messages returned by the reference during grading
    if result.correct:
        headline = '## All checks pass'
    else:
        headline = '## Checks are failing'
    messages = "\n".join(result.messages)
    syntax_errors = "".join(syntax_errors) or "None"
    # res.correct is a boolean for whether the reference was satisfied
    message = f"{headline}\n### ERRORS:{syntax_errors}\n### MESSAGES:\n{indent(messages, '  - ')}"

    if report:
        with open('result.md', 'w') as myfile:
            myfile.write(header)
            myfile.write(message)
    else:
        print(message)


code = """
functions = [(k,v) for k, v in locals().items() if callable(v)]
for k,v in functions:
    _tmp='_function_'+k
"""

if __name__ == "__main__":
    run_checks(*sys.argv[1:], suffix=[code])