import sys
import os.path
import stat
from xml.etree import ElementTree
from nis import match

#------------------------------------------------#
#                                                #
#   Classes                                #
#                                                #
#------------------------------------------------#

class CallStack():

    def __init__( self ):

        self.stack = []

    def is_empty( self ):

        return len( self.stack ) == 0

    def push( self, execute_index ):

        self.stack.append( execute_index )

    def get_top( self ):

        if self.is_empty():

            sys.stderr.write("Zasobnik volani je prazdny\n")
            exit(56)

        return self.stack[ len( self.stack ) - 1 ]

    def pop( self ):

        self.stack.pop()
    
class Label:

    def __init__( self, name, execute_index ):

        self.name = name
        self.execute_index = execute_index

class Labels:

    def __init__( self ):
        
        self.labels = []

    def add_label( self, name, execute_index ):

        # Create_new variable indicates wheter method should append new label or not
        create_new = True

        # Check if label already exists
        for label in self.labels:

            if label.name == name:
                
                create_new = False

                # Check if labels with same name have same execute index
                if label.execute_index != execute_index:
                    
                    sys.stderr.write("Semanticka chyba\n")
                    exit(52)

        # Create new label
        if create_new:

            label = Label( name, execute_index )

            # Append label to list
            self.labels.append( label )

    def get_execute_index( self, label_argument ):

        if label_argument.type != "label":

            sys.stderr.write("Semanticka chyba\n")
            exit(52)

        for label in self.labels:

            if label.name == label_argument.value:

                return label.execute_index

        sys.stderr.write("Skok na neexistujuce navesti\n")
        exit(52)

class DataStack:

    def __init__( self ):

        self.stack = []

    def is_empty( self ):

        return len( self.stack ) == 0

    def push( self, instruction_argument ):

        self.stack.append( instruction_argument )

    def pop( self ):

        if self.is_empty():

            sys.stderr.write("Chýbajúca hodnota na datovom zásobníku\n")
            exit(56)

        self.stack.pop()

    def get_top( self ):

        return self.stack[ len(self.stack) - 1 ]

class InstructionArgument:

    def __init__( self, type, value ):
        self.type = type
        self.value = value

    def is_variable( self ):

        return self.type == "var"

    def is_constant( self ):

        return self.type in ["int","bool","string","nil"]

    def get_variable_frame( self ):

        if not self.is_variable():

            return None

        return self.value[0: self.value.find("@")]

    def get_variable_name( self ):

        if not self.is_variable():

            return None
            
        return self.value[self.value.find("@") + 1:]

class Instruction:

    def __init__( self, opcode, order ):
        self.opcode = opcode
        self.order = order
        self.arguments = []

    def add_argument( self, instruction_argument ):

        self.arguments.append( instruction_argument )

# Class represents variable
class Variable:

    # Variable has it's name, type and value
    def __init__( self, name, type, value ):

        self.name = name
        self.type = type
        self.value = value

    # Method for setting variable attributes
    def set( self, name, type, value ):

        self.name = name
        self.type = type
        self.value = value

    def has_value( self ):

        return self.value is not None

# Class represents list of variables
class Frame:

    # Frame has list of variables
    def __init__( self ):

        self.variables = []

    # Method for adding variable to the frame
    # When variable with the same name already exists in frame,
    # method throws error
    def add_variable( self, variable_name ):

        # Check if variable with same name already exists in the frame
        if self.contains_variable( variable_name ):

            # Redefinition of variable
            sys.stderr.write("Redefinícia premennej")
            exit(52)

        # Add new variable into frame
        self.variables.append( Variable( variable_name, None, None ) )

    # Method for finding variable inside frame by variable's name
    # Method returns True if variable is found, otherwise it returns False
    def contains_variable( self, variable_name ):

        # Loop trough all variables
        for variable in self.variables:

            # If variable names match, return True
            if variable.name == variable_name:
                
                return True
        
        # Return False when variablew was not found
        return False

    # Method for getting variable inside frame by variable's name
    # Method return variable object on success, None on failure
    def get_variable( self, variable_name ):
        
        # Loop trough all variables
        for variable in self.variables:

            # If variables name match, return variable
            if variable.name == variable_name:

                return variable
        
        # Return None on failure
        return None

    # Destructor of frame
    def __del__( self ):

        # Delete all variables inside frame
        for variable in self.variables:

            del variable

# Class for the stack of frames
class FrameStack:

    # Frame stack is implemented as list
    def __init__( self ):
        
        self.stack = []

    # Method for pushing frame into stack
    def push( self, frame ):

        self.stack.append( frame )

    # Method for poping out frame from stack
    def pop( self ):

        self.stack.pop()

    # Method returns boolean that says wheter
    # stack is empty or not
    def is_empty( self ):

        return len( self.stack ) == 0

    # Method for getting local frame,
    # that should be frame on top of the stack
    # If stack is empty, method returns None
    def get_local_frame( self ):
        
        # If stack is empty, return None
        if self.is_empty():
            
            return None

        # If stack is not empty, return top frame from stack
        return self.stack[ len( self.stack ) - 1 ]

# Class represents program counter with all the instructions
# and current executt index - position of instruction
# to be execute
class ProgramCounter:

    # Program counter contains list of instructions
    # and current execute index starting with value 1
    def __init__(self):

        self.instructions = []
        self.execute_index = 1

    # Method for adding instruction into program counter
    def add_instruction( self, instruction ):

        self.instructions.append( instruction )

    # Method for changing current execute index
    def move_to_instruction( self, execute_index ):

        self.execute_index = execute_index

    # Method returns True, if program counter contains
    # instruction with given order
    # Otherwise it returns False
    def contains_order( self, order ):

        for instruction in self.instructions:

            if instruction.order == order:

                return True

        return False

