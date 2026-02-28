
grammar = ["DECLARE", "PRINT", "ADD", "SUB", "IF", "THEN", "ELSE", "ENDIF", "FOR", "TO", "DO", "ENDFOR", "TOSTR", "TOINT", "LABEL", "ENDLABEL", "GOTO"]
dataTypes = ["DB", "DW", "DD", "DQ", "DT"]

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

def to():
    pass

def do():
    pass

def endfor():
    pass