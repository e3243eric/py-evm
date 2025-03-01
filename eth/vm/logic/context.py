from typing import Tuple

from eth_typing import (
    Address,
)

from eth import constants

from eth.abc import (
    MessageComputationAPI,
)
from eth.exceptions import (
    OutOfBoundsRead,
)

from eth._utils.address import (
    force_bytes_to_address,
)
from eth._utils.numeric import (
    ceil32,
)

from eth.vm.computation import MessageComputation


def balance(computation: MessageComputation) -> None:
    addr = force_bytes_to_address(computation.stack_pop1_bytes())
    push_balance_of_address(addr, computation)


def selfbalance(computation: MessageComputation) -> None:
    push_balance_of_address(computation.msg.storage_address, computation)


def push_balance_of_address(address: Address, computation: MessageComputationAPI) -> None:
    balance = computation.state.get_balance(address)
    computation.stack_push_int(balance)


def origin(computation: MessageComputation) -> None:
    computation.stack_push_bytes(computation.transaction_context.origin)


def address(computation: MessageComputation) -> None:
    computation.stack_push_bytes(computation.msg.storage_address)


def caller(computation: MessageComputation) -> None:
    computation.stack_push_bytes(computation.msg.sender)


def callvalue(computation: MessageComputation) -> None:
    computation.stack_push_int(computation.msg.value)


def calldataload(computation: MessageComputation) -> None:
    """
    Load call data into memory.
    """
    start_position = computation.stack_pop1_int()

    value = computation.msg.data_as_bytes[start_position:start_position + 32]
    padded_value = value.ljust(32, b'\x00')
    normalized_value = padded_value.lstrip(b'\x00')

    computation.stack_push_bytes(normalized_value)


def calldatasize(computation: MessageComputation) -> None:
    size = len(computation.msg.data)
    computation.stack_push_int(size)


def calldatacopy(computation: MessageComputation) -> None:
    (
        mem_start_position,
        calldata_start_position,
        size,
    ) = computation.stack_pop_ints(3)

    computation.extend_memory(mem_start_position, size)

    word_count = ceil32(size) // 32
    copy_gas_cost = word_count * constants.GAS_COPY

    computation.consume_gas(copy_gas_cost, reason="CALLDATACOPY fee")

    value = computation.msg.data_as_bytes[
        calldata_start_position: calldata_start_position + size
    ]
    padded_value = value.ljust(size, b'\x00')

    computation.memory_write(mem_start_position, size, padded_value)


def chain_id(computation: MessageComputation) -> None:
    computation.stack_push_int(computation.state.execution_context.chain_id)


def codesize(computation: MessageComputation) -> None:
    size = len(computation.code)
    computation.stack_push_int(size)


def codecopy(computation: MessageComputation) -> None:
    (
        mem_start_position,
        code_start_position,
        size,
    ) = computation.stack_pop_ints(3)

    computation.extend_memory(mem_start_position, size)

    word_count = ceil32(size) // 32
    copy_gas_cost = constants.GAS_COPY * word_count

    computation.consume_gas(
        copy_gas_cost,
        reason="CODECOPY: word gas cost",
    )

    with computation.code.seek(code_start_position):
        code_bytes = computation.code.read(size)

    padded_code_bytes = code_bytes.ljust(size, b'\x00')

    computation.memory_write(mem_start_position, size, padded_code_bytes)


def gasprice(computation: MessageComputation) -> None:
    computation.stack_push_int(computation.transaction_context.gas_price)


def extcodesize(computation: MessageComputation) -> None:
    account = force_bytes_to_address(computation.stack_pop1_bytes())
    code_size = len(computation.state.get_code(account))

    computation.stack_push_int(code_size)


def extcodecopy_execute(computation: MessageComputationAPI) -> Tuple[Address, int]:
    """
    Runs the logical component of extcodecopy, without charging gas.

    :return (target_address, copy_size): useful for the caller to determine gas costs
    """
    account = force_bytes_to_address(computation.stack_pop1_bytes())
    (
        mem_start_position,
        code_start_position,
        size,
    ) = computation.stack_pop_ints(3)

    computation.extend_memory(mem_start_position, size)

    code = computation.state.get_code(account)

    code_bytes = code[code_start_position:code_start_position + size]
    padded_code_bytes = code_bytes.ljust(size, b'\x00')

    computation.memory_write(mem_start_position, size, padded_code_bytes)

    return account, size


def consume_extcodecopy_word_cost(computation: MessageComputationAPI, size: int) -> None:
    word_count = ceil32(size) // 32
    copy_gas_cost = constants.GAS_COPY * word_count
    computation.consume_gas(
        copy_gas_cost,
        reason='EXTCODECOPY: word gas cost',
    )


def extcodecopy(computation: MessageComputation) -> None:
    _address, size = extcodecopy_execute(computation)
    consume_extcodecopy_word_cost(computation, size)


def extcodehash(computation: MessageComputation) -> None:
    """
    Return the code hash for a given address.
    EIP: https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1052.md
    """
    account = force_bytes_to_address(computation.stack_pop1_bytes())
    state = computation.state

    if state.account_is_empty(account):
        computation.stack_push_bytes(constants.NULL_BYTE)
    else:
        computation.stack_push_bytes(state.get_code_hash(account))


def returndatasize(computation: MessageComputation) -> None:
    size = len(computation.return_data)
    computation.stack_push_int(size)


def returndatacopy(computation: MessageComputation) -> None:
    (
        mem_start_position,
        returndata_start_position,
        size,
    ) = computation.stack_pop_ints(3)

    if returndata_start_position + size > len(computation.return_data):
        raise OutOfBoundsRead(
            "Return data length is not sufficient to satisfy request.  Asked "
            f"for data from index {returndata_start_position} "
            f"to {returndata_start_position + size}.  "
            f"Return data is {len(computation.return_data)} bytes in length."
        )

    computation.extend_memory(mem_start_position, size)

    word_count = ceil32(size) // 32
    copy_gas_cost = word_count * constants.GAS_COPY

    computation.consume_gas(copy_gas_cost, reason="RETURNDATACOPY fee")

    value = computation.return_data[returndata_start_position: returndata_start_position + size]

    computation.memory_write(mem_start_position, size, value)
