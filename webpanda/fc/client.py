from datetime import datetime
from flask import g
import os
from webpanda.files import File, Container, Catalog
from webpanda.files.scripts import getScope, getGUID
from webpanda.services import catalog_, files_


def reg_file_in_cont(f, c, t):
    """
    Registers file in catalog
    :param f: File obj
    :param c: Container obj
    :param t: type (input, output, log)
    :return: True/False
    """
    if not isinstance(f, File):
        raise Exception("Illegal file class: not File")
    if not isinstance(c, Container):
        raise Exception("Illegal catalog class: not Container")
    if not isinstance(t, str):
        raise Exception("Illegal type class: not str")
    if t not in ['input', 'output', 'log', 'intermediate']:
        raise Exception("Illegal type value: " + t)

    catalog_item = Catalog()
    catalog_item.file = f
    catalog_item.cont = c
    catalog_item.type = t
    #TODO: Add registration time

    catalog_.save(catalog_item)
    return True


def reg_file_in_cont_byname(lfn, c, t):
    """
    Registers file in catalog
    :param f: File obj
    :param c: Container obj
    :param t: type (input, output, log)
    :return: True/False
    """
    if not isinstance(lfn, str):
        raise Exception("Illegal lfn class: not str")
    if len(lfn) == 0:
        raise Exception("Illegal lfn length: zero")

    # Prepare File obj
    f = File()
    f.scope = getScope(g.username)
    f.attemptn = 0
    f.guid = getGUID(f.scope, None)
    f.lfn = lfn
    f.status = "defined"
    f.transfertask = None
    # f.fsize =
    # md5sum =
    # checksum =
    f.modification_time = datetime.utcnow()
    f.downloaded = 0

    # Save to fc
    files_.save(f)

    if not isinstance(f, File):
        raise Exception("Illegal file class: not File")
    if not isinstance(c, Container):
        raise Exception("Illegal catalog class: not Container")
    if not isinstance(t, str):
        raise Exception("Illegal type class: not str")
    if t not in ['input', 'output', 'log', 'intermediate']:
        raise Exception("Illegal type value: " + t)

    catalog_item = Catalog()
    catalog_item.file = f
    catalog_item.cont = c
    catalog_item.type = t
    # TODO: Add registration time

    catalog_.save(catalog_item)
    return True


def new_file(lfn):
    """
    Creates new file object
    :param lfn: Local FileName
    :return: File obj
    """
    if not isinstance(lfn, str):
        raise Exception("Illegal lfn class: not str")
    if len(lfn) == 0:
        raise Exception("Illegal lfn length: zero")

    # Prepare File obj
    f = File()
    f.scope = getScope(g.username)
    f.attemptn = 0
    f.guid = getGUID(f.scope, None)
    f.lfn = lfn
    f.status = "defined"
    f.transfertask = None
    # f.fsize =
    # md5sum =
    # checksum =
    f.modification_time = datetime.utcnow()
    f.downloaded = 0

    # Save to fc
    files_.save(f)

    return f


def get_file_dir(f):
    """
    Returns relative system path to file's replicas
    :param f: File obj
    :return: str
    """
    if not isinstance(f, File):
        raise Exception("Illegal file class: not File")
    if not f.scope:
        raise Exception("Illegal file object: no scope")
    if not f.guid:
        raise Exception("Illegal file object: no guid")
    return os.path.join('/system', f.scope, f.guid, f.lfn)


def get_file_path(f):
    """
    Returns relative system path to file's replicas
    :param f: File obj
    :return: str
    """
    if not isinstance(f, File):
        raise Exception("Illegal file class: not File")
    if not f.scope:
        raise Exception("Illegal file object: no scope")
    if not f.guid:
        raise Exception("Illegal file object: no guid")
    return os.path.join('/system', f.scope, f.guid)


def save(o):
    if isinstance(o, File):
        files_.save(o)
