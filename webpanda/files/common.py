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
