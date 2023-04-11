from celery import shared_task

@shared_task(ignore_result=False,name="add_together")
def add_together(a: int, b: int) -> int:
    return a + b
