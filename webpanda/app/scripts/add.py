from app.scripts import updateJobStatus, transferOutputFiles, registerOutputFiles

if __name__ == '__main__':
    ids = updateJobStatus()
    registerOutputFiles(ids)
    transferOutputFiles(ids)