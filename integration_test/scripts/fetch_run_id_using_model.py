import sys

from model import get_production_run_id

sys.path.append("/app")  # Assuming the project root is mapped to /app in the container


if __name__ == "__main__":
    run_id = get_production_run_id()
    print(run_id)
