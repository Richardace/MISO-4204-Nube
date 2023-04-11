from flask import Flask
from celery import Celery, Task
from flask import request
from async_tasks import *
from celery.result import AsyncResult
from celery import shared_task
from async_tasks import tasks
from factory import *

app = create_app()
celery_app = app.extensions["celery"]

@app.route("/")
def hello():
    return "<h1 style='color:blue'>eHello There!</h1>"


@app.post("/add")
def start_add() -> dict[str, object]:
    a = request.form.get("a", type=int)
    b = request.form.get("b", type=int)
#    a = 12
#    b = 13
    result = tasks.add_together.delay(a, b)
    return {"result_id": result.id}

@app.get("/result/<id>")
def task_result(id: str) -> dict[str, object]:
    result = AsyncResult(id)
    return {
        "ready": result.ready(),
        "successful": result.successful(),
        "value": str(result.result),
        "a": result.status
    }

@app.errorhandler(Exception)
def exception_handler(error):
    return "!!!!"  + repr(error)

if __name__ == "__main__":
    app.run(host='0.0.0.0')

