import matplotlib.pyplot as plt
import numpy as np


def plotter(minRange, maxRange, xMin, xMax, fee, closes, amount, times):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
    ax1.plot(times, fee)
    ax1.set_title("feeUSD")
    if closes[0] < 1:
        ax2.plot(times, [1 / i for i in closes])
    else:
        ax2.plot(times, closes)
    for i in range(len(minRange)):
        ax2.fill_between(np.arange(xMin[i], xMax[i], 1 / 24), minRange[i], maxRange[i], color='r', alpha=.2)
    ax2.set_title("closes_price")
    ax3.plot(times, amount, times, np.array(amount))
    ax3.plot(times, amount, times, np.array(amount) + np.array(fee))
    ax3.set_title("LP_value")
    for ax in (ax1, ax2, ax3):
        ax.grid()
    plt.show()


def plotter_reinvesting(minRange, maxRange, xMin, xMax, fee, closes, amount, times, actual_fee):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
    ax1.plot(times, fee)
    ax1.set_title("feeUSD")
    ax2.plot(times, closes)
    for i in range(len(minRange)):
        ax2.fill_between(np.arange(xMin[i], xMax[i], 1 / 24 / 120), minRange[i], maxRange[i], color='r', alpha=.2)
    ax2.set_title("closes_price")
    ax3.plot(times, amount, times, np.array(amount))
    ax3.plot(times, amount, times, np.array(amount) + np.array(actual_fee))
    ax3.set_title("LP_value")
    for ax in (ax1, ax2, ax3):
        ax.grid()
    plt.savefig('data/fig.png')
    plt.show()


# def plotter_for_distribution(minRange, maxRange, xMin, xMax, fee, closes, amount, times, reinvesting=False):
#     fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
#     ax1.plot(times, fee)
#     ax1.set_title("feeUSD")
#     if closes[0] < 1:
#         ax2.plot(times, [1 / i for i in closes])
#     else:
#         ax2.plot(times, closes)
#     for i in range(len(minRange)):
#         ax2.fill_between(np.arange(xMin[i], xMax[i], 1 / 24), minRange[i], maxRange[i], color='r', alpha=.2)
#     ax2.set_title("closes_price")
#     if reinvesting == False:
#         ax3.plot(times, amount, times, np.array(amount) + np.array(fee))
#     else:
#         ax3.plot(times, amount, times, np.array(amount))
#     ax3.set_title("LP_value")
#     for ax in (ax1, ax2, ax3):
#         ax.grid()
#
#     plt.show()
