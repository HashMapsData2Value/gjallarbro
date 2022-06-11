from errno import EDEADLK
from pyteal import *


def approval(alice_addr, alice_partial_pk, bob_addr, bob_partial_pk, t0_timestamp, t1_timestamp):
    # globals
    alice_algo_addr = Addr(alice_addr)
    alice_xmr_pk = Bytes("base16", alice_partial_pk)
    bob_algo_addr = Addr(bob_addr)
    bob_xmr_pk = Bytes("base16", bob_partial_pk)
    t0 = Int(t0_timestamp)
    t1 = Int(t1_timestamp)
    alice_ready = Bytes("ready")  # byteslice

    @Subroutine(TealType.none)
    def closeAlgoTo(address: Expr) -> Expr:
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.close_remainder_to: address,
                }
            ),
            InnerTxnBuilder.Submit(),
        )


    on_create = Seq(
        App.globalPut(alice_ready, Int(0)),
        Assert(
            And(
                Global.latest_timestamp() < t0,
                t0 < t1,
            )
        ),
        Approve(),
    )

    on_leaky_refund = Seq(
        Assert(
            And(
                Txn.sender() == alice_algo_addr,
                Extract(Txn.application_args[1], Int(0), Int(32)) == Bytes("Xfffffffffffffffffffffffffffffff"),
                Ed25519Verify(alice_algo_addr, Txn.application_args[1], alice_xmr_pk),
                Global.latest_timestamp() < t0,
            )
        ),
        closeAlgoTo(alice_algo_addr),
        Approve(),
    )

    on_ready = Seq(
        Assert(
            And(
                App.globalGet(alice_ready) == Int(0),
                Global.latest_timestamp() < t0,
                Txn.sender() == alice_algo_addr,
            ),
        ),
        App.globalPut(alice_ready, Int(1)),
        Approve(),
    )

    on_leaky_claim = Seq(
        Assert(
            And(
                Txn.sender() == bob_algo_addr,
                Extract(Txn.application_args[1], Int(0), Int(32)) == Bytes("Xfffffffffffffffffffffffffffffff"),
                Ed25519Verify(bob_algo_addr, Txn.application_args[1], bob_xmr_pk),
                Or(
                    Global.latest_timestamp() >= t0,
                    App.globalGet(alice_ready) == Int(1),
                ),
                Global.latest_timestamp() < t1,
            )
        ),
        closeAlgoTo(bob_algo_addr),
        Approve(),
    )

    on_punish_refund = Seq(
        Assert(
            And(
                Global.latest_timestamp() >= t1,
                Txn.sender() == alice_algo_addr,
            ),
        ),
        closeAlgoTo(alice_algo_addr),
        Approve(),
    )

    on_plus_700 = Seq(
        Approve(),
    )

    on_delete = Seq(
        Assert(
            And(
                Balance(Global.current_application_address()) == Int(0),
                Or(
                    Txn.sender() == alice_algo_addr,
                    Txn.sender() == bob_algo_addr,
                ),
            ),
        ),
        Approve(),
    )

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        [on_call_method == Bytes("leaky_refund"), on_leaky_refund],
        [on_call_method == Bytes("ready"), on_ready],
        [on_call_method == Bytes("leaky_claim"), on_leaky_claim],
        [on_call_method == Bytes("punish_refund"), on_punish_refund],
        [on_call_method == Bytes("+700"), on_plus_700],
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, on_call],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete],
        [
            Or(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.on_completion() == OnComplete.UpdateApplication,
            ),
            Reject(),
        ],
    )

    return program


def clear():
    return Approve()