from instructions import *

with open('code.bbplc') as f:
    lines = f.readlines()

code = []

for line in lines: 
    line = line.rstrip("\n")
    words = line.split()
    words.append(0)
    code.append(words)

i = 0

while i < len(code):
    if code[i][0] == 0:
        del code[i]
    else:
        i += 1    

for row in code: 
    print(row)    
 
