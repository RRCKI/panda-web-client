import os
import commands
from datetime import datetime

from flask import g

from webpanda.files import File, Container, Catalog, Replica
from webpanda.jobs import Site
from webpanda.services import catalog_, files_, replicas_, conts_


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


def get_file_path(f):
    """
    Returns relative system path to file's replicas
    :param f: File obj
    :return: str
    """
    return os.path.join(get_file_dir(f), f.lfn)


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
    return os.path.join('/system', f.scope, f.guid)


def save(o):
    if isinstance(o, File):
        files_.save(o)
    if isinstance(o, Container):
        conts_.save(o)
    if isinstance(o, Replica):
        replicas_.save(o)


def getScope(username):
    """
    Get default user's scope
    :param username:
    :return: str
    """
    return 'web.' + username


def getGUID(scope, lfn):
    guid = commands.getoutput('uuidgen')
    return scope + '_' + guid