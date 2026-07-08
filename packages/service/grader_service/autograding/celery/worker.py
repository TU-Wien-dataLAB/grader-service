import argparse
import os

from grader_service.autograding.celery.app import CeleryApp


def main():
    parser = argparse.ArgumentParser(
        prog="Grader Worker", description="Starts celery worker for grader service."
    )
    parser.add_argument("-f", "--config", help="config file path", required=True)

    args = parser.parse_args()

    celery = CeleryApp.instance(config_file=os.path.abspath(args.config))
    app = celery.app

    worker = app.Worker(**celery.worker_kwargs)
    worker.start()


if __name__ == "__main__":
    main()
