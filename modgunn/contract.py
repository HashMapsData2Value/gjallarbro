from errno import EDEADLK
from pyteal import *


def approval():
    # globals
    alice_ready = Bytes("ready")  # byteslice
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

    on_create_t0 = Btoi(Txn.application_args[0])
    on_create_t1 = Btoi(Txn.application_args[1])
    on_create = Seq(
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
                Txn.sender() == Tmpl.Addr("TMPL_ALICE_ALGO_ADDRESS"),
#                Txn.application_args[1] == Bytes("5866666666666666666666666666666666666666666666666666666666666666"),
                Substring(Txn.application_args[1], Int(0), Int(31)) == Bytes("5866666666666666666666666666666666666666666666666666666666666666"),
#                Ed25519Verify(Bytes('gjallarbro'), Txn.note(), Tmpl.Bytes("TMPL_ALICE_PARTIAL_PK")),
#                Btoi(Txn.application_args[1]) == Int(1),  # REPLACE with ED25519VERIFY
                Global.latest_timestamp() < App.globalGet(t0),
            )
        ),
        closeAlgoTo(Tmpl.Addr("TMPL_ALICE_ALGO_ADDRESS")),
        Approve(),
    )

    on_ready = Seq(
        Assert(
            And(
                App.globalGet(alice_ready) == Int(0),
                Global.latest_timestamp() < App.globalGet(t0),
                Txn.sender() == Tmpl.Addr("TMPL_ALICE_ALGO_ADDRESS"),
            ),
        ),
        App.globalPut(alice_ready, Int(1)),
        Approve(),
    )

    on_leaky_claim = Seq(
        Assert(
            And(
                Txn.sender() == Tmpl.Addr("TMPL_BOB_ALGO_ADDRESS"),
                Substring(Txn.application_args[1], Int(0), Int(31)) == Bytes("base16", "0FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"),
#                Ed25519Verify(Bytes('gjallarbro'), Txn.note(), Tmpl.Bytes("TMPL_BOB_PARTIAL_PK")),
#                Btoi(Txn.application_args[1]) == Int(1),  # REPLACE with ED25519VERIFY
                Or(
                    Global.latest_timestamp() >= App.globalGet(t0),
                    App.globalGet(alice_ready) == Int(1),
                ),
                Global.latest_timestamp() < App.globalGet(t1),
            )
        ),
        closeAlgoTo(Tmpl.Addr("TMPL_BOB_ALGO_ADDRESS")),
        Approve(),
    )

    on_punish_refund = Seq(
        Assert(
            And(
                Global.latest_timestamp() >= App.globalGet(t1),
                Txn.sender() == Tmpl.Addr("TMPL_ALICE_ALGO_ADDRESS"),
            ),
        ),
        closeAlgoTo(Tmpl.Addr("TMPL_ALICE_ALGO_ADDRESS")),
        Approve(),
    )

    on_delete = Seq(
        Assert(
            And(
                Balance(Global.current_application_address()) == Int(0),
                Or(
                    Txn.sender() == Tmpl.Addr("TMPL_ALICE_ALGO_ADDRESS"),
                    Txn.sender() == Tmpl.Addr("TMPL_BOB_ALGO_ADDRESS"),
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