import re

grammar = ["DECLARE", "PRINT", "ADD", "SUB", "MUL","DIV","SQR","POW", "IF", "THEN", "ELSE", "ENDIF", "TOSTR", "TOINT", "LABEL","GOTO"]
dataTypes = ["DB", "DW", "DD", "DP", "DQ", "DT"]

variables = {}
declares = []
asm_lines = ["format ELF executable 4", "entry start", ""]

buffers_created = {}
tostr_counter = {}
tostr_buffers = []
RESERVED_NAMES = {"str", "eax", "ebx", "ecx", "edx", "esi", "edi"}

def safe_name(name):
    if name in RESERVED_NAMES:
        return f"var_{name}"
    return name

def parse_declare(line):
    m = re.match(r'DECLARE\s+(\w+)\s+(\w+)\s*=\s*(.+)', line)
    if not m:
        print(f"Ошибка разбора DECLARE: {line}")
        return None, None, None
    var_type, var_name, var_value = m.groups()
    var_value = var_value.strip()
    
    if var_value.startswith("'") and var_value.endswith("'"):
        var_value = var_value[1:-1]
        var_value = ', '.join(str(ord(c)) for c in var_value) + ", 0"
        var_type = "DB"
    return var_type, var_name, var_value

def declare(type, name, value):
    name = safe_name(name)
    variables[name] = value

    if type == "DB":
        declares.append(f"{name}: db {value}")
    elif type == "DW":
        declares.append(f"{name}: dw {value}")
    elif type == "DD":
        declares.append(f"{name}: dd {value}")
    elif type == "DP":
        declares.append(f"{name}: dp {value}")    
    elif type == "DQ":
        declares.append(f"{name}: dq {value}")
    elif type == "DT":
        declares.append(f"{name}: dt {value}")  
    else:
        print(f"Unknown type: {type}")

def tostr(name):
    count = tostr_counter.get(name, 0)
    tostr_counter[name] = count + 1
    buf = safe_name(f"{name}_str_{count}")
    len_var = safe_name(f"{buf}_len")  # переменная длины

    # создаём буфер только один раз
    if buf not in variables:
        declares.append(f"{buf}: times 20 db 0    ; buffer for TOSTR {name} (instance {count})")
        declares.append(f"{len_var}: dd 0         ; длина строки {buf}")
        variables[buf] = "tostr_buffer"
        variables[len_var] = 0

    asm_lines.append(f"; --- TOSTR {name} → {buf} ---")
    asm_lines.append(f"mov eax, [{safe_name(name)}]")
    asm_lines.append(f"lea edi, [{buf} + 19]")
    asm_lines.append(f"mov byte [edi], 0")
    asm_lines.append(f"xor ecx, ecx")
    asm_lines.append(f".tostr_loop_{name}_{count}:")
    asm_lines.append(f"xor edx, edx")
    asm_lines.append(f"mov ebx, 10")
    asm_lines.append(f"div ebx")
    asm_lines.append(f"add dl, '0'")
    asm_lines.append(f"dec edi")
    asm_lines.append(f"mov [edi], dl")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"test eax, eax")
    asm_lines.append(f"jnz .tostr_loop_{name}_{count}")
    asm_lines.append(f"mov [{len_var}], ecx ; сохраняем длину строки")

def toint(name):
    # берём последний созданный буфер
    if name not in buffers_created or not buffers_created[name]:
        count = 0
        print(f"Warning: TOINT {name} без предшествующего TOSTR — используется буфер {name}_str_0")
    else:
        count = buffers_created[name][-1]

    buf = safe_name(f"{name}_str_{count}")
    length_var = safe_name(f"{buf}_len")

    # создаём буфер fallback если нет
    if buf not in variables:
        declares.append(f"{buf}: times 20 db 0    ; buffer for TOINT {name} (fallback)")
        declares.append(f"{length_var}: dd 0")
        variables[buf] = "toint_buffer"

    asm_lines.append(f"; --- TOINT {name} ← {buf} ---")
    asm_lines.append(f"lea esi, [{buf}]")
    asm_lines.append(f"xor eax, eax")
    asm_lines.append(f"xor ecx, ecx")
    asm_lines.append(f".toint_loop_{name}_{count}:")
    asm_lines.append(f"movzx ebx, byte [esi]")
    asm_lines.append(f"cmp bl, 0")
    asm_lines.append(f"je .toint_done_{name}_{count}")
    asm_lines.append(f"sub bl, '0'")
    asm_lines.append(f"cmp bl, 9")
    asm_lines.append(f"ja .toint_done_{name}_{count}")
    asm_lines.append(f"imul eax, eax, 10")
    asm_lines.append(f"add eax, ebx")
    asm_lines.append(f"inc esi")
    asm_lines.append(f"inc ecx")
    asm_lines.append(f"jmp .toint_loop_{name}_{count}")
    asm_lines.append(f".toint_done_{name}_{count}:")
    asm_lines.append(f"mov [{safe_name(name)}], eax")

def print_var(name, is_number=False):
    name = safe_name(name)

    if is_number:
        count = tostr_counter.get(name, 0) - 1
        if count < 0:
            count = 0
        buf = safe_name(f"{name}_str_{count}")
        length_var = safe_name(f"{buf}_len")

        asm_lines.append("mov eax, 4")
        asm_lines.append("mov ebx, 1")
        asm_lines.append(f"lea ecx, [{buf}]")
        asm_lines.append(f"mov edx, [{length_var}]")
        asm_lines.append("int 0x80")
    else:
        value = variables.get(name, "")
        asm_lines.append("mov eax, 4")
        asm_lines.append("mov ebx, 1")
        asm_lines.append(f"mov ecx, {name}")
        if isinstance(value, str) and ',' in value:
            length = len([b for b in value.split(',') if b.strip() != ''])
        else:
            length = 4
        asm_lines.append(f"mov edx, {length}")
        asm_lines.append("int 0x80")

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

code = [line.strip() for line in lines if line.strip()]

label_counter = 0
for line in code:
    words = line.split()
    cmd = words[0]
    if cmd == "DECLARE":
        var_type, var_name, var_value = parse_declare(line)
        if var_type:
            declare(var_type, var_name, var_value)

for line in code:
    words = line.split()
    if not words:
        continue

    cmd = words[0]
    if cmd in ("TOSTR", "TOINT"):
        name = words[1]

        if name not in buffers_created:
            buf_index = 0
            buffers_created[name] = [buf_index]
        else:
            buf_index = max(buffers_created[name]) + 1
            buffers_created[name].append(buf_index)

        buf_name = f"{name}_str_{buf_index}"
        len_name = f"{buf_name}_len"

        if buf_name not in variables:
            declares.append(f"{buf_name}: times 20 db 0 ; buffer for {name}")
            declares.append(f"{len_name}: dd 0 ; length of {buf_name}")
            variables[buf_name] = "tostr_buffer"
            variables[len_name] = 0

asm_lines.extend(declares)
asm_lines.append("start:")

for line in code:
    words = line.split()
    cmd = words[0]
    if cmd == "DECLARE":
        continue
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