grammar = ["DECLARE", "PRINT", "ADD", "SUB", "MUL","DIV","SQR","POW", "IF", "THEN", "ELSE", "ENDIF", "TOSTR", "TOINT", "LABEL","GOTO"]
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

def add(op1, op2):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"add eax, [{op2}]")
    asm_lines.append(f"mov [{op1}], eax")

def sub(op1, op2):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"sub eax, [{op2}]")
    asm_lines.append(f"mov [{op1}], eax")

def mul(op1, op2):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"imul eax, [{op2}]")
    asm_lines.append(f"mov [{op1}], eax")

def div(op1, op2):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"cdq")
    asm_lines.append(f"idiv dword [{op2}]")
    asm_lines.append(f"mov [{op1}], eax")

def sqr(op1):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"imul eax, eax")
    asm_lines.append(f"mov [{op1}], eax")

def pow(op1, op2):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"mov ecx, [{op2}]")
    asm_lines.append(f"mov ebx, eax")
    asm_lines.append(f"cmp ecx, 0")
    asm_lines.append(f"je .pow_done")
    asm_lines.append(f"dec ecx")
    asm_lines.append(f".pow_loop:")
    asm_lines.append(f"imul eax, ebx")
    asm_lines.append(f"dec ecx")
    asm_lines.append(f"jnz .pow_loop")
    asm_lines.append(f".pow_done:")
    asm_lines.append(f"mov [{op1}], eax")

def if_word():
    pass

def else_word():
    pass

def then_word():
    pass

def endif_word():
    pass

def label(name):
    pass

def goto(name):
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
 
