from enum import Enum

from src.generic.algo import Algo


class InitialPollingAction(Enum):
    INIT = 'init'
    RECOVER_POSITIONS = 'recover_positions'

class AlgoPolling:
    def __init__(self, algo: Algo, initial_action: InitialPollingAction, interval: int = 30):
        self.algo = algo
        if initial_action == InitialPollingAction.INIT:
            self.algo.setup_initial_positions()
        elif initial_action == InitialPollingAction.RECOVER_POSITIONS:
            self.algo.retrieve_previous_orders()
        self.interval = interval

    def poll(self):
        import time
        while True:
            print("Checking orders...")
            self.algo.check_orders()
            time.sleep(self.interval)
#%%
