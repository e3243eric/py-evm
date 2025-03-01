from eth.vm.computation import MessageComputation


def mstore(computation: MessageComputation) -> None:
    start_position = computation.stack_pop1_int()
    value = computation.stack_pop1_bytes()

    padded_value = value.rjust(32, b'\x00')
    normalized_value = padded_value[-32:]

    computation.extend_memory(start_position, 32)

    computation.memory_write(start_position, 32, normalized_value)


def mstore8(computation: MessageComputation) -> None:
    start_position = computation.stack_pop1_int()
    value = computation.stack_pop1_bytes()

    padded_value = value.rjust(1, b'\x00')
    normalized_value = padded_value[-1:]

    computation.extend_memory(start_position, 1)

    computation.memory_write(start_position, 1, normalized_value)


def mload(computation: MessageComputation) -> None:
    start_position = computation.stack_pop1_int()

    computation.extend_memory(start_position, 32)

    value = computation.memory_read_bytes(start_position, 32)
    computation.stack_push_bytes(value)


def msize(computation: MessageComputation) -> None:
    computation.stack_push_int(len(computation._memory))
