#!/bin/bash

. /home/apf/.pandaat_env
source /srv/webclient/bin/activate
export PYTHONPATH=/srv/panda/lib/python2.6/site-packages/pandacommon:/srv/panda/lib/python2.6/site-packages/pandaserver:/srv/panda-web-client/nrckiclient:/cvmfs/atlas.cern.ch/repo/sw/ddm/latest/DQ2Clients/opt/dq2/lib/:/cvmfs/atlas.cern.ch/repo/sw/ddm/rucio-clients/latest/lib/python2.6/site-packages:/cvmfs/atlas.cern.ch/repo/sw/ddm/rucio-clients/latest/externals/kerberos/lib.slc6-x86_64-2.6:/cvmfs/atlas.cern.ch/repo/sw/ddm/rucio-clients/latest/externals/kerberos/lib.slc6-i686-2.6:$PYTHONPATH
export PATH=/cvmfs/atlas.cern.ch/repo/sw/ddm/latest/DQ2Clients/opt/dq2/bin/:$PATH
export X509_USER_PROXY=/tmp/x509up_u500
export X509_CERT_DIR=/etc/grid-security/certificates
export RUCIO_HOME=/cvmfs/atlas.cern.ch/repo/sw/ddm/rucio-clients/latest
export RUCIO_AUTH_TYPE="x509_proxy"
export RUCIO_ACCOUNT=pilot

LSM_HOME=/srv/panda-web-client/nrckiclient
cd $LSM_HOME
python mq/consumer.py method.sendjob

