#!/bin/sh
. $(dirname "$0")/functions.sh

# ADVERSIAL SCENARIO(s)
# check against bad stuff

echo SCENARIO: IDEAL SCENARIO

## alice funds
echo ALICE FUNDS CONTRACT WITH $algo_amnt
fund_app $app_addr $alice_addr $algo_amnt
check_funds $app_addr

## kim tries to claim

