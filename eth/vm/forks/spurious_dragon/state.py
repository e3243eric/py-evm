from typing import Type

from eth_utils import (
    encode_hex,
)

from eth.abc import (
    MessageComputationAPI,
    SignedTransactionAPI,
    TransactionExecutorAPI,
)
from eth.vm.forks.homestead.state import (
    HomesteadState,
    HomesteadTransactionExecutor,
)

from .computation import SpuriousDragonMessageComputation
from ._utils import collect_touched_accounts


class SpuriousDragonTransactionExecutor(HomesteadTransactionExecutor):
    def finalize_computation(self,
                             transaction: SignedTransactionAPI,
                             computation: MessageComputationAPI) -> MessageComputationAPI:
        computation = super().finalize_computation(transaction, computation)

        #
        # EIP161 state clearing
        #
        touched_accounts = collect_touched_accounts(computation)

        for account in touched_accounts:
            should_delete = (
                self.vm_state.account_exists(account)
                and self.vm_state.account_is_empty(account)
            )
            if should_delete:
                self.vm_state.logger.debug2(
                    "CLEARING EMPTY ACCOUNT: %s",
                    encode_hex(account),
                )
                self.vm_state.delete_account(account)

        return computation


class SpuriousDragonState(HomesteadState):
    message_computation_class: Type[MessageComputationAPI] = SpuriousDragonMessageComputation
    transaction_executor_class: Type[TransactionExecutorAPI] = SpuriousDragonTransactionExecutor
