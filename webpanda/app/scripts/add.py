from webpanda.app.scripts import updateJobStatus, transferOutputFiles, registerOutputFiles, extractLog

if __name__ == '__main__':
    updateJobStatus()
    ids = registerOutputFiles()
    transferOutputFiles(ids)
    for i in ids:
        extractLog(i)