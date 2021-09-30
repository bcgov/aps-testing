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
  MSG=$2
  IP="$1"
  if [ "$IP" = "$GOLD" ]
  then
    echo "-> GOLD $MSG"
  elif [ "$IP" = "$GOLDDR" ]
  then
    echo "-> GOLDDR $MSG"
  elif [ "$IP" = "$GOLD\n$GOLDDR" ]
  then
    echo "-> BOTH IPS $MSG"
  elif [ "$IP" = "$GOLDDR\n$GOLD" ]
  then
    echo "-> BOTH IPS $MSG"
  else
    echo "-> UNEXPECTED DIG ($IP) $MSG"
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

baseline_all_down
test_happy_path
test_switch_to_dr
test_total_outage
test_switch_to_primary
test_dr_down

' | bash

```

## Output for APS

```
[00000] ---------
[00000] BASELINE ALL DOWN - down/down
[00000] ---------
[00001] -> SCALED GOLD TO 0 replicas
[00001] -> SCALED GOLDDR TO 0 replicas
[00002] -> GOLD  : DOWN
[00003] -> GOLDDR  : DOWN
[00003] ---------
[00003] HAPPY PATH - up/up - expect GOLD IP
[00003] ---------
[00004] -> SCALED GOLD TO 2 replicas
[00004] -> SCALED GOLDDR TO 2 replicas
[00005] -> GOLD  : DOWN
[00006] -> GOLD  : DOWN
[00007] -> GOLD  : DOWN
[00009] -> GOLD  : DOWN
[00010] -> GOLD  : DOWN
[00012] -> GOLD  : DOWN
[00014] -> GOLD  : DOWN
[00015] -> GOLD  : UP
[00016] -> GOLDDR  : DOWN
[00018] -> GOLDDR  : DOWN
[00020] -> GOLDDR  : DOWN
[00022] -> GOLDDR  : DOWN
[00023] -> GOLDDR  : UP
[00023] -> GOLD  : EXPECTING..
[00023] -> SUCCESS!
[00023] ---------
[00023] SWITCH TO DR - down/up - expect GOLDDR IP
[00023] ---------
[00024] -> SCALED GOLD TO 0 replicas
[00025] -> SCALED GOLDDR TO 2 replicas
[00026] -> GOLD  : DOWN
[00026] -> GOLDDR  : UP
[00026] -> GOLDDR  : EXPECTING..
[00026] -> SUCCESS!
[00026] ---------
[00026] TOTAL OUTAGE - down/down - expect BOTH IP
[00026] ---------
[00026] -> SCALED GOLD TO 0 replicas
[00027] -> SCALED GOLDDR TO 0 replicas
[00028] -> GOLD  : DOWN
[00028] -> GOLDDR  : DOWN
[00028] -> BOTH IPS  : EXPECTING..
[00028] -> SUCCESS!
[00028] ---------
[00028] SWITCH TO PRIMARY - up/up - expect GOLD IP
[00028] ---------
[00029] -> SCALED GOLD TO 2 replicas
[00029] -> SCALED GOLDDR TO 2 replicas
[00029] -> GOLD  : DOWN
[00030] -> GOLD  : DOWN
[00032] -> GOLD  : DOWN
[00033] -> GOLD  : DOWN
[00034] -> GOLD  : DOWN
[00036] -> GOLD  : DOWN
[00038] -> GOLD  : DOWN
[00039] -> GOLD  : UP
[00040] -> GOLDDR  : DOWN
[00043] -> GOLDDR  : DOWN
[00045] -> GOLDDR  : DOWN
[00046] -> GOLDDR  : UP
[00046] -> GOLD  : EXPECTING..
[00046] -> SUCCESS!
[00046] ---------
[00046] TAKE DR DOWN - up/down - expect GOLD IP
[00046] ---------
[00046] -> SCALED GOLD TO 2 replicas
[00047] -> SCALED GOLDDR TO 0 replicas
[00047] -> GOLD  : UP
[00047] -> GOLDDR  : DOWN
[00047] -> GOLD  : EXPECTING..
[00047] -> SUCCESS!
```
