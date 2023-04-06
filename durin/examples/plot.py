import matplotlib.pyplot as plt
import pandas as pd

# load data from CSV file into a pandas DataFrame
df = pd.read_csv('sensor statistics/stats.csv')
text_file = open("sensor statistics/stats.txt", "w")


headers = ["Acce x","Acce y","Acce z",
           "Gyro x","Gyro y","Gyro z",
           "Magn x","Magn y","Magn z",
           "Position x","Position y","Position z",
           "Voltage","UWB ID","UWB distande"]

for header in headers:
    plt.clf()
    print(header)

    # extract column of data from DataFrame
    if header == "Acce x":
        header = "# Acce x"
    data = df[header]
    mean = data.mean()
    std = data.std()

    # create histogram with 1000 bins
    plt.hist(data, bins=500)

    # set title and axis labels
    plt.title('Histogram of '+header)
    plt.xlabel('Value')
    plt.ylabel('Frequency')
    plt.xlim((mean-3*std,mean+3*std))

    # Write mean
    text_file.write(header+"\n")
    text_file.write("Mean: "+str(mean)+"\n")
    text_file.write("Standard deviation: "+str(std)+"\n")
    text_file.write("Standard deviation in %: "+str(std/mean)+"\n")
    text_file.write("\n")
 

    plt.savefig("sensor statistics/plots/"+header+".png")

text_file.close()
# # display the plot
# plt.show()