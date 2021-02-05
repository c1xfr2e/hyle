#!/usr/bin/env python3
# coding: utf-8

"""
    Simple console progress bar.
"""

# print iterations progress
def print_progress_bar(iteration, total, suffix="", decimals=1, length=100, fill="█", print_end="\r"):
    """
    call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (int)
        total       - Required  : total iterations (int)
        suffix      - Optional  : suffix string (str)
        decimals    - Optional  : positive number of decimals in percent complete (int)
        length      - Optional  : character length of bar (int)
        fill        - Optional  : bar fill character (str)
        print_end   - Optional  : end character (e.g. "\r", "\r\n") (str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)

    prefix = " {}/{}".format(iteration, total)

    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=print_end)
    # print new line on complete
    if iteration >= total:
        print()


if __name__ == "__main__":
    import time

    # a list of items
    items = list(range(0, 57))
    total = len(items)

    # initial call to print 0% progress
    print_progress_bar(0, total, length=50)
    for i, item in enumerate(items):
        # do stuff...
        time.sleep(0.1)
        # update progress bar
        print_progress_bar(i + 1, total, length=50)
