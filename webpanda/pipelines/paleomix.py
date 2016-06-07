from webpanda.pipelines import BasicPipeline


class PaleomixPipeline(BasicPipeline):
    """
    1) Получаем форму с списком файлов и типом пайплайна
    2) Сохраняем в объект Pipeline, ставим current_state = start и забываем  TODO: Добавить колонку ifiles
    3) Мастер-скрипт (крон) видит current_state = start и ассинхронно запускает первый скрипт из pipeline_type
    4) Мастер-скрипт в очередном цикле крона проверяет, завершился ли этап current_state и если да, запускает следующий
    """
    def __init__(self, pp, params):
        BasicPipeline.__init__(self, pp, params)


