#!/bin/sh
. $(dirname "$0")/functions.sh

# ALICE REGRETS SCENARIO
# alice creates -> alice funds -> alice regrets -> alice leaky refund -> alice deletes
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

## alice leaky refund
echo ALICE REFUNDS ALGO AND LEAKS SECRET
alice_leaky_refund $app_index $alice_addr $alice_partial_pk # UNTIL WE GET NEW OPCODE
check_funds $app_addr

## bob gets access on 2nd blockchain
echo '*BOB GAINS ACCESS TO LOCKED FUNDS on X*'

## alice deletes
echo 'ALICE DELETES APP'
delete_app $app_index $alice_addr

## compare balances
compare_balances

## cleanup
clean_up