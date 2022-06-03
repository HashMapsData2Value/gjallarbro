# Initalize

alice_addr=$(goal account list | awk "NR==1"{print} |  awk '{print $2}')
bob_addr=$(goal account list | awk "NR==2"{print} |  awk '{print $2}')
kim_addr=$(goal account list | awk "NR==3"{print} |  awk '{print $2}')

alice_partial_pk=V16/mCosfYn+Anu7SGM1JcVmnjQQwihJ/iMyu1YB2y0=
# alice_partial_sk=Ea++z24o8bTLfUREBtG8CTrMf1UILOtg7hWSF8+7SaBXXr+YKix9if4Ce7tIYzUlxWaeNBDCKEn+IzK7VgHbLQ==
bob_partial_pk=juRWPz8FCi9myq/RxvsMPH3JNYlYIvKtt3633hGSiIE=
# bob_partial_sk=3/1u8dm+WwbXPd6FemBn84IIhtF9ijD8Vd93QRqm57mO5FY/PwUKL2bKr9HG+ww8fck1iVgi8q23frfeEZKIgQ==

algo_amnt=50003000 #needs to cover Bob's ideally 2 tx fees but potentially 3 tx fees 

deploy_app(){
    local NOW=$(date +%s) # Unix Time
    local t0=`expr $NOW + 30`
    local t1=`expr $t0 + 30`

    goal app create --creator $alice_addr --approval-prog /data/build/approval.teal --clear-prog /data/build/clear.teal --global-byteslices 4 --global-ints 3 --local-byteslices 0 --local-ints 0 --app-arg "addr:$alice_addr" --app-arg "str:$alice_partial_pk" --app-arg "addr:$bob_addr" --app-arg "str:$bob_partial_pk" --app-arg "int:$t0" --app-arg "int:$t1" > deploy_app.tx_output
}

fund_app(){
    goal clerk send --to $1 --from $2 --amount $3 > fund_app.tx_output
}

check_funds(){
    goal account balance --address $1 | cut -d ' ' -f 1 
}

alice_ready(){
    goal app call --app-id $1 --from $2 --app-arg "str:ready" > alice_ready.tx_output
}

alice_leaky_refund(){
    # Called before Alice is "ready" or t0
    goal app call --app-id $1 --from $2 --app-arg "str:leaky_refund" --note $3 > alice_leaky_refund.tx_output
}

alice_refunded_bob_punished(){
    # Called after t1
    goal app call --app-id $1 --from $2 --app-arg "str:punish_refund" > alice_refunded_bob_punished.tx_output
}

bob_leaky_claim(){
    # Called after Alice is "ready" or t0
    goal app call --app-id $1 --from $2  --app-arg "str:leaky_claim" --note $3 > bob_leaky_claim.tx_output
}

delete_app(){
    goal app delete --app-id $1 --from $2 > delete_app.tx_output
}

clean_up(){ 
    rm *.tx_output
}


alice_funds_start=$(check_funds $alice_addr)
bob_funds_start=$(check_funds $bob_addr) 

compare_balances(){
    alice_funds_end=$(check_funds $alice_addr)
    bob_funds_end=$(check_funds $bob_addr) 

    alice_delta=`expr $alice_funds_end - $alice_funds_start`
    bob_delta=`expr $bob_funds_end - $bob_funds_start`

    echo Alice had $alice_funds_start µAlgo, now she has $alice_funds_end µAlgo. Delta: $alice_delta µA.
    echo Bob had $bob_funds_start µAlgo, now he has $bob_funds_end µAlgo. Delta: $bob_delta µA.

}