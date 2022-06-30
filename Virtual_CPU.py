from typing import Callable, Optional, Union
from inspect import getfullargspec

MAX_MEM: int = 1000
MIN_MEM: int = 100
MAX_REGISTERS: int = 20
ABSTRACT_CLASS_ERROR: str = "This is an abstract class that is not meant to be instantiated."


class Operand:
    def get_value(self) -> None:
        raise NotImplementedError(ABSTRACT_CLASS_ERROR)

    def set_value(self, value) -> None:
        raise NotImplementedError(ABSTRACT_CLASS_ERROR)


class ReadOnlyOperand(Operand):
    def __init__(self, value) -> None:
        self.value: any = value

    def set_value(self, value) -> None:
        raise RuntimeError('This class is Read-Only')

    def get_value(self) -> any:
        return self.value


class Memory:
    def __init__(self, size: int) -> None:
        self.size: int = size
        self.mem: list[Union[str, int, float]] = [0] * size  # allocate memory and initialize to 0

    def set_mem(self, location: int, value: any) -> None:
        if location < 0:
            raise RuntimeError('location (' + str(location) + ') is less than 0')
        elif location > (self.size - 1):
            raise RuntimeError('location (' + str(location) + ') is greater than memory size (' + str(self.size) + ')')
        else:
            self.mem[location] = value

    def get_mem(self, location: int) -> Union[str, int, float]:
        if location < 0:
            raise RuntimeError('location (' + str(location) + ') is less than 0')
        elif location > (self.size - 1):
            raise RuntimeError('location (' + str(location) + ') is greater than memory size (' + str(self.size) + ')')
        else:
            return self.mem[location]


class MemoryOperand(Operand):
    def __init__(self, memory_object, location) -> None:
        self.location = location
        self.memory_object = memory_object

    def get_value(self):
        return self.memory_object.get_mem(self.location)

    def set_value(self, value) -> None:
        self.memory_object.set_mem(self.location, value)


class Literal(ReadOnlyOperand):
    def __init__(self, value) -> None:
        super().__init__(value)

    def set_value(self, value) -> None:
        raise RuntimeError(f'This class is Read-Only: you tried to set the value of a literal to "{value}" but it '
                           f'cannot be changed from "{self.value}"...')

    def get_value(self) -> any:
        return self.value


class Register(Operand):
    def __init__(self, value: int = 0) -> None:
        self.value: int = value

    def set_value(self, value) -> None:
        self.value = value

    def get_value(self) -> int:
        return self.value


class StackPointer(Operand):
    def __init__(self, value) -> None:
        self.value = value
        self.maxVal = value

    def pop(self) -> None:
        self.value += 1
        if self.value > self.maxVal:
            raise RuntimeError("Stack mismatch: max value is " + str(self.maxVal) + ", SP is " + str(self.value))

    def push(self) -> None:
        self.value -= 1
        if self.value < 0:
            raise RuntimeError("Stack overflow: stack pointer is " + str(self.value))

    def get_value(self) -> any:
        return self.value

    def set_value(self, value) -> None:
        self.value = value


class Flag:
    def __init__(self, value=False) -> None:
        self.value = value

    def set_true(self) -> None:
        self.value = True

    def set_false(self) -> None:
        self.value = False

    def get_value(self) -> any:
        return self.value