# Class program contains all info needed
# to interpret a program
class Program:

    # Program contains program counter, global frame, temporary frame
    # and stack of frames
    def __init__( self, input_lines ):

        self.program_counter = ProgramCounter()
        self.global_frame = Frame()
        self.temporary_frame = None
        self.frame_stack = FrameStack()
        self.data_stack = DataStack()
        self.labels = Labels()
        self.input_lines = input_lines
        self.call_stack = CallStack()

    def find_variable_by_argument( self, argument ):

        # Get the variable frame and name
        variable_frame = argument.get_variable_frame()
        variable_name = argument.get_variable_name()

        # Decide where the variable should be located
        if variable_frame == "GF":

            variable = self.global_frame.get_variable( variable_name )

        elif variable_frame == "LF":

            # Check if local frame exists
            if self.frame_stack.is_empty():

                sys.stderr.write("Lokálny rámec nie je definovaný\n")
                exit(55)

            variable = self.frame_stack.get_local_frame().get_variable( variable_name )

        elif variable_frame == "TF":

            # Check if temporary frame exists
            if self.temporary_frame is None:

                sys.stderr.write("Dočasný rámec nie je definovaný\n")
                exit(55)

            variable = self.temporary_frame.get_variable( variable_name )
        
        # Check if variable exists
        if variable is None:

            sys.stderr.write("Premenná neexistuje\n")
            exit(54)
        
        # Return found variable
        return variable

    def get_variable_by_argument( self, argument ):

        # Find the variable
        variable = self.find_variable_by_argument( argument )

        # Check if variable has value
        if variable.value is None:

            sys.stderr.write("Chybajúca hodnota v premennej\n")
            exit(56)

        return variable

