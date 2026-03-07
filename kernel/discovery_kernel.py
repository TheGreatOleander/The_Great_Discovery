from great_discovery.driver import run_epoch


class DiscoveryKernel:
    """
    Main loop controller for The Great Discovery system.
    Runs the discovery engine for a specified number of epochs.
    """

    def __init__(self, epochs=100):
        self.epochs = epochs

    def run(self):
        print("Starting Discovery Kernel...\n")

        for epoch in range(self.epochs):
            print(f"Epoch {epoch + 1}/{self.epochs}")
            run_epoch(epoch)

        print("\nDiscovery run complete.")