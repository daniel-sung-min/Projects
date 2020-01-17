r_sq = str(1)
a = str(2)
b = str(3)




L = ['coefficient of determination:' , r_sq, 'intercept:', a, 'slope:', b]

file1 = open("Output.txt","w") 
file1.writelines(L) 
file1.close() #to change file access modes 