# Class interpret is used to execute instructions
class Interpret:

    # Help method for getting operand type and value
    def get_operand_type_and_value( self, program, operand_argument ):

        # Check if operand is variable
        if operand_argument.is_variable():

            # Get the variable
            operand_variable = program.get_variable_by_argument( operand_argument )

            # Return operand type and value
            return operand_variable.type, operand_variable.value

        else:

            # Return operand type and value
            return operand_argument.type, operand_argument.value

    # Help method for getting operand types and values
    def get_operand_types_and_values( self, program, operand_arguments ):

        # Define lists for operands' types and values
        operand_types = []
        operand_values = []

        # For every operand argument
        for operand_argument in operand_arguments:

            # Get the operand's type and value
            operand_type, operand_value = self.get_operand_type_and_value( program, operand_argument )

             # Save the operand's type and value
            operand_types.append( operand_type )
            operand_values.append( operand_value )

        # Return operands's types and values
        return operand_types, operand_values

    # MOVE
    def execute_move_instruction( self, program, instruction ):

        # Get the destination argument
        dest_argument = instruction.arguments[0]

        # Destination argument must be variable type
        if not dest_argument.is_variable():

            sys.stderr.write("Zlý typ operandov\n")
            exit(53)

        # Find variable by destination argument
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get the source argument
        source_argument = instruction.arguments[1]

        # If source is a variable
        if source_argument.type == "var":

            # Get source variable by argument's value
            source_variable = program.find_variable_by_argument( source_argument )

            # Get source's type and value from variable
            source_type = source_variable.type
            source_value = source_variable.value

            # Verify source variable has value
            if not source_variable.has_value():

                sys.stderr.write("V premennej chyba hodnota")
                exit(56)
                
        else:

            # Get source type and value from argument
            source_type = source_argument.type
            source_value = source_argument.value

        # Set source attributes to destination variable
        dest_variable.set( dest_variable.name, source_type, source_value )

        # If destination variable is now string, translate it into readable form
        if dest_variable.type == "string":

            dest_variable.value = translate_string_value( dest_variable.value )

    # CREATEFRAME
    def execute_createframe_instruction( self, program ):
    
        # If there is already a temporary frame
        if program.temporary_frame is not None:

            del program.temporary_frame
                
        # Create new temporary frame
        program.temporary_frame = Frame()

    # PUSHFRAME
    def execute_pushframe_instruction( self, program ):

        # If temporary frame doesn't exist
        if program.temporary_frame is None:

            sys.stderr.write("Dočasný rámec nie je definovaný\n")
            exit(55)

        else:

            # Push temporary frame into frame stack
            program.frame_stack.push( program.temporary_frame )

            # Delete temporary frame and undefine it
            del program.temporary_frame
            program.temporary_frame = None

    # POPFRAME
    def execute_popframe_instruction( self, program ):

        # Check if current local frame exists
        if program.frame_stack.is_empty():

            sys.stderr.write("Lokálny rámec nie je definovaný\n")
            exit(55)

        else:

            # Delete temporary frame if it exists
            if program.temporary_frame is not None:

                del program.temporary_frame
            
            # Save the current local frame into temporary frame
            program.temporary_frame = program.frame_stack.get_local_frame()
            
            # Pop the current local frame from the frame stack
            program.frame_stack.pop()

    # DEFVAR
    def execute_defvar_instruction( self, program, instruction ):

        # Get the argument
        argument = instruction.arguments[0]

        if not argument.is_variable():

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Get the variable parameters
        variable_frame = argument.get_variable_frame()
        variable_name = argument.get_variable_name()

        if variable_frame == "GF":

            # Add variable into the global frame
            program.global_frame.add_variable( variable_name )

        elif variable_frame == "LF":
            
            # Get the local frame
            local_frame = program.frame_stack.get_local_frame()

            # Check if there is any local frame
            if program.frame_stack.get_local_frame() is None:

                # Local frame doesn't exist
                sys.stderr.write("Lokálny rámec nie je definovaný\n")
                exit(55)

            # Add variable into the current local frame
            local_frame.add_variable( variable_name )

        elif variable_frame == "TF":

            # Check if there is any temporary frame
            if program.temporary_frame is None:

                # Temporary frame doesn't exist
                sys.stderr.write("Dočasný rámec nie je definovaný\n")
                exit(55)

            # Add variable into the temporary frame
            program.temporary_frame.add_variable( variable_name )

    # CALL
    def execute_call_instruction( self, program, instruction ):

        # Get label argument
        label_argument = instruction.arguments[0]

        # Get the execute index from label
        execute_index = program.labels.get_execute_index( label_argument )

        # Save current execute index to call stack
        program.call_stack.push( program.program_counter.execute_index )

        # Do the jump
        program.program_counter.move_to_instruction( execute_index )

    # RETURN
    def execute_return_instruction( self, program ):

        # Get return execute index
        execute_index = program.call_stack.get_top()

        program.program_counter.move_to_instruction( execute_index )

        # Pop from the call stack
        program.call_stack.pop()

    # PUSHS
    def execute_pushs_instruction( self, program, instruction ):

        # Get the argument
        argument = instruction.arguments[0]

        # If argument is variable
        if argument.is_variable():

            # Get the variable
            variable = program.find_variable_by_argument( argument )

            new_argument_type = variable.type
            new_argument_value = variable.value

        else:

            new_argument_type = argument.type
            new_argument_value = argument.value

        # Create new instruction argument for data stack purposes
        new_argument = InstructionArgument( new_argument_type, new_argument_value )

        # Push new argument to the data stack
        program.data_stack.push( new_argument )

    # POPS
    def execute_pops_instruction( self, program, instruction ):

        # If data stack is empty, throw error
        if program.data_stack.is_empty():

            sys.stderr.write("Chýbajúca hodnota na datovom zásobníku\n")
            exit(56)

        # Get the destination argument
        dest_argument = instruction.arguments[0]

        # Create a temporary instruction that will be
        # passed to execute_move_instruction() method
        tmp_instruction = Instruction( None, None )

        # Fill the temporary instruction
        tmp_instruction.add_argument( dest_argument )
        tmp_instruction.add_argument( program.data_stack.get_top() )

        # Call the execute_move_instruction() method
        self.execute_move_instruction( program, tmp_instruction )

        # Delete temporary instruction and it's arguments
        del tmp_instruction.arguments[1]
        del tmp_instruction.arguments[0]
        del tmp_instruction

        # Pop from data stack
        program.data_stack.pop()

    # Help method for aritmetic instructions
    def get_aritmetic_operands_values( self, program, operand_arguments ):

        # Define array for operands' values
        operand_values = []

        # For every operand argument
        for operand_argument in operand_arguments:

            # If operand is variable
            if operand_argument.is_variable():
            
                # Get the operand's variable
                operand_variable = program.get_variable_by_argument( operand_argument )
                
                # Operand must by type of int
                if operand_variable.type != "int":

                    sys.stderr.write("Zly typ operandu\n")
                    exit(53)

                # Get value of the operand's variable
                operand_values.append( operand_variable.value )
            
            else:

                # First operand must by type of int
                if operand_argument.type != "int":

                    sys.stderr.write("Zly typ operandu\n")
                    exit(53)
                
                # Get value of the first operand's argument
                operand_values.append( operand_argument.value )

        return operand_values

    # ADD
    def execute_add_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]
        
        # Get operands' values
        operand_values = self.get_aritmetic_operands_values( program, operand_arguments )

        # Calculate result from operand values
        result = int( operand_values[0] ) + int( operand_values[1] )

        # Save result to destination variable
        dest_variable.set( dest_variable.name, "int", result)

    # SUB
    def execute_sub_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]
        
        # Get operands' values
        operand_values = self.get_aritmetic_operands_values( program, operand_arguments )

        # Calculate result from operand values
        result = int( operand_values[0] ) - int( operand_values[1] )

        # Save result to destination variable
        dest_variable.set( dest_variable.name, "int", result)

    # MUL
    def execute_mul_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]
        
        # Get operands' values
        operand_values = self.get_aritmetic_operands_values( program, operand_arguments )

        # Calculate result from operand values
        result = int( operand_values[0] ) * int( operand_values[1] )

        # Save result to destination variable
        dest_variable.set( dest_variable.name, "int", result)

    # IDIV
    def execute_idiv_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]
        
        # Get operands' values
        operand_values = self.get_aritmetic_operands_values( program, operand_arguments )

        # Check if second operand's value is zero
        # Division by zero
        if int( operand_values[1] ) == 0:

            sys.stderr.write("Delenie nulou\n")
            exit(57)

        # Calculate result from operand values
        result = int( operand_values[0] ) // int( operand_values[1] )

        # Save result to destination variable
        dest_variable.set( dest_variable.name, "int", result)

    # Help method for comparison instructions
    def get_comparison_operands_values_and_types( self, program, operand_arguments, eq ):

        # Define list for operand values
        operand_values = []

        # Define list for operand types
        operand_types = []

        # For every operand argument
        for operand_argument in operand_arguments:

            # If operand is variable
            if operand_argument.is_variable():

                # Get the variable
                operand_variable = program.get_variable_by_argument( operand_argument )

                # Save operand's value and type
                operand_values.append( operand_variable.value )
                operand_types.append( operand_variable.type )

            else:

                # Save operand's value and type
                operand_values.append( operand_argument.value )
                operand_types.append( operand_argument.type )
        
        if eq:

            # If one or two operands have type nil
            if "nil" not in operand_types:

                # Check if operands' types match
                if operand_types[0] != operand_types[1]:

                    # Operand has bad type
                    sys.stderr.write("Zly typ operandu\n")
                    exit(53)

            # Return operands' values and their types
            return operand_values, operand_types

        else:

            # Check if operands' types match
            if operand_types[0] != operand_types[1]:

                # Operand has bad type
                sys.stderr.write("Zly typ operandu\n")
                exit(53)

            # Return operands' values and their types
            return operand_values, operand_types

    # LT
    def execute_lt_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]

        # Get operands' values
        operand_values, operand_types = self.get_comparison_operands_values_and_types( program, operand_arguments, False )

        # Operand cannot be nil
        if "nil" in operand_types:

            sys.stderr.write("Zly typ operandu\n")
            exit(53)
        
        # Get the result of camparison
        result = operand_values[0] < operand_values[1]

        # Save result of comparison to destination variable
        if result:

            dest_variable.set( dest_variable.name, "bool", "true" )

        else:

            dest_variable.set( dest_variable.name, "bool", "false" )

    # GT
    def execute_gt_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]

        # Get operands' values
        operand_values, operand_types = self.get_comparison_operands_values_and_types( program, operand_arguments, False )

        # Operand cannot be nil
        if "nil" in operand_types:

            sys.stderr.write("Zly typ operandu\n")
            exit(53)
        
        # Get the result of camparison
        result = operand_values[0] > operand_values[1]

        # Save result of comparison to destination variable
        if result:

            dest_variable.set( dest_variable.name, "bool", "true" )

        else:

            dest_variable.set( dest_variable.name, "bool", "false" )

    # EQ
    def execute_eq_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]

        # Get operands' values
        operand_values, operand_types = self.get_comparison_operands_values_and_types( program, operand_arguments, True )

        # If one or two of the operands are nil
        if "nil" in operand_types:

            # If there is any other operand type
            if "int" in operand_types or "string" in operand_types or "bool" in operand_types:

                result = False
            
            else:

                # If there are only two nil type operands
                result = True

        else:

            # If there is no nil in operands
            # Check if operands are same type
            if operand_types[0] == operand_types[1]:

                # Get the result of camparison
                result = operand_values[0] == operand_values[1]

            else:

                # Operands have bad type
                sys.stderr.write("Zly typ operandu\n")
                exit(53)

        # Save result of comparison to destination variable
        if result:

            dest_variable.set( dest_variable.name, "bool", "true" )

        else:

            dest_variable.set( dest_variable.name, "bool", "false" )

    # Help method for logical instructions
    def get_logical_operands_values( self, program, operand_arguments ):

        # Define list for operand values
        operand_values = []

        # For every operand argument
        for operand_argument in operand_arguments:

            # Check if operand is variable
            if operand_argument.is_variable():

                # Get the variable
                operand_variable = program.get_variable_by_argument( operand_argument )

                # Operand type must be bool
                if operand_variable.type != "bool":

                    # Operand has bad type
                    sys.stderr.write("Zly typ operandu\n")
                    exit(53)

                operand_values.append( operand_variable.value )
            
            else:

                # Operand type must be bool
                if operand_argument.type != "bool":

                    # Operand has bad type
                    sys.stderr.write("Zly typ operandu\n")
                    exit(53)

                operand_values.append( operand_argument.value )

        return operand_values

    # AND
    def execute_and_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]

        # Get operands' values
        operand_values = self.get_logical_operands_values( program, operand_arguments )

        # Transfer every operand value into python boolean
        for operand_value in operand_values:

            if operand_value == "true":

                operand_value = True
            
            else:

                operand_value = False

        # Save result into destination variable
        dest_variable.set( dest_variable.name, "bool", operand_values[0] and operand_values[1] )

    # OR
    def execute_or_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments = [instruction.arguments[1], instruction.arguments[2]]

        # Get operands' values
        operand_values = self.get_logical_operands_values( program, operand_arguments )

        # Transfer every operand value into python boolean
        for operand_value in operand_values:

            if operand_value == "true":

                operand_value = True
            
            else:

                operand_value = False

        # Save result into destination variable
        dest_variable.set( dest_variable.name, "bool", operand_values[0] or operand_values[1] )

    # NOT
    def execute_not_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operand's argument
        operand_argument = instruction.arguments[1]

        # If operand is variable
        if operand_argument.is_variable():

            # Get the variable
            operand_variable = program.get_variable_by_argument( operand_argument )

            # Save the operand's type and value
            operand_type = operand_variable.type
            operand_value = operand_variable.value

        else:

            # Save the operand's type and value
            operand_type = operand_argument.type
            operand_value = operand_argument.value

        # Operand's type must be bool
        if operand_type != "bool":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        
        # Save the result into destination variable
        if operand_value == "true":

            dest_variable.set( dest_variable.name, "bool", "false" )

        else:

            dest_variable.set( dest_variable.name, "bool", "true" )

    # INT2CHAR
    def execute_int2char_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operand's argument
        operand_argument = instruction.arguments[1]

        # Check if operand is variable
        if operand_argument.is_variable():

            # Get the variable
            operand_variable = program.get_variable_by_argument( operand_argument )

            # Save the operand's type and value
            operand_type = operand_variable.type
            operand_value = operand_variable.value

        else:

            # Save the operand's type and value
            operand_type = operand_argument.type
            operand_value = operand_argument.value

        # Operand must be int type
        if operand_type != "int":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Try transform int into char
        try:

            result = chr( int( operand_value ) )

        except:

            # Operand's value isn't correct Unicode number of char
            sys.stderr.write("Chybná práca s retazcom\n")
            exit(58)

        # Save result into destination variable
        dest_variable.set( dest_variable.name, "string", result )

    # STRI2INT
    def execute_stri2int_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments =  [ instruction.arguments[1], instruction.arguments[2] ]

        # FIXME
        # Define lists for operands' values and types
        operand_values = []
        operand_types = []
        
        # For every operand argument
        for operand_argument in operand_arguments:

            # If operand is variable
            if operand_argument.is_variable():

                # Get the operand variable
                operand_variable = program.get_variable_by_argument( operand_argument )

                operand_values.append( operand_variable.value )
                operand_types.append( operand_variable.type )

            else:

                operand_values.append( operand_argument.value )
                operand_types.append( operand_argument.type )

        # First argument must be type of string
        # Second arugment must be type of int
        if operand_types[0] != "string" or operand_types[1] != "int":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Check if given index is out of string range
        if int( operand_values[1] ) >= len( operand_values[1] ):

            # Index of character is out of string range
            sys.stderr.write("Chybná práca s retazcom\n")
            exit(58)

        # Get a result
        result = ord( operand_values[0][int(operand_values[1])] )

        # Save the result into destination variable
        dest_variable.set( dest_variable.name, "int", result)

    # READ
    def execute_read_instruction( self, program, instruction ):
        
        # This variable indicates wheter input exists and is correct or not
        correct_input = True

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get type of destination variable
        dest_type_argument = instruction.arguments[1]
        dest_type = dest_type_argument.value

        # Check if there is any input
        if len( program.input_lines ) == 0:

            correct_input = False

        else:

            # Get input
            input = program.input_lines[0]

            # Check if input is correct only when it is other type than bool
            if not check_operand_type( dest_type, input ) and dest_type != "bool":

                correct_input = False
        
        # If input is string, transform it into readable form
        if dest_type == "string":

            input = translate_string_value( input )

        # If input is bool
        if dest_type == "bool":

            # True value comes only with string "true"
            if input != "true":

                input = "false"

        # Save input or nil to destination variable
        if correct_input:

            dest_variable.set( dest_variable.name, dest_type, input )

        else:

            dest_variable.set( dest_variable.name, "nil", "nil" )


    # WRITE
    def execute_write_instruction( self, program, instruction ):

        # Get the argument
        argument = instruction.arguments[0]

        # Get the arugment's type and value
        argument_type, argument_value = self.get_operand_type_and_value( program, argument )

        # If argument is string, translate it into readable form
        if argument_type == "string":

            argument_value = translate_string_value( argument_value )

        # If it's nil, print empty string
        if argument_type == "nil":
            
            sys.stdout.write("")

        else:

            # Otherwise print argument's value
            sys.stdout.write( str( argument_value ) )

    # CONCAT
    def execute_concat_instruction( self, program, instruction ):
        
        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments =  [ instruction.arguments[1], instruction.arguments[2] ]

        # Get the operand's types and values
        operand_types, operand_values = self.get_operand_types_and_values( program, operand_arguments )

        # Check the operands' types        
        if operand_types[0] != "string" or operand_types[1] != "string":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Get the result
        result = operand_values[0] + operand_values[1]

        # Save the result to destination variable
        dest_variable.set( dest_variable.name, "string", result )

    # STRLEN
    def execute_strlen_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operand arugment
        operand_argument = instruction.arguments[1]

        # Get operand's type and value
        operand_type, operand_value = self.get_operand_type_and_value( program, operand_argument )

        # Check the operand's type
        if operand_type != "string":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Get the result
        result = len( operand_value )

        # Save the result to destination variable
        dest_variable.set( dest_variable.name, "int", result )

    # GETCHAR
    def execute_getchar_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.find_variable_by_argument( dest_argument )

        # Get operands' arguments
        operand_arguments =  [ instruction.arguments[1], instruction.arguments[2] ]

        # Get the operands' types and values
        operand_types, operand_values = self.get_operand_types_and_values( program, operand_arguments )

        # First operand must be string type
        # Second operand must be int type
        if operand_types[0] != "string" or operand_types[1] != "int":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Rename the needed values
        string = operand_values[0]
        index = int( operand_values[1] )

        # Check if given index is inside string
        if index < 0 or index >= len( string ):

            # Index is out of string range
            sys.stderr.write("Chybna praca s retazcom\n")
            exit(58)

        # Get the result
        result = operand_values[0][ index ]

        # Save the result to destination variable
        dest_variable.set( dest_variable.name, "string", result )
    
    # SETCHAR
    def execute_setchar_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.get_variable_by_argument( dest_argument )
        
        # Destination variable must be string type
        if dest_variable.type != "string":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Get operands' arguments
        operand_arguments =  [ instruction.arguments[1], instruction.arguments[2] ]

        # Get the operands' types and values
        operand_types, operand_values = self.get_operand_types_and_values( program, operand_arguments )

        # First operand must be int type
        # Second operand must be string type
        if operand_types[0] != "int" or operand_types[1] != "string":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)
        
        # Second operand cannot be empty string ( string has been initialized )
        if len( operand_values[1] ) == 0:

            sys.stderr.write("Chybajuca hodnota v premennej\n")
            exit(56)

        # Rename the needed values
        index = int( operand_values[0] )
        char = operand_values[1][0]
        string = dest_variable.value

        # Check if given index is inside string
        if index < 0 or index >= len( string ):

            # Index is out of string range
            sys.stderr.write("Chybna praca s retazcom\n")
            exit(58)

        # Work with string as list
        string_list = list( string )

        # Change character in string list
        string_list[ index ] = char

        # Transform list back to string as result of the operation
        result = "".join( string_list )

        # Save the result to destination variable
        dest_variable.set( dest_variable.name, "string", result )

    # TYPE
    def execute_type_instruction( self, program, instruction ):

        # Get destination argument
        dest_argument = instruction.arguments[0]

        # Get destination variable
        dest_variable = program.get_variable_by_argument( dest_argument )

        # Get the operand_argument
        operand_argument = instruction.arguments[1]

        # Get the operand's type and value
        operand_type, operand_value = self.get_operand_type_and_value( program, operand_argument )

        # Get the result
        if operand_type == "nil":

            result = ""
        
        else:

            result = operand_type

        # Save the result to destination variable
        dest_variable.set( dest_variable.name, "string", result )

    # LABEL

    # JUMP
    def execute_jump_instruction( self, program, instruction ):

        # Get operand argument
        label_argument = instruction.arguments[0]

        # Get the execute index from label
        execute_index = program.labels.get_execute_index( label_argument )

        # Do the jump
        program.program_counter.move_to_instruction( execute_index )

    # JUMPIFEQ
    def execute_jumpifeq_instruction( self, program, instruction ):

        # Get label argument
        label_argument = instruction.arguments[0]

        # Get the execute index from label
        execute_index = program.labels.get_execute_index( label_argument )

        # Get operands' arguments
        operand_arguments =  [ instruction.arguments[1], instruction.arguments[2] ]

        # Get the operands' types and values
        operand_types, operand_values = self.get_operand_types_and_values( program, operand_arguments )

        # Get the result
        if "nil" in operand_types:

            if operand_types[0] == operand_types[1]:

                result = True

            else:

                result = False

        else:

            if operand_types[0] == operand_types[1]:

                if operand_values[0] == operand_values[1]:

                    result = True
                
                else: 

                    result = False
            
            else:

                result = False


        # Execute jump if result is True
        if result:

            program.program_counter.move_to_instruction( execute_index )


    # JUMPIFNEQ
    def execute_jumpifneq_instruction( self, program, instruction ):

        # Get label argument
        label_argument = instruction.arguments[0]

        # Get the execute index from label
        execute_index = program.labels.get_execute_index( label_argument )

        # Get operands' arguments
        operand_arguments =  [ instruction.arguments[1], instruction.arguments[2] ]

        # Get the operands' types and values
        operand_types, operand_values = self.get_operand_types_and_values( program, operand_arguments )

        # Get the result
        if "nil" in operand_types:

            if operand_types[0] == operand_types[1]:

                result = False

            else:

                result = True

        else:

            if operand_types[0] == operand_types[1]:

                if operand_values[0] == operand_values[1]:

                    result = False
                
                else: 

                    result = True
            
            else:

                result = True


        # Execute jump if result is True
        if result:

            program.program_counter.move_to_instruction( execute_index )

    # EXIT
    def execute_exit_instruction( self, program, instruction ):

        # Get operand argument
        operand_argument = instruction.arguments[0]

        # Get operand's type and value
        operand_type, operand_value = self.get_operand_type_and_value( program, operand_argument )

        # Operand must be int type
        if operand_type != "int":

            # Operand has bad type
            sys.stderr.write("Zly typ operandu\n")
            exit(53)

        # Transform operand value to int
        operand_value = int( operand_value )

        # Operant's value should be betweeen 0 and 49 inclusive
        if operand_value < 0 or operand_value > 49:

            # Operand has bad value
            sys.stderr.write("Zla hodnota operandu\n")
            exit(57)

        exit( operand_value )

    # DPRINT
    def execute_dprint_instruction( self, program, instruction ):
        
        # Get operand argument
        operand_argument = instruction.arguments[0]

        # Get operand's type and value
        operand_type, operand_value = self.get_operand_type_and_value( program, operand_argument )

        sys.stderr.write( str( operand_value ) )

    # BREAK
    def execute_break_instruction( self, program ):

        sys.stderr.write("---------------\n")
        sys.stderr.write("STAV INTERPRETU\n")
        sys.stderr.write("Pozicia v kode: " + str( program.program_counter.execute_index) + "\n")
        sys.stderr.write("---------------\n")    

    def run( self, program ):

        # Go instruction by instruction
        while program.program_counter.execute_index <= len( program.program_counter.instructions ):

            # Map the representative instruction order on the real
            # array order that starts from 0 
            i = program.program_counter.execute_index - 1

            # Get the current instruction being processed
            instruction = program.program_counter.instructions[i]

            if instruction.opcode == "MOVE":

                self.execute_move_instruction( program, instruction )

            elif instruction.opcode == "CREATEFRAME":

                self.execute_createframe_instruction( program )
                
            elif instruction.opcode == "PUSHFRAME":

                self.execute_pushframe_instruction( program )

            elif instruction.opcode == "POPFRAME":

                self.execute_popframe_instruction( program )

            elif instruction.opcode == "DEFVAR":
                
                self.execute_defvar_instruction( program, instruction )

            elif instruction.opcode == "CALL":

                self.execute_call_instruction( program, instruction )

            elif instruction.opcode == "RETURN":

                self.execute_return_instruction( program )

            elif instruction.opcode == "PUSHS":

                self.execute_pushs_instruction( program, instruction )

            elif instruction.opcode == "POPS":

                self.execute_pops_instruction( program, instruction )

            elif instruction.opcode == "ADD":

                self.execute_add_instruction( program, instruction )

            elif instruction.opcode == "SUB":

                self.execute_sub_instruction( program, instruction )

            elif instruction.opcode == "MUL":

                self.execute_mul_instruction( program, instruction )

            elif instruction.opcode == "IDIV":

                self.execute_idiv_instruction( program, instruction )

            elif instruction.opcode == "LT":

                self.execute_lt_instruction( program, instruction )

            elif instruction.opcode == "GT":

                self.execute_gt_instruction( program, instruction )

            elif instruction.opcode == "EQ":

                self.execute_eq_instruction( program, instruction )

            elif instruction.opcode == "AND":

                self.execute_and_instruction( program, instruction )

            elif instruction.opcode == "OR":

                self.execute_or_instruction( program, instruction )

            elif instruction.opcode == "NOT":

                self.execute_not_instruction( program, instruction )

            elif instruction.opcode == "INT2CHAR":

                self.execute_int2char_instruction( program, instruction )

            elif instruction.opcode == "STRI2INT":

                self.execute_stri2int_instruction( program, instruction )

            elif instruction.opcode == "READ":

                self.execute_read_instruction( program, instruction )

            elif instruction.opcode == "WRITE":

                self.execute_write_instruction( program, instruction )


            elif instruction.opcode == "CONCAT":

                self.execute_concat_instruction( program, instruction )

            elif instruction.opcode == "STRLEN":

                self.execute_strlen_instruction( program, instruction )

            elif instruction.opcode == "GETCHAR":

                self.execute_getchar_instruction( program, instruction )

            elif instruction.opcode == "SETCHAR":

                self.execute_setchar_instruction( program, instruction )

            elif instruction.opcode == "TYPE":

                self.execute_type_instruction( program, instruction )

            elif instruction.opcode == "LABEL":

                pass

            elif instruction.opcode == "JUMP":

                self.execute_jump_instruction( program, instruction )

            elif instruction.opcode == "JUMPIFEQ":

                self.execute_jumpifeq_instruction( program, instruction )

            elif instruction.opcode == "JUMPIFNEQ":

                self.execute_jumpifneq_instruction( program, instruction )

            elif instruction.opcode == "EXIT":

                self.execute_exit_instruction( program, instruction )

            elif instruction.opcode == "DPRINT":

                self.execute_dprint_instruction( program, instruction )

            elif instruction.opcode == "BREAK":

                self.execute_break_instruction( program )

            else:

                print()

            # Move to the next instruction
            program.program_counter.move_to_instruction( program.program_counter.execute_index + 1 )



