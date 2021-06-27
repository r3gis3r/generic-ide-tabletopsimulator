#!/usr/bin/python
# -*- coding: utf-8 -*-

# Print iterations progress
import asyncio
import sys


def print_progress_bar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    print_end="\r",
    **__,
):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)

    sys.stdout.write("\r")
    # the exact output you're looking for:
    sys.stdout.write(f"{prefix} |{bar}| {percent}% {suffix}")
    sys.stdout.flush()
    # Print New Line on Complete
    if iteration == total:
        print(flush=True)


async def main():
    # A List of Items
    items = list(range(0, 57))
    l = len(items)

    # Initial call to print 0% progress
    print_progress_bar(0, l, prefix="Progress:", suffix="Complete", length=50)
    for i, item in enumerate(items):
        # Do stuff...
        await asyncio.sleep(0.2)
        # Update Progress Bar
        print_progress_bar(i + 1, l, prefix="Progress:", suffix="Complete", length=50)


if __name__ == "__main__":

    asyncio.run(main())
