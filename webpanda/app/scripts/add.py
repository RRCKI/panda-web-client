from app.scripts import updateJobStatus, transferOutputFiles, registerOutputFiles

if __name__ == '__main__':
    updateJobStatus()
    ids = registerOutputFiles()
    transferOutputFiles(ids)