#------------------------------------------------#
#                                                #
#   Own functions                                #
#                                                #
#------------------------------------------------#

# Function for printing help
def print_help():

    print("NAPOVEDA")

# Function for processing arguments
# Function exits the program if either there are no arguments,
# bad combination of arguments or too many arguments.
# The function returns source file's path and input file's path,
# if there is any, otherwise it returns only one of them,
# the second one is returned as empty string.
def handle_arguments( arguments ):

    # If there are no arguments
    if len( arguments ) == 0:

        # Missing arguments
        sys.stderr.write("Ziadny argument nebol zadany.\n")
        exit(10)
        
    # Define variables that will be returned
    source_file, input_file = "", ""

    # For each argument
    for i in range( len( arguments ) ):

         # Catch the "help" argument
        if arguments[i] == "--help":

            # Accept the "help" argument only if it is the only argument given
            if i != 0 or len( arguments ) != 1:

                # More "--help" arguments than allowed (1)
                sys.stderr.write("Nevhodna kombinacia argumentov.\n")
                exit(10)
            
            print_help()
            
        # Catch the "source" argument
        elif arguments[i][0:9] == "--source=":

            # Accept only the first "source" argument
            if source_file != "":
                
                # More source arguments than allowed (1)
                sys.stderr.write("Nevhodna kombinacia argumentov.\n")
                exit(10)

            source_file = arguments[i][9:]

        # Catch the "input" argument
        elif arguments[i][0:8] == "--input=":

            # Accept only the first "input" argument
            if input_file != "":

                # More input arguments than allowed (1)
                sys.stderr.write("Nevhodna kombinacia argumentov.\n")
                exit(10)

            input_file = arguments[i][8:]

        else:

            sys.stderr.write("Neznamy argument.\n")
            exit(10)

    # Return source and input file after arguments check
    return source_file, input_file

