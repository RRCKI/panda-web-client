Overview
********

Panda Web Client is an instrument developed in a frame of the MegaPanDA project as a replacement for the standart PanDA client and monitoring system. PanDA client allows to submit jobs, but has several disadvantages:

* Before you can start submitting jobs with PanDA client, you have to setup environment properly, which requires the technical knowledge about the server and other things.
* For each job to be submitted you have to create a python file and thoroughly describe the task in it.

PanDA Web Client was designed as more user-friendly tool for job submitting, while also providing several other services. It consists of the web interface and the API:

* :doc:`Web interface<webclient>` allows users to use the Client directly by means of a web browser.
* :doc:`API<api>` is intended for interaction with other software via HTTP requests.

After you've :doc:`registered<registration>`, both methods can be used to:

1) Upload files to KI's resources for processing.
2) Submit jobs to KI's PanDA server and process the uploaded files.
3) Retrieve the results.
4) Monitor the state of submitted jobs and uploaded files.