# -*- coding: utf-8 -*-
from flask import jsonify, Blueprint, make_response, current_app, request, g, Response
import os

from webpanda.common.NrckiLogger import NrckiLogger
from webpanda.core import WebpandaError
from webpanda.files import Replica, File
from webpanda.files.scripts import getFtpLink, getScope, getGUID, setFileMeta
from webpanda.pilot import route
from webpanda.services import sites_, conts_, files_, replicas_
from webpanda.async.scripts import async_cloneReplica, async_copyReplica
from webpanda.fc.Client import Client as fc


bp = Blueprint('file', __name__, url_prefix="/file")
_logger = NrckiLogger().getLogger("pilot.file")


@route(bp, '/<container_guid>/<lfn>/makereplica/<se>', methods=['POST'])
def new_replica(container_guid, lfn, se):
    """Creates task to make new file replica"""
    nsite = sites_.find(se=se).count()
    if nsite == 0:
        return make_response(jsonify({'error': 'SE not found'}), 400)

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = conts_.first(guid=container_guid)
    cc = container.files
    for c in cc:
        f = c.file
        if f.lfn == lfn:
            rep_num = f.replicas.count()
            replicas = f.replicas
            if rep_num == 0:
                raise WebpandaError('No replicas available')

            ready_replica = None
            for r in replicas:
                if r.se == se:
                    return {'status': r.status}
                if r.se == current_app.config['DEFAULT_SE']:  # and r.status == 'ready'
                    ready_replica = r

            if ready_replica is None:
                ready_replica = replicas[0]

            task = async_cloneReplica.delay(ready_replica.id, se)
            return {'task_id': task.id}
    raise WebpandaError('File not found')


@route(bp, '/<container_guid>/<lfn>/copy', methods=['POST'])
def stage_in(container_guid, lfn):
    """Creates task to copy file in path on se"""
    args = request.form
    if not ('to_se' in args.keys() and 'to_path' in args.keys()):
        raise WebpandaError('Please specify correct request params')

    to_se = args.get('to_se', type=str)
    to_path = args.get('to_path', type=str)

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = conts_.first(guid=container_guid)
    cc = container.files
    for c in cc:
        f = c.file
        if f.lfn == lfn:
            replicas = f.replicas

            for r in replicas:
                if r.status == 'ready':
                    task = async_copyReplica.delay(r.id, to_se, to_path)
                    return {'task_id': task.id}

            raise WebpandaError('No replicas available')
    raise WebpandaError('File not found')


@route(bp, '/<container_guid>/<lfn>/info', methods=['GET'])
def file_info(container_guid, lfn):
    """Returns file metadata"""
    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = conts_.first(guid=container_guid)
    cc = container.files
    for c in cc:
        f = c.file
        if f.lfn == lfn:
            data = {}
            data['lfn'] = f.lfn
            data['guid'] = f.guid
            data['modification_time'] = str(f.modification_time)
            data['fsize'] = int(f.fsize)
            data['adler32'] = f.checksum
            data['md5sum'] = f.md5sum
            return make_response(jsonify(data), 200)
    raise WebpandaError('File not found')


@route(bp, '/<container_guid>/<lfn>/link', methods=['GET'])
def link_file(container_guid, lfn):
    """Returns ftp link to file"""
    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = conts_.first(guid=container_guid)
    site = sites_.first(se=current_app.config['DEFAULT_SE'])

    cc = container.files
    for c in cc:
        f = c.file
        if f.lfn == lfn:
            replicas = f.replicas
            for r in replicas:
                if r.se == site.se and r.status == 'ready':
                    data = {}
                    data['lfn'] = f.lfn
                    data['guid'] = f.guid
                    data['ftp'] = getFtpLink(r.lfn)
                    return make_response(jsonify(data), 200)
    raise WebpandaError('File not found')


@route(bp, '/<container_guid>/<lfn>/save', methods=['POST'])
def file_save(container_guid, lfn):
    """Saves file from request, returns file guid"""
    site = sites_.first(se=current_app.config['DEFAULT_SE'])

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = conts_.first(guid=container_guid)
    if container.status != 'open':
        raise WebpandaError('Unable to upload: Container is not open')
    cc = container.files

    ff = None
    for c in cc:
        f = c.file
        if f.lfn == lfn:
            ff = f
    if not ff:
        ff = File()
        ff.scope = getScope(g.user.username)
        ff.lfn = lfn
        ff.guid = getGUID(ff.scope, ff.lfn)
        ff.status = 'defined'
        files_.save(ff)

        # Register file in container
        fc.reg_file_in_cont(ff, container, 'input')

    path = os.path.join(site.datadir, getScope(g.user.username), container.guid)
    replfn = '/' + os.path.join(getScope(g.user.username), container.guid, ff.lfn)
    destination = os.path.join(path, ff.lfn)

    for r in ff.replicas:
        if r.se == site.se:
            destination = site.datadir + r.lfn
            file_dir = '/'.join(destination.split('/')[:-1])
            if r.status == 'ready':
                if os.path.isfile(destination):  # Check fsize, md5 or adler
                    raise WebpandaError('Replica exists')
                else:
                    r.status = 'broken'
                    replicas_.save(r)
                    raise WebpandaError('Broken replica')
            elif r.status == 'defined':
                try:
                    os.makedirs(file_dir)
                except(Exception):
                    pass
                f = open(destination, 'wb')
                f.write(request.data)
                f.close()

                # Update file info
                setFileMeta(ff.id, destination)

                r.status = 'ready'
                replicas_.save(r)
                return {'guid': ff.guid}
            else:
                raise WebpandaError('Replica status: %s' % r.status)


    replica = Replica()
    if os.path.isfile(destination):
        raise WebpandaError('Unable to upload: File exists')
    try:
        os.makedirs(path)
    except(Exception):
        _logger.debug('Path exists: %s' % path)
    f = open(destination, 'wb')
    f.write(request.data)
    f.close()

    # Update file info
    setFileMeta(ff.id, destination)

    # Create/change replica
    replica.se = site.se
    replica.status = 'ready'
    replica.lfn = replfn
    replica.token = ''
    replica.original = ff
    replicas_.save(replica)
    return {'guid': ff.guid}
    # return make_response(jsonify({'error': 'Illegal Content-Type'}), 400)


@route(bp, '/<container_guid>/<lfn>/fetch', methods=['GET'])
def file_fetch(container_guid, lfn):
    """Returns file in response"""

    if ':' in container_guid:
        container_guid = container_guid.split(':')[-1]
    container = conts_.first(guid=container_guid)
    cc = container.files
    for c in cc:
        f = c.file
        if f.lfn == lfn:
            replicas = f.replicas
            for replica in replicas:
                if replica.se == current_app.config['DEFAULT_SE']:
                    fullpath = current_app.config['DATA_PATH'] + replica.lfn
                    f = open(fullpath, 'r')
                    rr = Response(f.read(), status=200, content_type='application/octet-stream')
                    rr.headers['Content-Disposition'] = 'inline; filename="%s"' % f.lfn
                    rr.headers['Content-MD5'] = f.md5sum
                    f.downloaded += 1
                    files_.save(f)
                    return rr
    raise WebpandaError('File not found')
