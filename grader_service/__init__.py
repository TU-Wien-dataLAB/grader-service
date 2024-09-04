import sys

from grader_service._version import __version__
from grader_service.main import GraderService

main = GraderService.launch_instance

if __name__ == "__main__":
    main(sys.argv)
