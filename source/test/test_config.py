import os
import os.path as osp
import sys


def import_context_roots():
    """ enable to import relative parent module"""
    sys.path.append(osp.relpath(osp.dirname(osp.dirname(os.getcwd()))))
