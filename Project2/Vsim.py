
import sys
# 1. Declaration/Initialization
# Dictionary to store memory data values
memory_data = {}
# Dictionary to map instructions with their addresses for fetching and execution
inst_memory = {}
# Flags and counters for pipeline control
is_data_active = False
execute_process= True
is_branch_stalled = False
registers = [0] * 32
pc_current_address = 256
cycle_count = 1
# Queue structures for managing pipeline stages
branch_wait_queue = []
branch_exec_queue = []
Pre_issue_Queue = []
Pre_ALU1_Queue = []
Pre_ALU2_Queue = []
Post_ALU2_Queue = []
Pre_MEM_Queue = []
Post_MEM_Queue = []
writeBuffer = []
# Helper functions
def twos_complement(binary_instruction, bits=32):
return str(int(binary_instruction, 2) - (1 << bits))
def detect_data_hazards(instrParsed, Queue_p):
# Instruction type and operand extraction
# Parse the instruction type (e.g., "add") and operands (registers and
immediate values)
opType = instrParsed.split()[0]
operands = instrParsed.split()[1:]
rs1,rs2 = 0,0 # Source register initializations
# Extract source registers based on instruction type
# Case 1: Handle branching and jump instructions
if opType in ["beq", "bne", "blt","jal"]:
rdx = None
if "x" in operands[0]:
rs1 = int(operands[0][1:].replace(',', ''))
if "x" in operands[1]:
rs2 = int(operands[1][1:].replace(',', ''))
# Case 2: Handle arithmetic and logical instructions
elif opType in ["add", "sub", "and", "or","addi", "andi", "ori", "sll", "sra"]:
rdx = int(operands[0][1:-1])
if "x" in operands[1]:
rs1 = int(operands[1][1:].replace(',', ''))
if "x" in operands[2]:
rs2 = int(operands[2][1:].replace(',', ''))
# Case 3: Handle load/store instructions (which often have memory offsets)
elif opType in ["lw", "sw"]:
rdx = None
rs1 = int(operands[1][1:][4:-1])
rs2 = int(operands[0][1:-1])
# If instruction type is unrecognized, assume no hazard and return False
else:
return False
# Check for data hazards with entries in the main pipeline queue
for entry in Queue_p:
if entry:
entryOpType = entry.split()[0]
entry_operands = entry.split()[1:]
if entryOpType in ["add", "sub", "addi", "andi", "ori", "sll", "sra",
"lw", "jal","or","and"]:
rd = int(entry_operands[0][1:].replace(',', ''))
else:
continue
# Check if current instruction sources (rs1, rs2, rdx) match the
entry's destination (RAW hazard)
if (rs1 and rs1 == rd) or (rs2 and rs2 == rd) or (rdx == rd):
return True # Hazard detected if sources match any destination
register
# Repeat hazard checks for each of the pipeline queues (Pre_ALU1, Pre_ALU2,
Post_ALU2, Pre_MEM, Post_MEM)
for entry in Pre_ALU1_Queue:
if entry:
entryOpType = entry.split()[0]
entry_operands = entry.split()[1:]
if entryOpType in ["add", "sub", "addi", "andi", "ori", "sll", "sra",
"lw", "jal","or","and"]:
rd = int(entry_operands[0][1:].replace(',', ''))
else:
continue
if (rs1 == rd) or (rs2 and rs2 == rd) or (rdx == rd):
return True
for entry in Pre_ALU2_Queue:
if entry:
entryOpType = entry.split()[0]
entry_operands = entry.split()[1:]
if entryOpType in ["add", "sub", "addi", "andi", "ori", "sll", "sra",
"lw", "jal","or","and"]:
rd = int(entry_operands[0][1:].replace(',', ''))
else:
continue
if (rs1 == rd) or (rs2 and rs2 == rd) or (rdx == rd):
return True
for entry in Post_ALU2_Queue:
if entry:
entryOpType = entry.split()[0]
entry_operands = entry.split()[1:]
if entryOpType in ["add", "sub", "addi", "andi", "ori", "sll", "sra",
"lw", "jal","or","and"]:
rd = int(entry_operands[0][1:].replace(',', ''))
else:
continue
if (rs1 == rd) or (rs2 and rs2 == rd) or (rdx == rd):
return True
for entry in Pre_MEM_Queue:
if entry:
entryOpType = entry.split()[0]
entry_operands = entry.split()[1:]
if entryOpType in ["add", "sub", "addi", "andi", "ori", "sll", "sra",
"lw", "jal","or","and"]:
rd = int(entry_operands[0][1:].replace(',', ''))
else:
continue
if (rs1 == rd) or (rs2 and rs2 == rd) or (rdx == rd):
return True
for entry in Post_MEM_Queue:
if entry:
entryOpType = entry.split()[0]
entry_operands = entry.split()[1:]
if entryOpType in ["add", "sub", "addi", "andi", "ori", "sll", "sra",
"lw", "jal","or","and"]:
rd = int(entry_operands[0][1:].replace(',', ''))
else:
continue
if (rs1 == rd) or (rs2 and rs2 == rd) or (rdx == rd):
return True
# Lastly, check the write buffer for potential hazards
for entry in writeBuffer:
if entry:
entryOpType = entry.split()[0]
entry_operands = entry.split()[1:]
if entryOpType in ["add", "sub", "addi", "andi", "ori", "sll", "sra",
"lw", "jal","or","and"]:
rd = int(entry_operands[0][1:].replace(',', ''))
else:
continue
if (rs1 == rd) or (rs2 and rs2 == rd) or (rdx == rd):
return True
return False # Return False if no hazards are detected across all queues
# 2. Disassemble functions - Function to disassemble category 1/2/3/4 instructions
def disassemble_cat1(binary_instruction):
opcode_dict = {
"00000": "beq",
"00001": "bne",
"00010": "blt",
"00011": "sw"
}
opcode = binary_instruction[25:30]
rs1 = int(binary_instruction[12:17], 2)
rs2 = int(binary_instruction[7:12], 2)
imm_11_5 = int(binary_instruction[0:7], 2)
imm_4_0 = int(binary_instruction[20:25], 2)
offset = (imm_11_5 << 5) | imm_4_0
if opcode in opcode_dict:
instruction = opcode_dict[opcode]
if instruction == "sw":
return f"{instruction} x{rs1}, {offset}(x{rs2})"
else:
return f"{instruction} x{rs1}, x{rs2}, #{offset}"
else:
raise ValueError(f"Unknown opcode: {opcode}")
def disassemble_cat2(instruction):
opcode = instruction[25:30]
rd = int(instruction[20:25], 2)
rs1 = int(instruction[12:17], 2)
rs2 = int(instruction[7:12], 2)
opcode_map = {
"00000": "add",
"00001": "sub",
"00010": "and",
"00011": "or",
}
if opcode in opcode_map:
mn_inst_code = opcode_map[opcode]
return f"{mn_inst_code} x{rd}, x{rs1}, x{rs2}"
else:
raise ValueError(f"Unknown opcode: {opcode}")
def disassemble_cat3(binary_instruction):
opcode_dict = {
"00000": "addi",
"00001": "andi",
"00010": "ori",
"00011": "sll",
"00100": "sra",
"00101": "lw"
}
opcode = binary_instruction[25:30]
rd = int(binary_instruction[20:25], 2)
rs1 = int(binary_instruction[12:17], 2)
imm = int(binary_instruction[0:12], 2) if int(binary_instruction[0]) == 0 else
int(twos_complement(binary_instruction[0:12], 12), 12)
if opcode in opcode_dict:
instruction = opcode_dict[opcode]
if instruction in ["sll", "sra"]:
return f"{instruction} x{rd}, x{rs1}, #{imm}"
elif instruction == "lw":
return f"{instruction} x{rd}, {imm}(x{rs1})"
else:
return f"{instruction} x{rd}, x{rs1}, #{imm}"
else:
raise ValueError(f"Unknown opcode: {opcode}")
def disassemble_cat4(binary_instruction):
opcode_dict = {
"00000": "jal",
"11111": "break"
}
opcode = binary_instruction[25:30]
rd = int(binary_instruction[20:25], 2)
imm = int(binary_instruction[0:20], 2) if int(binary_instruction[0]) == 0 else
twos_complement(binary_instruction[0:20], 20)
if opcode in opcode_dict:
instruction = opcode_dict[opcode]
if instruction == "break":
return instruction
return f"{instruction} x{rd}, #{imm}"
else:
raise ValueError(f"Unknown opcode: {opcode}")
# 3. Multiple Stages functions - Function to define fetch/decode, issue, alu,
memory, write stage
instructionPointer = 0
def instructionFetch():
global execute_process, is_branch_stalled, pc_current_address, Pre_issue_Queue,
cycle_count, instructionPointer
current_instructions = 0
while current_instructions < 2 and execute_process:
if len(branch_exec_queue) != 0:
outputStateSnapshot(cycle_count)
cycle_count += 1
branch_exec_queue.pop()
increment_pc = True
if len(Pre_issue_Queue) >= 4:
break
binary_instruction, instrParsed = inst_memory.get(pc_current_address,
(None, None))
if not binary_instruction or "break" in instrParsed:
execute_process = False
break
# Handle branch instructions with hazard detection
if any(branch in instrParsed for branch in ["jal", "beq", "bne", "blt"]):
if detect_data_hazards(instrParsed, Pre_issue_Queue):
if not branch_wait_queue:
branch_wait_queue.append(instrParsed)
is_branch_stalled = True
break
else:
is_branch_stalled = True
branch_exec_queue.append(instrParsed)
operands = instrParsed.split()[1:]
rs1_value = registers[int(operands[0][1:].replace(',', ''))]
rs2_value = registers[int(operands[1][1:].replace(',', ''))]
if "beq" in instrParsed and rs1_value == rs2_value or \
"bne" in instrParsed and rs1_value != rs2_value or \
"blt" in instrParsed and rs1_value < rs2_value:
offset = int(operands[2][1:])
pc_current_address += offset << 1
increment_pc = False
if "jal" in instrParsed:
registers[int(operands[0][1:].replace(',', ''))] =
pc_current_address + 4
offset = int(operands[1][1:])
pc_current_address += offset << 1
increment_pc = False
if instrParsed in branch_wait_queue:
branch_wait_queue.remove(instrParsed)
else:
outputStateSnapshot(cycle_count)
cycle_count += 1
instructionPointer = 1
branch_exec_queue.pop()
else:
Pre_issue_Queue.append(instrParsed)
current_instructions += 1
if increment_pc:
pc_current_address += 4
def instructionIssue():
global Pre_issue_Queue, Pre_ALU1_Queue, Pre_ALU2_Queue, Post_ALU2_Queue
issued_counter = 0
i = 0
while i < len(Pre_issue_Queue) and issued_counter < 3:
instruction = Pre_issue_Queue[i]
if instruction:
opcode = instruction.split()[0]
if opcode in ["lw", "sw"] and len(Pre_ALU1_Queue) < 1 and not
detect_data_hazards(instruction, Pre_issue_Queue[:i]):
Pre_ALU1_Queue.append(instruction)
Pre_issue_Queue.pop(i)
issued_counter += 1
continue
elif opcode in ["add", "sub", "addi", "and", "or", "andi", "ori",
"sll", "sra"] and len(Pre_ALU2_Queue) < 1:
if not detect_data_hazards(instruction, Pre_issue_Queue[:i]):
Pre_ALU2_Queue.append(instruction)
Pre_issue_Queue.pop(i)
issued_counter += 1
continue
i += 1
def instructionALU():
if Pre_ALU1_Queue:
instruction = Pre_ALU1_Queue.pop(0)
Pre_MEM_Queue.append(instruction)
if Pre_ALU2_Queue:
instruction = Pre_ALU2_Queue.pop(0)
Post_ALU2_Queue.append(instruction)
def instructionLoadMemory():
for i in Pre_MEM_Queue:
if i[:2] != "sw" and len(Post_MEM_Queue) == 0:
Post_MEM_Queue.append(i)
Pre_MEM_Queue.remove(i)
else:
instruction = Pre_MEM_Queue.pop(0)
run_pipeline(instruction)
def run_pipeline(instrParsed):
global pc_current_address,registers, memory_data
operand_components = instrParsed.split()
opcode = operand_components[0]
def process_operand(op):
if "(" in op:
return int(op.replace('x', '').replace(',', '').replace('#', '')[4:-1])
return int(op.replace('x', '').replace(',', '').replace('#', ''))
operands = [process_operand(op) for op in operand_components[1:]]
# using if-else or scoreboarding or t algo
if opcode == "beq":
rs1, rs2 = operands
if registers[rs1] == registers[rs2]:
pc_current_address += offset<<1
elif opcode == "bne":
rs1, rs2 = operands
if registers[rs1] != registers[rs2]:
pc_current_address += offset<<1
elif opcode == "blt":
rs1, rs2 = operands
if registers[rs1] < registers[rs2]:
pc_current_address += offset<<1
elif opcode == "sw":
rs1, rs2, offset = operands + [int(operand_components[2][:3])]
memory_data[registers[rs2] + offset] = registers[rs1]
elif opcode == "add":
rd, rs1, rs2 = operands
registers[rd] = registers[rs1] + registers[rs2]
elif opcode == "sub":
rd, rs1, rs2 = operands
registers[rd] = registers[rs1] - registers[rs2]
elif opcode == "and":
rd, rs1, rs2 = operands
registers[rd] = registers[rs1] & registers[rs2]
elif opcode == "or":
rd, rs1, rs2 = operands
registers[rd] = registers[rs1] | registers[rs2]
elif opcode == "addi":
rd, rs1, imm = operands
registers[rd] = registers[rs1] + imm
elif opcode == "andi":
rd, rs1, imm = operands
registers[rd] = registers[rs1] & imm
elif opcode == "ori":
rd, rs1, imm = operands
registers[rd] = registers[rs1] | imm
elif opcode == "sll":
rd, rs1, imm = operands
registers[rd] = registers[rs1] << imm
elif opcode == "sra":
rd, rs1, imm = operands
registers[rd] = registers[rs1] >> imm
elif opcode == "lw":
rd, rs1,offset = operands + [int(operand_components[2][:3])]
registers[rd] = memory_data[registers[rs1] + offset]
registers = [int(i) for i in registers]
def instructionWriteCommit():
global Post_MEM_Queue, Post_ALU2_Queue,writeBuffer
writeBuffer = Post_MEM_Queue + Post_ALU2_Queue
if Post_MEM_Queue:
instruction = Post_MEM_Queue.pop(0)
run_pipeline(instruction)
if Post_ALU2_Queue:
instruction = Post_ALU2_Queue.pop(0)
run_pipeline(instruction)
# 4. Printing the pipeline output functions - Function to print pipeline output in
simulation.txt file
output = open("simulation.txt","w")
def outputStateSnapshot(cycle_count):
global branch_exec_queue
output.write('--------------------\n')
output.write(f"Cycle {cycle_count}:\n")
output.write("\n") # Added blank line before "IF Unit"
output.write("IF Unit:\n")
# Handle empty Waiting and Executed
output.write("\t")
if branch_wait_queue:
output.write(f"Waiting: [{' '.join(str(x) for x in branch_wait_queue)}]\n")
else:
output.write("Waiting:\n")
output.write("\t")
if branch_exec_queue:
output.write(f"Executed: [{' '.join(str(x) for x in branch_exec_queue)}]\
n")
else:
output.write("Executed:\n")
output.write("Pre-Issue Queue:\n")
for i in range(4):
output.write("\t")
if i < len(Pre_issue_Queue) and Pre_issue_Queue[i] is not None:
output.write(f"Entry {i}: [{Pre_issue_Queue[i]}]\n")
else:
output.write(f"Entry {i}:\n")
output.write("Pre-ALU1 Queue:\n")
for i in range(2):
output.write("\t")
if i < len(Pre_ALU1_Queue) and Pre_ALU1_Queue[i] is not None:
output.write(f"Entry {i}: [{Pre_ALU1_Queue[i]}]\n")
else:
output.write(f"Entry {i}:\n")
output.write("Pre-MEM Queue:")
if Pre_MEM_Queue:
output.write(f" [{' '.join(str(x) for x in Pre_MEM_Queue)}]")
output.write("\n")
output.write("Post-MEM Queue:")
if Post_MEM_Queue:
output.write(f" [{' '.join(str(x) for x in Post_MEM_Queue)}]")
output.write("\n")
output.write("Pre-ALU2 Queue:\n")
for i in range(2):
output.write("\t")
if i < len(Pre_ALU2_Queue) and Pre_ALU2_Queue[i] is not None:
output.write(f"Entry {i}: [{Pre_ALU2_Queue[i]}]\n")
else:
output.write(f"Entry {i}:\n")
output.write("Post-ALU2 Queue:")
if Post_ALU2_Queue:
output.write(f" [{' '.join(str(x) for x in Post_ALU2_Queue)}]")
output.write("\n")
output.write("\nRegisters\n")
for i in range(0, 32, 8):
output.write(f"x{i:02}:")
for j in range(8):
if i + j < 32:
output.write(f"\t{registers[i + j]}")
output.write("\n")
output.write("\n")
output.write("Data\n")
data_keys = sorted(memory_data.keys())
for i in range(0, len(data_keys), 8):
output.write(f"{data_keys[i]}:")
for j in range(8):
if i + j < len(data_keys):
output.write(f"\t{memory_data[data_keys[i + j]]}")
output.write("\n")
sample=sys.argv[1]
sample_file=open(sample,"r")
with sample_file:
while True:
instruction = sample_file.readline().strip()
if not instruction:
break
if is_data_active:
if instruction[0] == "1":
value = twos_complement(instruction)
else:
value = int(instruction, 2)
memory_data[pc_current_address] = value
else:
last_two_digits = instruction[-2:]
if last_two_digits == "00" and disassemble_cat4(instruction) ==
"break":
is_data_active = True
if last_two_digits == "11":
decoded = disassemble_cat1(instruction)
elif last_two_digits == "01":
decoded = disassemble_cat2(instruction)
elif last_two_digits == "10":
decoded = disassemble_cat3(instruction)
elif last_two_digits == "00":
decoded = disassemble_cat4(instruction)
inst_memory[pc_current_address] = [instruction, decoded]
pc_current_address += 4
def executionPipeline():
global cycle_count
global pc_current_address
global execute_process,instructionPointer,execute_process,branch_exec_queue
pc_current_address = 256
while execute_process :
instructionWriteCommit()
instructionLoadMemory()
instructionALU()
instructionIssue()
instructionFetch()
if not execute_process:
branch_exec_queue.append("break")
if not instructionPointer:
outputStateSnapshot(cycle_count)
cycle_count += 1
else:
instructionPointer = 0
if cycle_count > 100:
break
executionPipeline()
output.close()
