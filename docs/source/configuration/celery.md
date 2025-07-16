# Celery

We use Celery to handle background tasks in our application. Below are the configuration details for setting up Celery.
By default, Celery is configured to use RabbitMQ as the message broker:

```python
c.CeleryApp.conf = dict(
    broker_url='amqp://localhost',
    result_backend='rpc://',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    broker_connection_retry_on_startup=True,
)
c.CeleryApp.worker_kwargs = dict(concurrency=1, pool="prefork")
```

If you want to setup Grader Service locally and you do not have RabbitMQ or other alternatives (Redis etc.) installed, you can use the following configuration to run Celery  in 'eager' mode:
```python
c.CeleryApp.conf = dict(
    broker_url='amqp://',
    result_backend='rpc://',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    broker_connection_retry_on_startup=True,
    task_always_eager=True,
)