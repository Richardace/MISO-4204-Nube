from flask import Flask

from celery import Celery, Task

from async_tasks import *

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://54.211.21.168:6379",
            result_backend="redis://54.211.21.168:6379",
            task_ignore_result=True,
            include = ('async_tasks.tasks')
        ),
    )
    app.config.from_prefixed_env()
    app.config['UPLOAD_FOLDER'] = "./uploads/"
    celery_init_app(app)
    return app

