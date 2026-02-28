grammar = ["DECLARE", "PRINT", "ADD", "SUB", "IF", "THEN", "ELSE", "ENDIF", "TOSTR", "TOINT", "LABEL","GOTO"]
dataTypes = ["DB", "DW", "DD", "DP", "DQ", "DT"]

code = []

variables = {}
asm_lines = []

def declare(type, name, value):
    variables[name] = value
    if type == "DB":
        asm_lines.append(f"{name}: db {value}")
    elif type == "DW":
        asm_lines.append(f"{name}: dw {value}")
    elif type == "DD":
        asm_lines.append(f"{name}: dd {value}")
    elif type =="DP":
        asm_lines.append(f"{name}: dp {value}")    
    elif type == "DQ":
        asm_lines.append(f"{name}: dq {value}")
    elif type == "DT":
        asm_lines.append(f"{name}: dt {value}")
    else:
        print(f"Unknown type: {type}")       

def tostr(name):
    pass

def toint(name):
    pass

def print(name):
    pass

def add(perand1, operand2):
    pass

def sub(operand1, operand2):
    pass

def if_word():
    pass

def else_word():
    pass

def then_word():
    pass

def endif_word():
    pass


with open('code.bbplc') as f:
    lines = f.readlines()



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
 