class Instructions:
    def __init__(self, cpu) -> None:
        self.cpu = cpu

    def inc(self, op1) -> None:
        op1.set_value(op1.get_value() + 1)

    def dec(self, op1) -> None:
        op1.set_value(op1.get_value() - 1)

    def cmp(self, op1, op2) -> None:
        val = op1.get_value() - op2.get_value()
        if 0 == val:
            self.cpu.EqualFlag.set_true()
        else:
            self.cpu.EqualFlag.set_false()
        if 0 < val:
            self.cpu.GreaterFlag.set_true()
        else:
            self.cpu.GreaterFlag.set_false()

    def out(self, op1) -> None:
        print(op1.get_value())

    def add(self, op1, op2) -> None:
        op1.set_value(op1.get_value() + op2.get_value())

    def sub(self, op1, op2) -> None:
        op1.set_value(op1.get_value() - op2.get_value())

    def jmp(self, op1) -> None:
        self.cpu.IC.set_value(op1.get_value())

    def je(self, op1) -> None:
        if self.cpu.EqualFlag.get_value():
            self.cpu.IC.set_value(op1.get_value())

    def jne(self, op1) -> None:
        if not self.cpu.EqualFlag.get_value():
            self.cpu.IC.set_value(op1.get_value())

    def jg(self, op1) -> None:
        if self.cpu.GreaterFlag.get_value() and (not self.cpu.EqualFlag.get_value()):
            self.cpu.IC.set_value(op1.get_value())

    def jl(self, op1) -> None:
        if (not self.cpu.GreaterFlag.get_value()) and (not self.cpu.EqualFlag.get_value()):
            self.cpu.IC.set_value(op1.get_value())

    def jle(self, op1) -> None:
        if (not self.cpu.GreaterFlag.get_value()) or (self.cpu.EqualFlag.get_value()):
            self.cpu.IC.set_value(op1.get_value())

    def jge(self, op1) -> None:
        if (self.cpu.GreaterFlag.get_value()) or (self.cpu.EqualFlag.get_value()):
            self.cpu.IC.set_value(op1.get_value())

    def mul(self, op1, op2) -> None:
        op1.set_value(op1.get_value() * op2.get_value())

    def div(self, op1, op2) -> None:
        op1.set_value(op1.get_value() // op2.get_value())

    def push(self, op1) -> None:
        self.cpu.SP.push()
        self.cpu.stack.set_mem(self.cpu.SP.get_value(), op1.get_value())

    def pop(self, op1) -> None:
        op1.set_value(self.cpu.stack.get_mem(self.cpu.SP.get_value()))
        self.cpu.SP.pop()

    def load(self, op1, op2) -> None:
        self.cpu.set_mem(op1.get_value(), op2.get_value())

    def call(self, op1) -> None:
        self.push(Literal(self.cpu.IC.get_value() + 1))
        self.jmp(op1)

    def ret(self) -> None:  #
        self.pop(self.cpu.IC)

    def set(self, op1, op2) -> None:
        op1.set_value(op2.get_value())

    def end(self) -> bool:
        return False

    def nop(self) -> None:
        pass


class CPU:
    def __init__(self, registers: int, memory: Memory, stack_memory: Memory, debug_print: bool = False) -> None:
        self.memory: Memory = memory
        self.stack: Memory = stack_memory
        self.registers: list[Register] = [Register() for _ in range(registers)]
        self.IC: Register = Register(0)
        self.instructions: Instructions = Instructions(self)
        self.EqualFlag: Flag = Flag()
        self.GreaterFlag: Flag = Flag()
        self.SP: StackPointer = StackPointer(stack_memory.size - 1)
        self.labels: dict[str, int] = {}
        self.debug_print: bool = debug_print

    def execute_program(self, entry_point=0) -> None:
        print('Starting Program at Entry Point ' + str(entry_point))
        self.IC.set_value(entry_point)
        ic_val: int = self.IC.get_value()
        while self.execute_instruction():
            if self.IC.get_value() == ic_val:
                self.IC.set_value(self.IC.get_value() + 1)
            ic_val: int = self.IC.get_value()
        print('Program Ended')

    def execute_instruction(self) -> bool:
        instruction_string: str = self.memory.get_mem(self.IC.get_value())
        if self.debug_print:
            print(instruction_string)
        if instruction_string is not None:
            return self.decode_instruction(instruction_string)
        else:
            return False

    def decode_instruction(self, instruction_string: str) -> bool:
        split_instruction: list[str] = instruction_string.split(' ', 1)
        instruction_name: str = split_instruction[0]
        try:
            instruction_function: Callable = getattr(self.instructions, instruction_name)
        except AttributeError:
            raise RuntimeError(f'You\'ve attempted to call a nonexistent instruction: "{instruction_name}"...weird...')
        else:
            num_operands: int = len(getfullargspec(instruction_function).args) - 1
        if num_operands == 2:
            operands: list[str] = split_instruction[1].split(', ', 1)
            op1: Operand = self.decode_operand(operands[0])
            op2: Operand = self.decode_operand(operands[1])
            result: Optional[bool] = instruction_function(op1, op2)
        elif num_operands == 1:
            op1: Operand = self.decode_operand(split_instruction[1])
            result: Optional[bool] = instruction_function(op1)
        else:
            result: Optional[bool] = instruction_function()
        if result is None:  # result is None; this is normal (all instructions besides "end" return nothing)
            return True
        elif not result:  # result is False; the program has halted
            return False
        else:  # shouldn't happen
            print(f'Weird: result from {instruction_name} was {result}. It should only either be None or False, though')
            return True

    def decode_operand(self, op: str) -> Operand:
        # Registers start with R
        # Literal Numbers start with #
        # Literal Strings start with "
        # Memory starts with M
        # Stack Pointer = SP
        # Instruction Counter = IC
        if op in self.labels:
            label_location: int = self.labels[op]
            return Literal(label_location)
        if op == 'SP':
            return self.SP
        if op == 'IC':
            return self.IC
        op_type = op[:1]
        op_value = op[1:]
        if op_type == 'R':
            register_number: int
            try:
                register_number = int(op_value)
            except ValueError:
                raise RuntimeError(f'Uh what? You want me to convert "{op_value}" to an int? That\'s not possible...')
            if register_number < 0 or register_number > (len(self.registers) - 1):
                raise RuntimeError(f'You tried to access register number "{register_number}" but that\'s invalid.')
            return self.registers[register_number]
        if op_type == '#':
            literal_value: Union[int, float]
            try:
                literal_value = int(op_value)
            except ValueError:
                try:
                    literal_value = float(op_value)
                except ValueError:
                    raise RuntimeError(f'I expected "{op_value}" to be an int or float! what am I supposed to do here?')
            return Literal(literal_value)
        if op_type == '"':
            return Literal(op_value[:-1])
        if op_type == 'M':
            return MemoryOperand(self.memory, int(op_value))
        raise RuntimeError(f'Can\'t decode operand "{op}". There is no label with that name. I have no clue what '
                           f'you\'re trying to say.')


class Computer:
    def __init__(self, registers=10, memory=256):
        self.memory: Memory = Memory(memory)
        self.stackMem: Memory = Memory(memory)
        self.processor: CPU = CPU(registers, self.memory, self.stackMem)

    def load_program(self, program: str, entry_point: int = 0):
        i: int = entry_point
        for string in program.splitlines():
            set_string: str = string
            if set_string[:1] != ';':  # line is commented out
                split_instruction: list[str] = string.split(' ', 1)
                label_name: str = split_instruction[0]
                if label_name[-1:] == ':':  # line starts with a label
                    self.processor.labels[label_name[:-1]] = i  # store the address of this label in a dict
                    set_string = split_instruction[1]
                self.memory.set_mem(i, set_string)
                i += 1

    def start(self, entry_point=0):
        self.processor.execute_program(entry_point)

    def run_program(self, program: str, entry_point: int = 0):
        self.load_program(program, entry_point)
        self.start(entry_point)


# TODO: Labelled memory? How do I reference memory addresses?


if __name__ == '__main__':
    PC: Computer = Computer()
    program_str: str = '''\
out "Let's begin...
set R0, #10
loop: out R0
dec R0
cmp R0, #0
jge loop
out "Okay, it's over!
end
;commented out nonsense
'''
    PC.run_program(program_str)
