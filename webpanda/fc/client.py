import commands
from datetime import datetime
from flask import g
import os

from webpanda.files import File, Container, Catalog, Replica
from webpanda.files.common import getScope, getGUID
from webpanda.jobs import Site
from webpanda.services import catalog_, files_, conts_, replicas_


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


def new_replica(f, site):
    """
    Creates new replica of file on se
    :param f: File obj
    :param se: Site obj
    :return: Replica obj
    """
    if not isinstance(f, File):
        raise Exception("Illegal file class: not File")
    if not isinstance(site, Site):
        raise Exception("Illegal file class: not File")

    r = Replica()
    r.original_id = f.id
    r.se = site.se
    r.status = "defined"
    r.lfn = get_file_path(f)
    replicas_.save(r)

    # Add replica to file
    f.replicas.append(r)
    files_.save(f)

    return r


def new_cont():
    """
    Creates new Container object
    :return: Container obj
    """
    # Prepare Container obj
    f = Container()
    f.guid = 'cont.' + commands.getoutput('uuidgen')
    f.status = "open"

    # Save to fc
    conts_.save(f)

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
    """
    Wrapper for .save methods of Service instances
    :param o: object to save
    :return:
    """
    if isinstance(o, File):
        files_.save(o)
        return True
    elif isinstance(o, Container):
        conts_.save(o)
        return True
    elif isinstance(o, Replica):
        replicas_.save(o)
        return True
    return False