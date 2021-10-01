# Global Server Load Balancing Test Suite

## Testing Primary and Secondary Site Failover

```
export HOST="ggw.dev.api.gov.bc.ca"
export GOLD="142.34.229.4"
export GOLDDR="142.34.64.4"

export KUBE_PRIMARY_CONTEXT=""
export KUBE_DR_CONTEXT=""
export HEALTH_CHECK_SERVICE=""

echo '
GSLB_HOST="$HOST.glb.gov.bc.ca"
BOTH="$GOLD\n$GOLDDR"

start=`date +%s`

function echo {
  diff=$(expr `date +%s` - $start)
  printf "[%05d] %s\n" $diff "$1"
}

# try <attempts> <wait> <cmd>
function try {
  n=0
  until [ "$n" -ge $1 ]
  do
    "${@:3}" && return 0
    n=$((n+1))
    sleep $2
  done
  echo "FAILED COMMAND ${@:3}"
  exit 1
}

function scale_gold {
  REPLICAS=$1
  kubectl config use-context $KUBE_PRIMARY_CONTEXT > /dev/null
  kubectl scale --replicas=$REPLICAS deployment $HEALTH_CHECK_SERVICE > /dev/null
  echo "-> SCALED GOLD TO $REPLICAS replicas"
}

function scale_golddr {
  REPLICAS=$1
  kubectl config use-context $KUBE_DR_CONTEXT > /dev/null
  kubectl scale --replicas=$REPLICAS deployment $HEALTH_CHECK_SERVICE > /dev/null
  echo "-> SCALED GOLDDR TO $REPLICAS replicas"
}

function is_up {
  IP=$1
  RES=`curl -s -k -m 1 https://$IP/health -H "Host: $HOST"`
  if [ "$RES" = "<html><body>iamalive</body></html>" ]
  then
    print_ip $IP " : UP"
    return 0
  else
    print_ip $IP " : DOWN"
    return 1
  fi
}

function is_down {
  IP=$1
  RES=`curl -s -k -m 1 https://$IP/health -H "Host: $HOST"`
  if [ "$RES" = "<html><body>iamalive</body></html>" ]
  then
    print_ip $IP " : UP"
    return 1
  else
    print_ip $IP " : DOWN"
    return 0
  fi
}

function print_ip {
  EXP_IP="$1"
  MSG="$2"
  if [ "$EXP_IP" = "$GOLD" ]
  then
    echo "-> GOLD $MSG"
  elif [ "$EXP_IP" = "$GOLDDR" ]
  then
    echo "-> GOLDDR $MSG"
  elif [ "$EXP_IP" = "$GOLD\n$GOLDDR" ]
  then
    echo "-> BOTH IPS $MSG"
  elif [ "$EXP_IP" = "$GOLDDR\n$GOLD" ]
  then
    echo "-> BOTH IPS $MSG"
  else
    echo "-> UNEXPECTED DIG ($EXP_IP) $MSG"
  fi
}

function expect_routing_to {
  MATCH="$1"
  IP=`dig $GSLB_HOST +short`
  print_ip "$MATCH" " : EXPECTING.."
  if [ "$IP" = "$MATCH" ]
  then
    echo "-> SUCCESS!"
    return 0
  fi
  echo "-> FAILED - NOT WHAT IS EXPECTED"
  return 1
}

function print_header {
  echo ""
  echo "---------"
  echo "$1"
  echo "---------"

}

function baseline_all_down {
  print_header "BASELINE ALL DOWN - down/down"
  scale_gold 0
  scale_golddr 0
  try 20 1 is_down $GOLD
  try 20 1 is_down $GOLDDR
}

function test_happy_path {
  print_header "HAPPY PATH - up/up - expect GOLD IP"
  scale_gold 2
  scale_golddr 2
  try 20 1 is_up $GOLD
  try 20 1 is_up $GOLDDR
  try 15 2 expect_routing_to $GOLD
}

