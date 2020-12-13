from pprint import pprint
from run import *
data = getdata(sys.argv[1])[0]
s = 0
for i in range(len(data)//3):
    print(i, "%.1f"%(sum(data[3*i:3*i+3])*1000), "%.1f"%(s*1000))
    s += sum(data[3*i:3*i+3])
