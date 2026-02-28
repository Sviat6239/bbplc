import re

grammar = ["DECLARE", "PRINT", "ADD", "SUB", "MUL","DIV","SQR","POW", "IF", "THEN", "ELSE", "ENDIF", "TOSTR", "TOINT", "LABEL","GOTO"]
dataTypes = ["DB", "DW", "DD", "DP", "DQ", "DT"]

DATA_DEFINE = {1:"db", 2:"dw", 4:"dd", 6:"dp", 8:"dq", 10:"dt"}
DATA_RESERVE = {1:"rb", 2:"rw", 4:"rd", 6:"rf", 8:"rq", 10:"rt"}

variables = {}
declares = []
asm_lines = ["format ELF executable 4", "entry start", ""]
buffers_created = {}
tostr_counter = {}
RESERVED_NAMES = {"str", "eax", "ebx", "ecx", "edx", "esi", "edi"}

def safe_name(name):
    return f"var_{name}" if name in RESERVED_NAMES else name

def get_var_size(name):
    value = variables.get(name)
    if isinstance(value, int):
        size = 4
    elif isinstance(value, str) and ',' in value:
        size = len([b for b in value.split(',') if b.strip()])
    else:
        size = 4
    define = DATA_DEFINE.get(size, "dd")
    return size, define

def parse_declare(line):
    m = re.match(r'DECLARE\s+(\w+)\s+(\w+)\s*=\s*(.+)', line)
    if not m:
        return None, None, None
    var_type, var_name, var_value = m.groups()
    var_value = var_value.strip()
    if var_value.startswith("'") and var_value.endswith("'"):
        var_value = var_value[1:-1]
        var_value = ', '.join(str(ord(c)) for c in var_value) + ", 0"
        var_type = "DB"
    return var_type, var_name, var_value

def declare(type_or_size, name, value=None, reserve=False):
    name = safe_name(name)
    if isinstance(type_or_size, int):
        size = type_or_size
        type_define = DATA_RESERVE[size] if reserve else DATA_DEFINE[size]
    else:
        type_define = type_or_size.upper()
    variables[name] = value if value is not None else 0
    if reserve or value is None:
        declares.append(f"{name}: {type_define} {10 if type_define.startswith('r') else ''} dup(0) ; reserved")
    else:
        declares.append(f"{name}: {type_define} {value}")

def tostr(name):
    size, define = get_var_size(name)
    count = tostr_counter.get(name, 0)
    tostr_counter[name] = count + 1

    buf = safe_name(f"{name}_str_{count}")
    len_var = safe_name(f"{buf}_len")
    ptr_var = safe_name(f"{buf}_ptr")

    if buf not in variables:
        declares.append(f"{buf}: times 20 db 0 ; buffer for {name}")
        declares.append(f"{len_var}: dd 0 ; length of {buf}")
        declares.append(f"{ptr_var}: dd 0 ; pointer to start of {buf}")
        variables[buf] = "tostr_buffer"
        variables[len_var] = 0
        variables[ptr_var] = 0

    buffers_created.setdefault(name, []).append(count)

    asm_lines.append(f"; --- TOSTR {name} ({define}) → {buf} ---")
    if size == 1:
        asm_lines.append(f"movzx eax, byte [{safe_name(name)}]")
    elif size == 2:
        asm_lines.append(f"movzx eax, word [{safe_name(name)}]")
    else:
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
    asm_lines.append(f"mov [{len_var}], ecx")
    asm_lines.append(f"mov [{ptr_var}], edi")

def toint(name):
    if name not in buffers_created or not buffers_created[name]:
        print(f"Warning: TOINT {name} без TOSTR — используем {name}_str_0")
        count = 0
    else:
        count = max(buffers_created[name])

    buf = safe_name(f"{name}_str_{count}")
    ptr_var = safe_name(f"{buf}_ptr")
    len_var = safe_name(f"{buf}_len")
    size, _ = get_var_size(name)

    asm_lines.append(f"; --- TOINT {name} ({size*8}bit) ← {buf} ---")
    
    asm_lines.append(f"cmp dword [{len_var}], 0")
    asm_lines.append(f"je .toint_skip_{name}_{count}")

    asm_lines.append(f"mov esi, [{ptr_var}]")
    asm_lines.append("xor eax, eax")
    asm_lines.append("xor ecx, ecx")

    asm_lines.append(f".toint_loop_{name}_{count}:")
    asm_lines.append("movzx ebx, byte [esi]")
    asm_lines.append("cmp bl, 0")
    asm_lines.append(f"je .toint_done_{name}_{count}")
    asm_lines.append("sub bl, '0'")
    asm_lines.append("cmp bl, 9")
    asm_lines.append(f"ja .toint_done_{name}_{count}")
    asm_lines.append("imul eax, eax, 10")
    asm_lines.append("add eax, ebx")
    asm_lines.append("inc esi")
    asm_lines.append("inc ecx")
    asm_lines.append(f"jmp .toint_loop_{name}_{count}")

    asm_lines.append(f".toint_done_{name}_{count}:")
    if size == 1:
        asm_lines.append(f"mov [{safe_name(name)}], al")
    elif size == 2:
        asm_lines.append(f"mov [{safe_name(name)}], ax")
    else:
        asm_lines.append(f"mov [{safe_name(name)}], eax")

    asm_lines.append(f".toint_skip_{name}_{count}:")

