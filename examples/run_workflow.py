"""Offline Workflow CLI."""
import argparse
import asyncio
from examples.function_workflow.agent import root_agent
from examples.runtime import run_once


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="?", default="  Global   Bike sells bicycles.  ")
    args = parser.parse_args()
    answer, _ = await run_once(root_agent, args.text)
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
