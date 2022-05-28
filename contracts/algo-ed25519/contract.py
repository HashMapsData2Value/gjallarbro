from pyteal import *


def approval():
    # globals
    alice_algo_address = Bytes("a_addr")  # byteslice
    alice_partial_pk = Bytes("a_ppk")  # byteslice
    alice_ready = Bytes("ready")  # byteslice
    bob_algo_address = Bytes("b_addr")  # byteslice
    bob_partial_pk = Bytes("b_ppk")  # byteslice
    t0 = Bytes("t0")  # uint64
    t1 = Bytes("t1")  # uint64

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

    on_create_t0 = Btoi(Txn.application_args[4])
    on_create_t1 = Btoi(Txn.application_args[5])
    on_create = Seq(
        App.globalPut(alice_algo_address, Txn.application_args[0]),
        App.globalPut(alice_partial_pk, Txn.application_args[1]),
        App.globalPut(bob_algo_address, Txn.application_args[2]),
        App.globalPut(bob_partial_pk, Txn.application_args[3]),
        App.globalPut(t0, on_create_t0),
        App.globalPut(t1, on_create_t1),
        App.globalPut(alice_ready, Int(0)),
        Assert(
            And(
                Global.latest_timestamp() < on_create_t0,
                on_create_t0 < on_create_t1,
            )
        ),
        Approve(),
    )

    on_leaky_refund = Seq(
        Assert(
            And(
                Txn.sender() == App.globalGet(alice_algo_address),
                Txn.note()
                == App.globalGet(alice_partial_pk),  # REPLACE with NEW OPCODE
                Global.latest_timestamp() < App.globalGet(t0),
            )
        ),
        closeAlgoTo(App.globalGet(alice_algo_address)),
        Approve(),
    )

    on_ready = Seq(
        Assert(
            And(
                App.globalGet(alice_ready) == Int(0),
                Global.latest_timestamp() < App.globalGet(t0),
                Txn.sender() == App.globalGet(alice_algo_address),
            ),
        ),
        App.globalPut(alice_ready, Int(1)),
        Approve(),
    )

    on_leaky_claim = Seq(
        Assert(
            And(
                Txn.sender() == App.globalGet(bob_algo_address),
                Txn.note() == App.globalGet(bob_partial_pk),  # REPLACE with NEW OPCODE
                Or(
                    Global.latest_timestamp() >= App.globalGet(t0),
                    App.globalGet(alice_ready) == Int(1),
                ),
                Global.latest_timestamp() < App.globalGet(t1),
            )
        ),
        closeAlgoTo(App.globalGet(bob_algo_address)),
        Approve(),
    )

    on_punish_refund = Seq(
        Assert(
            And(
                Global.latest_timestamp() >= App.globalGet(t1),
                Txn.sender() == App.globalGet(alice_algo_address),
            ),
        ),
        closeAlgoTo(App.globalGet(alice_algo_address)),
        Approve(),
    )

    on_delete = Seq(
        Assert(
            And(
                Balance(Global.current_application_address()) == Int(0),
                Or(
                    Txn.sender() == App.globalGet(alice_algo_address),
                    Txn.sender() == App.globalGet(bob_algo_address),
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
