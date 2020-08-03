from run import *
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    for coin in ALLCOINS:
        data = calc_fullprofit_curve(coin)
        plt.plot(data)
        plt.xlabel(coin)
        plt.ylabel("profit")
        #plt.show()
        plt.savefig(coin+".png")
        plt.clf()
    exit()