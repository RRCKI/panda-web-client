API
************************************

API is intended for non-direct interaction using HTTP requests (unless you prefer using curl to a web browser). The work cycle consists of the following steps:

Obtain a token.
------------------------------------

PanDA Web Client uses `OAuth <http://oauth.net/>`_ for API authentication. After you've acquired username and password, you should get id and secret for your client by logging
into system and going to https://144.206.233.179:8080/api/client. Then you should obtain an access token.

Curl example::

    curl -d "grant_type=password&username=USERNAME&password=PASSWORD&client_id=CLIENT_ID" -X POST https://144.206.233.179:8080/oauth/token

This will return a response, something like::

    {"token_type": "Bearer", "version": "0.1.0", "access_token": "1111111111", "scope": "email", "refresh_token": "2222222222"}

The access token can now be used to interact with the server and perform different operations (see below)::

    curl -H "Authorization: Bearer ACCESS_TOKEN" -X POST http://144.206.233.179:8080/...

Access token functions for a limited period of time. After it expires, you should obtain a new one using refresh token.

Curl example::

    curl -d "grant_type=refresh_token&client_id=CLIENT_ID&refresh_token=REFRESH_TOKEN" -X POST https://144.206.233.179:8080/oauth/token

This will return a new pair of tokens::

    {"token_type": "Bearer", "version": "0.1.0", "access_token": "3333333333", "scope": "email", "refresh_token": "4444444444"}

Distributives.
++++++++++++++++++++++++++++++++++++

Distributives consist of software which processes data. Their list may vary depending on requests from our users. You should know which distributive you want to use on your data,
so obtaining a list of the distributives can be helpful - this can be done by sending GET request to /sw/api::

    curl -H "Authorization: Bearer ACCESS_TOKEN" -X GET http://144.206.233.179:8080/sw/api

Selected distributive will be added to PATH.

.. warning::

    Information below is outdated and should not be used. Stand by for updates.


Upload files.
++++++++++++++++++++++++++++++++++++

Before processing files must be uploaded to the resources. Files intended for the single job are uploaded into single container, which is later specified during job submitting.

1. Request a container::

    POST request to https://144.206.233.179:8080/api/container

You'll get a container guid in return.

2. Container operations.

Set container status to open::

    POST request to https://144.206.233.179:8080/api/container/<guid>/open

Set container status to closed::

    POST request to https://144.206.233.179:8080/api/container/<guid>/close

Get container info::

    GET request to https://144.206.233.179:8080/api/container/<guid>/info

Show files in container::

    GET request to https://144.206.233.179:8080/api/container/<guid>/list

3. File operations.

#To do: finish this.

    POST request to https://144.206.233.179:8080/api/v0.1/upload/<guid>

Post request::

    {
        "files":
        [
            {
                "se": "http",
                "lfn": "http://www.........file1.txt",
                "token": "123"
            },
            {
                "se": "http",
                "lfn": "http://www.........file2.txt",
                "token": "123"
            }
        ]
    }

Where:

* se: from which source file should be uploaded. Correct values include http, ftp and dropbox.
* lfn: path to the file or its name, depending on source.
* token: to do.


Submit jobs.
+++++++++++++++++++++++++++++++++++++

Jobs can be submitted by putting the job information into a json file. Then this json file should be sent via POST request.

json example::

    {
        "distr": "bowtie2",
        "release": 1,
        "parameters": "-num=5",
        "container": "9464902-7345628-8573494",
    }

Curl example::

    curl -H "Authorization: Bearer ACCESS_TOKEN" -vX POST https://144.206.233.179:8080/api/jobs/ -d @test.json

Check your jobs' states.
+++++++++++++++++++++++++++++++++++++

Curl example::

    curl -H "Authorization: Bearer ACCESS_TOKEN" -vX GET https://144.206.233.179:8080/api/jobs/