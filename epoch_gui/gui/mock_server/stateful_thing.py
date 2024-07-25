from enum import Enum
import threading

from gui.mock_server.call_executable import run_headless

PATH_TO_EPOCH = "../Epoch"


class Status(Enum):
    READY = 1
    RUNNING = 2
    FINISHED = 3


class StatefulThing:
    def __init__(self):
        # track progress crudely with a dictionary to hold results and an enum
        self.status = Status.READY
        self.results = {}

    def get_full_status(self):
        info = {
            "status": self.status.name
        }

        if self.status == Status.RUNNING:
            info["num_scenarios"] = 9999

        if self.status == Status.FINISHED:
            info["results"] = self.results

        print("INFO\n", info)
        return info

    def run_epoch(self):
        if self.status == Status.READY:
            print("Running Epoch")
            self.status = Status.RUNNING
            threading.Thread(target=self._run_epoch_internal).start()

    def _run_epoch_internal(self):
        self.results = run_headless(
            PATH_TO_EPOCH,
            input_dir="./mock_server/mock_data/InputData",
            config_dir="./mock_server/mock_data/Config",
            output_dir="./mock_server/mock_data/OutputData"
        )
        self.status = Status.FINISHED
        print(self.results)

    def get_results(self):
        return self.results


