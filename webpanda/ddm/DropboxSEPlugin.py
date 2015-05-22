import dropbox
import os
from common.NrckiLogger import NrckiLogger

_logger = NrckiLogger().getLogger("DDM")

class DropboxSEPlugin():
    def __init__(self, params={}):
        self.client = self.getClient(params['auth_key'])

    def getClient(self, auth_key):
        # Get your app key and secret from the Dropbox developer website
        app_key = 'APP_KEY'
        app_secret = 'APP_SECRET'

        # flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)

        # Have the user sign in and authorize this token
        # authorize_url = flow.start()
        # print '1. Go to: ' + authorize_url
        # print '2. Click "Allow" (you might have to log in first)'
        # print '3. Copy the authorization code.'
        # code = raw_input("Enter the authorization code here: ").strip()

        # This will fail if the user enters an invalid authorization code
        # access_token, user_id = flow.finish(auth_key)
        return dropbox.client.DropboxClient(auth_key)

    def get(self, src, dest):
        _logger.debug('DROPBOX: Try to get file from %s to %s' % (src, dest))
        fname = src.split('/')[-1]

        # get file from dropbox to local se
        out = open(os.path.join(dest, fname), 'wb')
        f, metadata = self.client.get_file_and_metadata(src)
        with f:
            out.write(f.read())
        _logger.debug('downloaded: ' + metadata)

    def put(self, src, dest):
        _logger.debug('DROPBOX: Try to put file from %s to %s' % (src, dest))
        # put file from local se to dropbox
        f = open(src, 'rb')
        response = self.client.put_file(dest, f)
        _logger.debug('uploaded: ', response)