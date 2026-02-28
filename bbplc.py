grammar = ["DECLARE", "PRINT", "ADD", "SUB", "MUL","DIV","SQR","POW", "IF", "THEN", "ELSE", "ENDIF", "TOSTR", "TOINT", "LABEL","GOTO"]
dataTypes = ["DB", "DW", "DD", "DP", "DQ", "DT"]

variables = {}
asm_lines = ["format ELF executable 4", "", "entry start", "", "start:"]

tostr_counter = {}

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
    count = tostr_counter.get(name, 0)
    tostr_counter[name] = count + 1
    buf = f"{name}_str_{count}"
    asm_lines.append(f"{buf}: times 12 db 0 ; buffer for {name} TOSTR")
    asm_lines.append(f"; --- TOSTR {name} ---")
    asm_lines.append(f"mov eax, [{name}]")
    asm_lines.append(f"lea edi, [{buf} + 12]")
    asm_lines.append(f"xor ecx, ecx")

    asm_lines.append(f".tostr_loop_{name}_{count}:")
    asm_lines.append(f"xor edx, edx")
    asm_lines.append(f"mov ebx, 10")
    asm_lines.append(f"div ebx")
    asm_lines.append(f"add dl, '0'")
    asm_lines.append(f"dec edi")
    asm_lines.append(f"mov [edi], dl")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"cmp eax, 0")
    asm_lines.append(f"jne .tostr_loop_{name}_{count}")
    asm_lines.append(f"; TO STR done, length in ecx, start at edi")

def toint(name):
    count = tostr_counter.get(name, 0) - 1
    if count < 0:
        count = 0
    buf = f"{name}_str_{count}"
    
    asm_lines.append(f"; --- TOINT {name} ---")
    asm_lines.append(f"lea esi, [{buf}]")
    asm_lines.append(f"mov ecx, 12")
    asm_lines.append(f"xor eax, eax")
    asm_lines.append(f".toint_loop_{name}_{count}:")
    asm_lines.append(f"cmp ecx, 0")
    asm_lines.append(f"je .toint_done_{name}_{count}")
    asm_lines.append(f"mov bl, [esi]")
    asm_lines.append(f"sub bl, '0'")
    asm_lines.append(f"imul eax, eax, 10")
    asm_lines.append(f"add eax, ebx")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"dec ecx")
    asm_lines.append(f"jmp .toint_loop_{name}_{count}")
    asm_lines.append(f".toint_done_{name}_{count}:")
    asm_lines.append(f"mov [{name}], eax")

def print_var(name):
    asm_lines.append(f"mov eax, 4")
    asm_lines.append(f"mov ebx, 1")
    asm_lines.append(f"mov ecx, {name}")
    asm_lines.append(f"mov edx, 4")
    asm_lines.append(f"int 0x80")

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
    asm_lines.append(f"je .pow_done_{op1}")
    asm_lines.append(f"dec ecx")
    asm_lines.append(f".pow_loop_{op1}:")
    asm_lines.append(f"imul eax, ebx")
    asm_lines.append(f"dec ecx")
    asm_lines.append(f"jnz .pow_loop_{op1}")
    asm_lines.append(f".pow_done_{op1}:")
    asm_lines.append(f"mov [{op1}], eax")

def label(name):
    asm_lines.append(f"{name}:")

def goto(name):
    asm_lines.append(f"jmp {name}")

def if_eq(op1, op2, label_true, label_false):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"cmp eax, [{op2}]")
    asm_lines.append(f"je {label_true}")
    asm_lines.append(f"jmp {label_false}")

def if_gt(op1, op2, label_true, label_false):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"cmp eax, [{op2}]")
    asm_lines.append(f"jg {label_true}")
    asm_lines.append(f"jmp {label_false}")

def if_lt(op1, op2, label_true, label_false):
    asm_lines.append(f"mov eax, [{op1}]")
    asm_lines.append(f"cmp eax, [{op2}]")
    asm_lines.append(f"jl {label_true}")
    asm_lines.append(f"jmp {label_false}")


with open('code.bbplc') as f:
    lines = f.readlines()

code = []
for line in lines: 
    line = line.strip()
    if line:
        code.append(line)


label_counter = 0
for line in code:
    words = line.split()
    cmd = words[0]

    if cmd == "DECLARE":
        declare(words[1], words[2], words[4])
    elif cmd == "ADD":
        add(words[1], words[2])
    elif cmd == "SUB":
        sub(words[1], words[2])
    elif cmd == "MUL":
        mul(words[1], words[2])
    elif cmd == "DIV":
        div(words[1], words[2])
    elif cmd == "SQR":
        sqr(words[1])
    elif cmd == "POW":
        pow(words[1], words[2])
    elif cmd == "TOSTR":
        tostr(words[1])
    elif cmd == "TOINT":
        toint(words[1])
    elif cmd == "PRINT":
        print_var(words[1])
    elif cmd == "LABEL":
        label(words[1])
    elif cmd == "GOTO":
        goto(words[1])
    elif cmd == "IF":
        op1 = words[1]
        op = words[2]
        op2 = words[3]
        label_true = f"L_true_{label_counter}"
        label_false = f"L_false_{label_counter}"
        label_counter += 1
        if op == "==":
            if_eq(op1, op2, label_true, label_false)
        elif op == ">":
            if_gt(op1, op2, label_true, label_false)
        elif op == "<":
            if_lt(op1, op2, label_true, label_false)
        asm_lines.append(f"{label_true}: ; THEN branch")
        asm_lines.append(f"{label_false}: ; ELSE branch")

asm_lines.append("mov eax, 1")
asm_lines.append("xor ebx, ebx")
asm_lines.append("int 0x80")

with open("output.asm", "w") as f:
    f.write("\n".join(asm_lines))

print("ASM code generated in output.asm")