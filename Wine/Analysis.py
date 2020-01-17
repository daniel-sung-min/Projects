import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from scipy import stats
import csv
import matplotlib.pyplot as plt 

data = pd.read_csv('winemag-data_first150k.csv')


x = data.loc[data['price'].notnull(), 'price'].values
y = data.loc[data['price'].notnull(), 'points'].values


regressor = LinearRegression()  
model = regressor.fit(np.matrix(x), np.matrix(y))

r_sq = model.score(x, y)

L = ['coefficient of determination:' , str(r_sq), 'intercept:', str(model.intercept_), 'slope:', str(model.coef_)]

file1 = open("Output.txt","w") 
file1.writelines(L) 
file1.close() #to change file access modes 