function test_switch_to_dr {
  print_header "SWITCH TO DR - down/up - expect GOLDDR IP"
  scale_gold 0
  scale_golddr 2
  try 20 1 is_down $GOLD
  try 20 1 is_up $GOLDDR
  try 15 2 expect_routing_to $GOLDDR
}

function test_total_outage {
  print_header "TOTAL OUTAGE - down/down - expect BOTH IP"
  scale_gold 0
  scale_golddr 0
  try 20 1 is_down $GOLD
  try 20 1 is_down $GOLDDR
  try 15 2 expect_routing_to "$BOTH"
}

function test_switch_to_primary {
  print_header "SWITCH TO PRIMARY - up/up - expect GOLD IP"
  scale_gold 2
  scale_golddr 2
  try 20 1 is_up $GOLD
  try 20 1 is_up $GOLDDR
  try 15 2 expect_routing_to $GOLD
}

function test_dr_down {
  print_header "TAKE DR DOWN - up/down - expect GOLD IP"
  scale_gold 2
  scale_golddr 0
  try 20 1 is_up $GOLD
  try 20 1 is_down $GOLDDR
  try 15 2 expect_routing_to $GOLD
}

function test_dr_then_recovery {
  print_header "DR THEN RECOVERY"
  scale_gold 0
  scale_golddr 2
  try 20 1 is_down $GOLD
  try 20 1 is_up $GOLDDR
  try 15 2 expect_routing_to "$GOLDDR"
  scale_gold 2
  try 15 2 expect_routing_to "$GOLD"
}

baseline_all_down
test_happy_path
test_switch_to_dr
test_total_outage
test_switch_to_primary
test_dr_down
test_dr_then_recovery

' | bash

