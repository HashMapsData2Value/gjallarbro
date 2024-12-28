from algopy import (
  Bytes,
  arc4,
  ARC4Contract,
  Account,
  Global,
  GlobalState,
  String,
  Txn,
  itxn,
  UInt64,
  subroutine,
  op,
)

# Ali <-- Algo/ASA asset holder, wants to swap for foreign asset
# Xin <-- Foreign asset holder, wants to swap for Algo/ASA asset
class LeakSwap(ARC4Contract):
    def __init__(self) -> None:
        self.ali_algo_addr = GlobalState(
            arc4.Address, key=b"ali_algo_addr", description="Ali's Algo address")
        self.ali_xternal_pk = GlobalState(
            Bytes, key=b"ali_xternal_pk", description="Ali's xternal public key")

        self.xin_algo_addr = GlobalState(
            arc4.Address, key=b"xin_algo_addr", description="Xin's Algo address")
        self.xin_xternal_pk = GlobalState(
            Bytes, key=b"xin_xternal_pk", description="Xin's xternal public key")

        self.t0 = GlobalState(UInt64, key=b"t0_timestamp", description="Timestamp to enter Leaky Claim")
        self.t1 = GlobalState(UInt64, key=b"t1_timestamp", description="Timestamp to enter Punish Refund")

        self.ali_ready = GlobalState(bool, key=b"ali_ready", description="Ali's flag to enter Leaky Claim")

        self.data_to_sign = Global.current_application_address.bytes

    @arc4.abimethod()
    def hello(self, name: String) -> String:
        return "Hello, " + name
    
    @arc4.abimethod(create="require")
    def create(self,
               ali_algo_addr: arc4.Address,
               ali_xternal_pk: Bytes,
               xin_algo_addr: arc4.Address,
               xin_xternal_pk: Bytes,
               t0: UInt64,
               t1: UInt64) -> None:
        """
        Create the LeakSwap contract.
        """
        self.ali_algo_addr.value = ali_algo_addr
        self.ali_xternal_pk.value = ali_xternal_pk
        self.xin_algo_addr.value = xin_algo_addr
        self.xin_xternal_pk.value = xin_xternal_pk
        self.t0.value = t0
        self.t1.value = t1

        self.ali_ready.value = False

        assert self.t0.value > Global.latest_timestamp
        assert self.t1.value > self.t0.value

    # arc4.abimethod(delete="require")
    # def delete(self) -> None:
    #    """
    #    Contract should be deletable once there are no more funds left.
    #    """    
    # 

    @subroutine
    def disburse_funds(self, recipient: arc4.Address) -> None:
        """
        Disburse funds to the recipient.
        """
        itxn.Payment(
            receiver=recipient.native,
            close_remainder_to=recipient.native,
            fee=0,
        ).submit()

    # TODO: For when we have ASA support
    # @subroutine
    # def disburse_assets(self, recipient: arc4.Address):
    #   """
    #   Disburses ASA funds to the recipient.
    #   """
    #     itxn.AssetTransfer(
    #         asset_id=self.asset_id,
    #         amount=?,
    #         close_to=recipient.native,
    #         fee=0,
    #     ).submit()

    @subroutine
    def leaky_verify_ed25519(self, signature: Bytes, xternal_pk: Bytes) -> None:
        """
        Verifies that the user has provided a broken signature signed by the xternal pk.
        The broken signature leaks the private key, because it uses an R value whose scalar
        is known: r = 1.
        """
        assert op.extract(signature, 0, 32) == Bytes(b"Xfffffffffffffffffffffffffffffff")
        assert op.ed25519verify_bare(self.data_to_sign, signature, xternal_pk)

    # TODO: For when we have secp256k1 support, to swap on other chains
    # @subroutine
    # def leaky_verify_secp256k1(self, signature, xternal_pk):
    # ...
    # ...
    # ...

    @arc4.abimethod()
    def set_ready(self) -> None:
        """
        Ali sets the contract to ready once Xin has locked up funds on the xternal chain.
        (If Ali times out, the contract will enter an equivalent "ready" state after t0.)
        """
        assert Txn.sender == self.ali_algo_addr.value.native
        self.ali_ready.value = True

    @arc4.abimethod()
    def leaky_refund(self, signature: Bytes) -> None:
        """
        Ali noticed that Xin has not deposited funds on the xternal chain (fast enough) and
        wants to refund her Algo/ASA. But the refund leaks Ali's xternal secret key, in case
        Xin does lock up funds in the meanwhile and needs Ali's xternal secret key to reclaim.
        """
        # Check called by Ali
        assert Txn.sender == self.ali_algo_addr.value.native
        
        # Check contract has not passed t0/ready
        assert Global.latest_timestamp <= self.t0.value
        assert self.ali_ready.value == False
        
        # Force Ali to leak xternal secret key
        self.leaky_verify_ed25519(signature, self.ali_xternal_pk.value)
        
        # Return Ali's funds
        self.disburse_funds(self.ali_algo_addr.value)

    @arc4.abimethod()
    def leaky_claim(self, signature: Bytes) -> None:
        """
        The contract has entered "ready" state, either because Ali set it to ready (after noticing that
        Xin locked funds up) or because t0 has passed. Xin can now claim Ali's Algo/ASA, doing so by
        leaking the xternal secret key. That will allow Ali to claim the xternal funds
        """
        # Check called by Xin
        assert Txn.sender == self.xin_algo_addr.value.native

        # Check contract has passed t0/ready
        assert (
            Global.latest_timestamp > self.t0.value or self.ali_ready.value == True
        )
        # Check contract has not passed t1
        assert Global.latest_timestamp <= self.t1.value
        
        # Force Xin to leak xternal secret key
        self.leaky_verify_ed25519(signature, self.xin_xternal_pk.value)
        
        # Disburse funds to Xin
        self.disburse_funds(self.xin_algo_addr.value)

    @arc4.abimethod()
    def punish_refund(self) -> None:
        # Check called by Ali, in case she wants to punish Xin
        assert Txn.sender == self.ali_algo_addr.value.native
        
        # Check contract has passed t1
        assert Global.latest_timestamp > self.t1.value

        # Return Ali's funds
        self.disburse_funds(self.ali_algo_addr.value)