# Function for checking whether the file is readable
def file_is_readable( file ):

    st = os.stat( file )
    return bool( st.st_mode & stat.S_IRGRP )

# Function exits with error code if a given file
# is either unreadable or doesn't exist
def file_check( file ):

    # File must exist
    if not os.path.exists( file ):

        sys.stderr.write("Subor neexistuje.\n")
        exit(11)
    
    # File must be readable
    if not file_is_readable( file ):

        sys.stderr.write("Nedostatocne opravnenia pre citanie suboru.\n")
        exit(11)

# Function opens given files for reading
def open_files( source_file, input_file ):

    # If "source" argument was given by user,
    # check wheter the file can be opened and open it
    if source_file != "":

        file_check( source_file )
        source = open( source_file, "r" )

    else:

        source = sys.stdin
    
    # If "input" argument was given by user,
    # check wheter the file can be opened and open it
    if input_file != "":
        
        file_check( input_file )
        input = open(input_file, "r")
        input = input.read()

    else:

        input = sys.stdin.read()

    return source, input

# This function checks the correct properties of the program tag
def check_program_tag( program ):

    # Program tag has the right name
    if program.tag != "program":

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)

    # Program tag has "language" attribute
    if "language" not in program.attrib:

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)

    # "language" attribute has the right value
    if program.attrib["language"] != "IPPcode22":

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)