def print_var(name, is_number=False):
    name = safe_name(name)
    size, _ = get_var_size(name)

    if is_number:
        count = tostr_counter.get(name, 0) - 1
        if count < 0:
            count = 0
        buf = safe_name(f"{name}_str_{count}")
        length_var = safe_name(f"{buf}_len")
        ptr_var = safe_name(f"{buf}_ptr")

        asm_lines.append("; --- PRINT number ---")
        asm_lines.append("mov eax, 4")
        asm_lines.append("mov ebx, 1")
        asm_lines.append(f"mov ecx, [{ptr_var}]")
        asm_lines.append(f"mov edx, [{length_var}]")
        asm_lines.append("int 0x80")
    else:
        asm_lines.append("; --- PRINT string ---")
        asm_lines.append("mov eax, 4")
        asm_lines.append("mov ebx, 1")
        asm_lines.append(f"lea ecx, [{name}]")
        asm_lines.append(f"mov edx, {size}")
        asm_lines.append("int 0x80")

def add(op1, op2):
    size, _ = get_var_size(op1)
    if size == 1:
        asm_lines.append(f"mov al, [{op1}]")
        asm_lines.append(f"add al, [{op2}]")
        asm_lines.append(f"mov [{op1}], al")
    elif size == 2:
        asm_lines.append(f"mov ax, [{op1}]")
        asm_lines.append(f"add ax, [{op2}]")
        asm_lines.append(f"mov [{op1}], ax")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"add eax, [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def sub(op1, op2):
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)

    if size1 == 1:
        asm_lines.append(f"mov al, [{op1}]")
        asm_lines.append(f"sub al, [{op2}]")
        asm_lines.append(f"mov [{op1}], al")
    elif size1 == 2:
        asm_lines.append(f"mov ax, [{op1}]")
        asm_lines.append(f"sub ax, [{op2}]")
        asm_lines.append(f"mov [{op1}], ax")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"sub eax, [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def mul(op1, op2):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"imul {reg}, [{op2}]")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"imul eax, [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def div(op1, op2):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"cwd" if size1==2 else "cbw")
        asm_lines.append(f"idiv [{op2}]")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"cdq")
        asm_lines.append(f"idiv dword [{op2}]")
        asm_lines.append(f"mov [{op1}], eax")

def sqr(op1):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"imul {reg}, {reg}")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"imul eax, eax")
        asm_lines.append(f"mov [{op1}], eax")

def pow(op1, op2):
    size1, _ = get_var_size(op1)
    if size1 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"mov cx, [{op2}]")
        asm_lines.append(f"mov bx, {reg}")
        asm_lines.append(f"cmp cx, 0")
        asm_lines.append(f"je .pow_done_{op1}")
        asm_lines.append(f"dec cx")
        asm_lines.append(f".pow_loop_{op1}:")
        asm_lines.append(f"imul {reg}, bx")
        asm_lines.append(f"dec cx")
        asm_lines.append(f"jnz .pow_loop_{op1}")
        asm_lines.append(f".pow_done_{op1}:")
        asm_lines.append(f"mov [{op1}], {reg}")
    else:
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
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)
    
    if size1 <= 2 and size2 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"cmp {reg}, [{op2}]")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"cmp eax, [{op2}]")
    
    asm_lines.append(f"je {label_true}")
    asm_lines.append(f"jmp {label_false}")

def if_gt(op1, op2, label_true, label_false):
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)
    
    if size1 <= 2 and size2 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"cmp {reg}, [{op2}]")
    else:
        asm_lines.append(f"mov eax, [{op1}]")
        asm_lines.append(f"cmp eax, [{op2}]")
    
    asm_lines.append(f"jg {label_true}")
    asm_lines.append(f"jmp {label_false}")

def if_lt(op1, op2, label_true, label_false):
    size1, _ = get_var_size(op1)
    size2, _ = get_var_size(op2)
    
    if size1 <= 2 and size2 <= 2:
        reg = "ax" if size1 == 2 else "al"
        asm_lines.append(f"mov {reg}, [{op1}]")
        asm_lines.append(f"cmp {reg}, [{op2}]")
    else:
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

        buf_name = safe_name(f"{name}_str_{buf_index}")
        len_name = safe_name(f"{buf_name}_len")
        ptr_name = safe_name(f"{buf_name}_ptr")

        if buf_name not in variables:
            declares.append(f"{buf_name}: times 20 db 0 ; buffer for {name}")
            declares.append(f"{len_name}: dd 0 ; length of {buf_name}")
            declares.append(f"{ptr_name}: dd 0 ; pointer to start of {buf_name}")

            variables[buf_name] = "tostr_buffer"
            variables[len_name] = 0
            variables[ptr_name] = 0

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
        name = words[1]
        if name in tostr_counter and tostr_counter[name] > 0:
            print_var(name, is_number=True)
        else:
            print_var(name)
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