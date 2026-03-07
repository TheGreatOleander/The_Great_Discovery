#!/usr/bin/env python3
"""
The Great Discovery Engine
Primary runtime entry point
"""

from kernel.discovery_kernel import DiscoveryKernel


def main():
    """
    Boot the Discovery Engine.
    """
    kernel = DiscoveryKernel(
        epochs=100
    )

    kernel.run()


if __name__ == "__main__":
    main()