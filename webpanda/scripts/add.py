from webpanda.jobs.scripts import update_status, register_outputs

if __name__ == '__main__':
    update_status()
    ids = register_outputs()
    #transferOutputFiles(ids)
    #for i in ids:
    #    extractLog(i)