"""Run one prompt through the first agent using the ADK Runner."""
import argparse
import asyncio
from examples.first_agent.agent import root_agent
from examples.runtime import run_once


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="?", default="What is the total for 3 bikes at EUR 499.95 each?")
    args = parser.parse_args()
    answer, _ = await run_once(root_agent, args.prompt)
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
