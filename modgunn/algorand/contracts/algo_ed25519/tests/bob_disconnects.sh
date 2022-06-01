#!/bin/sh
. $(dirname "$0")/functions.sh

# BOB DISCONNECTS SCENARIO 1
# alice creates -> alice funds -> alice readies -> t1 passes -> alice punish refunds -> alice deletes
echo SCENARIO: BOB DISCONNECTS 1

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

## alice readies
echo ALICE SETS READY
alice_ready $app_index $alice_addr

## bob disconnects
echo BOB IS DISCONNECTED
echo WAITING UNTIL t1...
sleep 60
echo ENTERED t1...

## alice punish refunds
echo ALICE REFUNDS ALGO WITHOUT LEAKING SECRET
alice_refunded_bob_punished $app_index $alice_addr
check_funds $app_addr

## alice deletes
echo 'ALICE DELETES APP'
delete_app $app_index $bob_addr

## compare balances
compare_balances

## cleanup
clean_up


###########################

# BOB DISCONNECTS SCENARIO 2
# alice creates -> alice funds -> t0 passes -> t1 passes -> alice punish refunds -> alice deletes
echo SCENARIO: BOB DISCONNECTS 2

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

## alice disconnects
echo ALICE DISCONNECTS
echo WAITING UNTIL t0
sleep 30
echo ENTERED t0...

## bob disconnects
echo BOB DISCONNECTS
echo WAITING UNTIL t1...
sleep 30
echo ENTERED t1...

## alice punish refunds
echo ALICE IS BACK
echo ALICE REFUNDS ALGO WITHOUT LEAKING SECRET
alice_refunded_bob_punished $app_index $alice_addr
check_funds $app_addr

## alice deletes
echo 'ALICE DELETES APP'
delete_app $app_index $bob_addr

## compare balances
compare_balances

## cleanup
clean_up