# This function checks the correct properties of the instruction tag
def check_instruction_tag( instruction ):

    # Instruction tag has the right name
    if instruction.tag != "instruction":

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)

    # Instruction tag has "order" and "opcode" attribute
    if "order" not in instruction.attrib or "opcode" not in instruction.attrib:

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)

# This function checks if program counter already contains instruction with given order
def check_instruction_order( program, instruction_tag ):

    try:
        
        int( instruction_tag.attrib["order"] )
    
    except:

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)

    if program.program_counter.contains_order( int( instruction_tag.attrib["order"] ) ):

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)

    if int( instruction_tag.attrib["order"] ) < 0:

        sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
        exit(32)        



def handle_empty_string_in_argument_tag( argument_tag ):

    if argument_tag.text is None:

        argument_tag.text = ""

def translate_string_value( string ):

    string = string.replace("\\010","\n")
    string = string.replace("\\032"," ")
    string = string.replace("\\035","#")
    string = string.replace("\\092","\\")

    return string

def check_operand_type( type, value ):

    if type == "bool":

        if value != "false" and value != "true":

            return False

        return True
    
    elif type == "int":

        try:

            int( value )

        except:

            return False

        return True

    elif type == "string":

        if value is not None:

            if " " in value or "\n" in value:

                return False

            # Get backslash occurrences
            occurrences = [i for i, c in enumerate(value) if c == "\\"]

            for occurrence in occurrences:

                if occurrence + 3 >= len( value ):

                    return False

                for letter in value[occurrence + 1:occurrence + 4]:

                    if not letter.isdigit():

                        return False

        return True

    elif type=="nil":

        if value != "nil":

            return False

        return True
    
    elif type=="var":

        if "@" not in value:

            return False

        if value[0: value.find("@")] not in ["GF","LF","TF"]:

            return False

        return True

    elif type == "type" or type == "label":
        
        return True

    else:

        return False

