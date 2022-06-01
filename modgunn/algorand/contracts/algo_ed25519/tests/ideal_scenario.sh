#!/bin/sh
. $(dirname "$0")/functions.sh

# IDEAL SCENARIO
# alice creates -> alice funds -> alice readies -> bob leaky claims -> alice deletes
echo SCENARIO: IDEAL SCENARIO

## alice creates
echo ALICE CREATES
deploy_app
app_index=$(cat deploy_app.tx_output | grep -o 'index.*' | cut -d ' ' -f 2)
app_addr=$(goal app info --app-id $app_index | grep -o 'Application account.*' | tr -s ' ' | cut -d ' ' -f 3)

echo APP ASSIGNED INDEX: $app_index

## alice funds
echo ALICE FUNDS CONTRACT WITH $algo_amnt
fund_app $app_addr $alice_addr $algo_amnt
check_funds $app_addr

## bob commits on 2nd blockchain
echo '*BOB LOCKED UP x FUNDS ON X*'

## alice readies
echo ALICE SETS READY
alice_ready $app_index $alice_addr

## bob leaky claims
echo BOB CLAIMS ALGO AND LEAKS SECRET
bob_leaky_claim $app_index $bob_addr $bob_partial_pk # UNTIL WE GET NEW OPCODE
check_funds $app_addr

## alice deletes
echo 'ALICE DELETES APP'
delete_app $app_index $alice_addr

## compare balances
compare_balances

## cleanup
clean_up