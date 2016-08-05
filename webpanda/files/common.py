import commands


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


def getFullPath(scope, dataset, lfn):
    if ':' in dataset:
        return '/' + '/'.join([dataset.split(':')[0], '.sys', dataset.split(':')[1], lfn])
    return '/' + '/'.join([scope, '.sys', dataset, lfn])