#------------------------------------------------#
#                                                #
#   Main function                                #
#                                                #
#------------------------------------------------#

if __name__ == "__main__":
    
    # Pass the arguments to process them
    source_file, input_file = handle_arguments( sys.argv[1:] )

    # Open files
    source, input = open_files( source_file, input_file )

    # Create minidom from the source and try if it's well formed
    try:

        source_dom = ElementTree.parse( source )

    except:

        # Source isn't well formed
        sys.stderr.write("Zdrojovy subor nie je spravne formatovany.\n")
        exit(31)

    # Create a new interpret
    interpret = Interpret()

    # Create a new program
    program = Program( input.splitlines() )

    # Save the first tag as the root of a tree
    program_tag = source_dom.getroot()

    # The first tag should be the "program" tag
    check_program_tag( program_tag )

    # Loop trought instruction tags
    for instruction_tag in program_tag:

        # Check if the instruction has correct attributes
        check_instruction_tag( instruction_tag )

        # Check if there isn't already instruction with same order
        check_instruction_order( program, instruction_tag )

        # Create an instruction object
        instruction = Instruction( instruction_tag.attrib["opcode"].upper(), int( instruction_tag.attrib["order"] ) )

        # Define a variable for the opcode for a better work in next if statement
        opcode = instruction_tag.attrib["opcode"]

        instruction_arguments = []

        for argument_tag in instruction_tag:

            # check_argument_tag( argument_tag )

            # Check if arugment's value is compatibile with it's type
            if not check_operand_type( argument_tag.attrib["type"], argument_tag.text ):

                sys.stderr.write("Chybna struktura zdrojoveho XML suboru.\n")
                exit(32)

            # If argument is string
            if argument_tag.attrib["type"] == "string":
                
                # Check if string is empty and handle it
                handle_empty_string_in_argument_tag( argument_tag )
                
                # Transform string into readable form
                argument_tag.text = translate_string_value(argument_tag.text)

            # Add new argument to the instruction
            instruction.add_argument( InstructionArgument( argument_tag.attrib["type"], argument_tag.text ) )

        # Check if instruction is LABEL
        if opcode == "LABEL":
            
            program.labels.add_label( argument_tag.text, instruction.order )

        # Add the instruction to instruction runner
        program.program_counter.add_instruction( instruction )

    # Sort list of instructions by order
    program.program_counter.instructions.sort(key=lambda x: x.order)

    # Start an interpretation of the program
    interpret.run( program )

    # Exit with code 0
    exit(0)