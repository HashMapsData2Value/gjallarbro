aaa=JCGNB4PJBLBMJIJQHOWNLXJKGUQDLNOTSWOEZMXVG7F3RG23NYR2DOEH4U
baa=QIK2JTH3J57PU7WLYONAWC7VBLXRNYRRJZJQZ5LXKRZKPEWIXB2WAK64A4

keys=$(../venv/bin/python3 monero/main.py keys) 
sec=$(echo $keys | awk '{print $1}')
pub=$(echo $keys | awk '{print $2}')

# for testing both have the same pub
aed=$pub
bed=$pub

hash=$(../venv/bin/python3 algorand/main.py generate -c algo_ed25519 -aaa $aaa -aed $aed -baa $baa -bed $bed)
Rs=$(../venv/bin/python3 monero/main.py signature -p $pub -s $sec -H $hash)
echo $Rs