from webpanda.core import WebpandaError
from webpanda.files import File, Catalog
from webpanda.services import catalog_


class Client:
    def __init__(self):
        pass

    @staticmethod
    def reg_file_in_cont(f, c, t):
        """
        Registers file in catalog
        :param f: File obj
        :param c: Container obj
        :param t: type (input, output, log)
        :return: True/False
        """
        if not isinstance(f, File):
            raise WebpandaError("Illegal file class")
        if not isinstance(c, Catalog):
            raise WebpandaError("Illegal catalog class")
        if not isinstance(t, str):
            raise WebpandaError("Illegal type class")
        if t not in ['input', 'output', 'log', 'intermediate']:
            raise WebpandaError("Illegal type value: " + t)

        catalog_item = Catalog()
        catalog_item.file = f
        catalog_item.cont = c
        catalog_item.type = t
        #TODO: Add registration time

        catalog_.save(catalog_item)
        return True