```

## Output for APS

```
[00000]
[00000] ---------
[00000] BASELINE ALL DOWN - down/down
[00000] ---------
[00001] -> SCALED GOLD TO 0 replicas
[00002] -> SCALED GOLDDR TO 0 replicas
[00003] -> GOLD  : DOWN
[00004] -> GOLDDR  : DOWN
[00004]
[00004] ---------
[00004] HAPPY PATH - up/up - expect GOLD IP
[00004] ---------
[00004] -> SCALED GOLD TO 2 replicas
[00005] -> SCALED GOLDDR TO 2 replicas
[00006] -> GOLD  : DOWN
[00007] -> GOLD  : DOWN
[00008] -> GOLD  : DOWN
[00009] -> GOLD  : DOWN
[00010] -> GOLD  : DOWN
[00012] -> GOLD  : DOWN
[00014] -> GOLD  : DOWN
[00016] -> GOLD  : UP
[00017] -> GOLDDR  : DOWN
[00019] -> GOLDDR  : DOWN
[00021] -> GOLDDR  : DOWN
[00023] -> GOLDDR  : UP
[00023] -> GOLD  : EXPECTING..
[00023] -> SUCCESS!
[00023]
[00023] ---------
[00023] SWITCH TO DR - down/up - expect GOLDDR IP
[00023] ---------
[00023] -> SCALED GOLD TO 0 replicas
[00024] -> SCALED GOLDDR TO 2 replicas
[00024] -> GOLD  : DOWN
[00024] -> GOLDDR  : UP
[00024] -> GOLDDR  : EXPECTING..
[00024] -> FAILED - NOT WHAT IS EXPECTED
[00026] -> GOLDDR  : EXPECTING..
[00026] -> FAILED - NOT WHAT IS EXPECTED
[00028] -> GOLDDR  : EXPECTING..
[00028] -> FAILED - NOT WHAT IS EXPECTED
[00030] -> GOLDDR  : EXPECTING..
[00030] -> SUCCESS!
[00030]
[00030] ---------
[00030] TOTAL OUTAGE - down/down - expect BOTH IP
[00030] ---------
[00031] -> SCALED GOLD TO 0 replicas
[00031] -> SCALED GOLDDR TO 0 replicas
[00031] -> GOLD  : DOWN
[00032] -> GOLDDR  : DOWN
[00032] -> BOTH IPS  : EXPECTING..
[00032] -> FAILED - NOT WHAT IS EXPECTED
[00034] -> BOTH IPS  : EXPECTING..
[00035] -> FAILED - NOT WHAT IS EXPECTED
[00037] -> BOTH IPS  : EXPECTING..
[00037] -> FAILED - NOT WHAT IS EXPECTED
[00039] -> BOTH IPS  : EXPECTING..
[00039] -> FAILED - NOT WHAT IS EXPECTED
[00041] -> BOTH IPS  : EXPECTING..
[00041] -> FAILED - NOT WHAT IS EXPECTED
[00043] -> BOTH IPS  : EXPECTING..
[00043] -> FAILED - NOT WHAT IS EXPECTED
[00045] -> BOTH IPS  : EXPECTING..
[00045] -> FAILED - NOT WHAT IS EXPECTED
[00047] -> BOTH IPS  : EXPECTING..
[00047] -> FAILED - NOT WHAT IS EXPECTED
[00049] -> BOTH IPS  : EXPECTING..
[00049] -> FAILED - NOT WHAT IS EXPECTED
[00051] -> BOTH IPS  : EXPECTING..
[00051] -> FAILED - NOT WHAT IS EXPECTED
[00053] -> BOTH IPS  : EXPECTING..
[00053] -> FAILED - NOT WHAT IS EXPECTED
[00055] -> BOTH IPS  : EXPECTING..
[00055] -> SUCCESS!
[00055]
[00055] ---------
[00055] SWITCH TO PRIMARY - up/up - expect GOLD IP
[00055] ---------
[00055] -> SCALED GOLD TO 2 replicas
[00056] -> SCALED GOLDDR TO 2 replicas
[00056] -> GOLD  : DOWN
[00057] -> GOLD  : DOWN
[00059] -> GOLD  : DOWN
[00060] -> GOLD  : DOWN
[00061] -> GOLD  : DOWN
[00062] -> GOLD  : DOWN
[00064] -> GOLD  : DOWN
[00066] -> GOLD  : DOWN
[00067] -> GOLD  : UP
[00068] -> GOLDDR  : DOWN
[00070] -> GOLDDR  : DOWN
[00072] -> GOLDDR  : DOWN
[00074] -> GOLDDR  : UP
[00074] -> GOLD  : EXPECTING..
[00074] -> SUCCESS!
[00074]
[00074] ---------
[00074] TAKE DR DOWN - up/down - expect GOLD IP
[00074] ---------
[00074] -> SCALED GOLD TO 2 replicas
[00075] -> SCALED GOLDDR TO 0 replicas
[00075] -> GOLD  : UP
[00076] -> GOLDDR  : DOWN
[00076] -> GOLD  : EXPECTING..
[00076] -> SUCCESS!
[00076]
[00076] ---------
[00076] DR THEN RECOVERY
[00076] ---------
[00076] -> SCALED GOLD TO 0 replicas
[00077] -> SCALED GOLDDR TO 2 replicas
[00078] -> GOLD  : DOWN
[00079] -> GOLDDR  : DOWN
[00080] -> GOLDDR  : DOWN
[00081] -> GOLDDR  : DOWN
[00082] -> GOLDDR  : DOWN
[00084] -> GOLDDR  : DOWN
[00085] -> GOLDDR  : DOWN
[00087] -> GOLDDR  : DOWN
[00089] -> GOLDDR  : DOWN
[00091] -> GOLDDR  : DOWN
[00093] -> GOLDDR  : DOWN
[00094] -> GOLDDR  : UP
[00094] -> GOLDDR  : EXPECTING..
[00094] -> FAILED - NOT WHAT IS EXPECTED
[00096] -> GOLDDR  : EXPECTING..
[00096] -> SUCCESS!
[00097] -> SCALED GOLD TO 2 replicas
[00097] -> GOLD  : EXPECTING..
[00097] -> SUCCESS!
```
