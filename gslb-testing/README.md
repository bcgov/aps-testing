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

# repeat <attempts> <wait> <cmd>
function repeat {
  echo "--"
  attempts=$1
  fails=attempts
  n=0
  until [ "$n" -ge $attempts ]
  do
    "${@:3}" && fails=$((fails-1))
    n=$((n+1))
    sleep $2
  done
  echo "REPEATS ($fails of $attempts) COMMAND ${@:3}"
  if [ $fails -gt 0 ]
  then
    echo "REPEATS > TOO MANY FAILURES"
  else
    echo "REPEATS > NICE! ALL ATTEMPTS WERE OK!"
  fi
  echo "--"
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
    echo "-> GOLD[$GOLD] $MSG"
  elif [ "$EXP_IP" = "$GOLDDR" ]
  then
    echo "-> GOLDDR[$GOLDDR] $MSG"
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
  echo "-> FAILED - NOT WHAT IS EXPECTED [DIG = $IP]"
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
  try 40 2 expect_routing_to "$BOTH"
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
  try 30 2 expect_routing_to "$GOLDDR"
  scale_gold 2
  try 20 1 is_up $GOLD
  repeat 30 .5 expect_routing_to "$GOLD"
  repeat 30 .5 expect_routing_to "$GOLD"
  repeat 30 .5 expect_routing_to "$GOLD"
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
[00001] -> SCALED GOLDDR TO 0 replicas
[00002] -> GOLD[142.34.229.4]  : DOWN
[00002] -> GOLDDR[142.34.64.4]  : DOWN
[00002]
[00002] ---------
[00002] HAPPY PATH - up/up - expect GOLD IP
[00002] ---------
[00003] -> SCALED GOLD TO 2 replicas
[00003] -> SCALED GOLDDR TO 2 replicas
[00004] -> GOLD[142.34.229.4]  : DOWN
[00006] -> GOLD[142.34.229.4]  : DOWN
[00008] -> GOLD[142.34.229.4]  : DOWN
[00009] -> GOLD[142.34.229.4]  : DOWN
[00010] -> GOLD[142.34.229.4]  : DOWN
[00012] -> GOLD[142.34.229.4]  : DOWN
[00013] -> GOLD[142.34.229.4]  : UP
[00014] -> GOLDDR[142.34.64.4]  : DOWN
[00016] -> GOLDDR[142.34.64.4]  : DOWN
[00018] -> GOLDDR[142.34.64.4]  : DOWN
[00020] -> GOLDDR[142.34.64.4]  : DOWN
[00022] -> GOLDDR[142.34.64.4]  : UP
[00022] -> GOLD[142.34.229.4]  : EXPECTING..
[00022] -> SUCCESS!
[00022]
[00022] ---------
[00022] SWITCH TO DR - down/up - expect GOLDDR IP
[00022] ---------
[00023] -> SCALED GOLD TO 0 replicas
[00024] -> SCALED GOLDDR TO 2 replicas
[00025] -> GOLD[142.34.229.4]  : DOWN
[00025] -> GOLDDR[142.34.64.4]  : UP
[00025] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00025] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00027] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00027] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00029] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00029] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00031] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00031] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00037] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00037] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00040] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00040] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00042] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00042] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00044] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00045] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00047] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00047] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00049] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00049] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00051] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00051] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00053] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00053] -> SUCCESS!
[00053]
[00053] ---------
[00053] TOTAL OUTAGE - down/down - expect BOTH IP
[00053] ---------
[00054] -> SCALED GOLD TO 0 replicas
[00054] -> SCALED GOLDDR TO 0 replicas
[00054] -> GOLD[142.34.229.4]  : DOWN
[00054] -> GOLDDR[142.34.64.4]  : DOWN
[00054] -> BOTH IPS  : EXPECTING..
[00054] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00057] -> BOTH IPS  : EXPECTING..
[00057] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00059] -> BOTH IPS  : EXPECTING..
[00059] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00061] -> BOTH IPS  : EXPECTING..
[00061] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00063] -> BOTH IPS  : EXPECTING..
[00063] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00065] -> BOTH IPS  : EXPECTING..
[00065] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00067] -> BOTH IPS  : EXPECTING..
[00067] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00069] -> BOTH IPS  : EXPECTING..
[00069] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00071] -> BOTH IPS  : EXPECTING..
[00071] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00073] -> BOTH IPS  : EXPECTING..
[00073] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00075] -> BOTH IPS  : EXPECTING..
[00075] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00077] -> BOTH IPS  : EXPECTING..
[00077] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00079] -> BOTH IPS  : EXPECTING..
[00079] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00081] -> BOTH IPS  : EXPECTING..
[00081] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00083] -> BOTH IPS  : EXPECTING..
[00083] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00085] -> BOTH IPS  : EXPECTING..
[00085] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00088] -> BOTH IPS  : EXPECTING..
[00088] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4
142.34.229.4]
[00090] -> BOTH IPS  : EXPECTING..
[00090] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4
142.34.229.4]
[00092] -> BOTH IPS  : EXPECTING..
[00092] -> SUCCESS!
[00092]
[00092] ---------
[00092] SWITCH TO PRIMARY - up/up - expect GOLD IP
[00092] ---------
[00092] -> SCALED GOLD TO 2 replicas
[00093] -> SCALED GOLDDR TO 2 replicas
[00093] -> GOLD[142.34.229.4]  : DOWN
[00094] -> GOLD[142.34.229.4]  : DOWN
[00096] -> GOLD[142.34.229.4]  : DOWN
[00097] -> GOLD[142.34.229.4]  : DOWN
[00098] -> GOLD[142.34.229.4]  : DOWN
[00100] -> GOLD[142.34.229.4]  : DOWN
[00102] -> GOLD[142.34.229.4]  : DOWN
[00103] -> GOLD[142.34.229.4]  : UP
[00104] -> GOLDDR[142.34.64.4]  : DOWN
[00106] -> GOLDDR[142.34.64.4]  : DOWN
[00108] -> GOLDDR[142.34.64.4]  : DOWN
[00110] -> GOLDDR[142.34.64.4]  : UP
[00110] -> GOLD[142.34.229.4]  : EXPECTING..
[00110] -> SUCCESS!
[00110]
[00110] ---------
[00110] TAKE DR DOWN - up/down - expect GOLD IP
[00110] ---------
[00111] -> SCALED GOLD TO 2 replicas
[00112] -> SCALED GOLDDR TO 0 replicas
[00112] -> GOLD[142.34.229.4]  : UP
[00112] -> GOLDDR[142.34.64.4]  : DOWN
[00112] -> GOLD[142.34.229.4]  : EXPECTING..
[00112] -> SUCCESS!
[00112]
[00112] ---------
[00112] DR THEN RECOVERY
[00112] ---------
[00113] -> SCALED GOLD TO 0 replicas
[00114] -> SCALED GOLDDR TO 2 replicas
[00115] -> GOLD[142.34.229.4]  : DOWN
[00115] -> GOLDDR[142.34.64.4]  : DOWN
[00116] -> GOLDDR[142.34.64.4]  : DOWN
[00117] -> GOLDDR[142.34.64.4]  : DOWN
[00118] -> GOLDDR[142.34.64.4]  : DOWN
[00119] -> GOLDDR[142.34.64.4]  : DOWN
[00121] -> GOLDDR[142.34.64.4]  : DOWN
[00122] -> GOLDDR[142.34.64.4]  : DOWN
[00124] -> GOLDDR[142.34.64.4]  : DOWN
[00126] -> GOLDDR[142.34.64.4]  : DOWN
[00128] -> GOLDDR[142.34.64.4]  : DOWN
[00130] -> GOLDDR[142.34.64.4]  : DOWN
[00131] -> GOLDDR[142.34.64.4]  : UP
[00131] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00131] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.229.4]
[00133] -> GOLDDR[142.34.64.4]  : EXPECTING..
[00133] -> SUCCESS!
[00134] -> SCALED GOLD TO 2 replicas
[00134] -> GOLD[142.34.229.4]  : DOWN
[00135] -> GOLD[142.34.229.4]  : DOWN
[00137] -> GOLD[142.34.229.4]  : DOWN
[00138] -> GOLD[142.34.229.4]  : DOWN
[00139] -> GOLD[142.34.229.4]  : DOWN
[00140] -> GOLD[142.34.229.4]  : DOWN
[00142] -> GOLD[142.34.229.4]  : DOWN
[00144] -> GOLD[142.34.229.4]  : DOWN
[00145] -> GOLD[142.34.229.4]  : UP
[00145] --
[00145] -> GOLD[142.34.229.4]  : EXPECTING..
[00145] -> SUCCESS!
[00146] -> GOLD[142.34.229.4]  : EXPECTING..
[00146] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00146] -> GOLD[142.34.229.4]  : EXPECTING..
[00146] -> SUCCESS!
[00147] -> GOLD[142.34.229.4]  : EXPECTING..
[00147] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00148] -> GOLD[142.34.229.4]  : EXPECTING..
[00148] -> SUCCESS!
[00148] -> GOLD[142.34.229.4]  : EXPECTING..
[00148] -> SUCCESS!
[00149] -> GOLD[142.34.229.4]  : EXPECTING..
[00149] -> SUCCESS!
[00149] -> GOLD[142.34.229.4]  : EXPECTING..
[00149] -> SUCCESS!
[00150] -> GOLD[142.34.229.4]  : EXPECTING..
[00150] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00150] -> GOLD[142.34.229.4]  : EXPECTING..
[00150] -> SUCCESS!
[00151] -> GOLD[142.34.229.4]  : EXPECTING..
[00151] -> SUCCESS!
[00151] -> GOLD[142.34.229.4]  : EXPECTING..
[00151] -> SUCCESS!
[00152] -> GOLD[142.34.229.4]  : EXPECTING..
[00152] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00152] -> GOLD[142.34.229.4]  : EXPECTING..
[00152] -> SUCCESS!
[00153] -> GOLD[142.34.229.4]  : EXPECTING..
[00153] -> SUCCESS!
[00154] -> GOLD[142.34.229.4]  : EXPECTING..
[00154] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00154] -> GOLD[142.34.229.4]  : EXPECTING..
[00154] -> SUCCESS!
[00155] -> GOLD[142.34.229.4]  : EXPECTING..
[00155] -> SUCCESS!
[00155] -> GOLD[142.34.229.4]  : EXPECTING..
[00155] -> SUCCESS!
[00156] -> GOLD[142.34.229.4]  : EXPECTING..
[00156] -> SUCCESS!
[00156] -> GOLD[142.34.229.4]  : EXPECTING..
[00156] -> SUCCESS!
[00157] -> GOLD[142.34.229.4]  : EXPECTING..
[00157] -> SUCCESS!
[00157] -> GOLD[142.34.229.4]  : EXPECTING..
[00157] -> SUCCESS!
[00158] -> GOLD[142.34.229.4]  : EXPECTING..
[00158] -> SUCCESS!
[00159] -> GOLD[142.34.229.4]  : EXPECTING..
[00159] -> FAILED - NOT WHAT IS EXPECTED [DIG = 142.34.64.4]
[00159] -> GOLD[142.34.229.4]  : EXPECTING..
[00159] -> SUCCESS!
[00160] -> GOLD[142.34.229.4]  : EXPECTING..
[00160] -> SUCCESS!
[00160] -> GOLD[142.34.229.4]  : EXPECTING..
[00160] -> SUCCESS!
[00161] -> GOLD[142.34.229.4]  : EXPECTING..
[00161] -> SUCCESS!
[00161] -> GOLD[142.34.229.4]  : EXPECTING..
[00161] -> SUCCESS!
[00162] REPEATS (6 of 30) COMMAND expect_routing_to
[00162] REPEATS > TOO MANY FAILURES
[00162] --
[00162] --
[00162] -> GOLD[142.34.229.4]  : EXPECTING..
[00162] -> SUCCESS!
[00162] -> GOLD[142.34.229.4]  : EXPECTING..
[00162] -> SUCCESS!
[00163] -> GOLD[142.34.229.4]  : EXPECTING..
[00163] -> SUCCESS!
[00163] -> GOLD[142.34.229.4]  : EXPECTING..
[00163] -> SUCCESS!
[00164] -> GOLD[142.34.229.4]  : EXPECTING..
[00164] -> SUCCESS!
[00165] -> GOLD[142.34.229.4]  : EXPECTING..
[00165] -> SUCCESS!
[00165] -> GOLD[142.34.229.4]  : EXPECTING..
[00165] -> SUCCESS!
[00166] -> GOLD[142.34.229.4]  : EXPECTING..
[00166] -> SUCCESS!
[00166] -> GOLD[142.34.229.4]  : EXPECTING..
[00166] -> SUCCESS!
[00167] -> GOLD[142.34.229.4]  : EXPECTING..
[00167] -> SUCCESS!
[00167] -> GOLD[142.34.229.4]  : EXPECTING..
[00167] -> SUCCESS!
[00168] -> GOLD[142.34.229.4]  : EXPECTING..
[00168] -> SUCCESS!
[00168] -> GOLD[142.34.229.4]  : EXPECTING..
[00168] -> SUCCESS!
[00169] -> GOLD[142.34.229.4]  : EXPECTING..
[00169] -> SUCCESS!
[00170] -> GOLD[142.34.229.4]  : EXPECTING..
[00170] -> SUCCESS!
[00170] -> GOLD[142.34.229.4]  : EXPECTING..
[00170] -> SUCCESS!
[00171] -> GOLD[142.34.229.4]  : EXPECTING..
[00171] -> SUCCESS!
[00171] -> GOLD[142.34.229.4]  : EXPECTING..
[00171] -> SUCCESS!
[00172] -> GOLD[142.34.229.4]  : EXPECTING..
[00172] -> SUCCESS!
[00172] -> GOLD[142.34.229.4]  : EXPECTING..
[00172] -> SUCCESS!
[00173] -> GOLD[142.34.229.4]  : EXPECTING..
[00173] -> SUCCESS!
[00173] -> GOLD[142.34.229.4]  : EXPECTING..
[00173] -> SUCCESS!
[00174] -> GOLD[142.34.229.4]  : EXPECTING..
[00174] -> SUCCESS!
[00174] -> GOLD[142.34.229.4]  : EXPECTING..
[00174] -> SUCCESS!
[00175] -> GOLD[142.34.229.4]  : EXPECTING..
[00175] -> SUCCESS!
[00176] -> GOLD[142.34.229.4]  : EXPECTING..
[00176] -> SUCCESS!
[00176] -> GOLD[142.34.229.4]  : EXPECTING..
[00176] -> SUCCESS!
[00177] -> GOLD[142.34.229.4]  : EXPECTING..
[00177] -> SUCCESS!
[00177] -> GOLD[142.34.229.4]  : EXPECTING..
[00177] -> SUCCESS!
[00178] -> GOLD[142.34.229.4]  : EXPECTING..
[00178] -> SUCCESS!
[00178] REPEATS (0 of 30) COMMAND expect_routing_to
[00178] REPEATS > NICE! ALL ATTEMPTS WERE OK!
[00178] --
[00178] --
[00178] -> GOLD[142.34.229.4]  : EXPECTING..
[00178] -> SUCCESS!
[00179] -> GOLD[142.34.229.4]  : EXPECTING..
[00179] -> SUCCESS!
[00179] -> GOLD[142.34.229.4]  : EXPECTING..
[00179] -> SUCCESS!
[00180] -> GOLD[142.34.229.4]  : EXPECTING..
[00180] -> SUCCESS!
[00181] -> GOLD[142.34.229.4]  : EXPECTING..
[00181] -> SUCCESS!
[00181] -> GOLD[142.34.229.4]  : EXPECTING..
[00181] -> SUCCESS!
[00182] -> GOLD[142.34.229.4]  : EXPECTING..
[00182] -> SUCCESS!
[00182] -> GOLD[142.34.229.4]  : EXPECTING..
[00182] -> SUCCESS!
[00183] -> GOLD[142.34.229.4]  : EXPECTING..
[00183] -> SUCCESS!
[00183] -> GOLD[142.34.229.4]  : EXPECTING..
[00183] -> SUCCESS!
[00184] -> GOLD[142.34.229.4]  : EXPECTING..
[00184] -> SUCCESS!
[00184] -> GOLD[142.34.229.4]  : EXPECTING..
[00184] -> SUCCESS!
[00185] -> GOLD[142.34.229.4]  : EXPECTING..
[00185] -> SUCCESS!
[00185] -> GOLD[142.34.229.4]  : EXPECTING..
[00185] -> SUCCESS!
[00186] -> GOLD[142.34.229.4]  : EXPECTING..
[00186] -> SUCCESS!
[00186] -> GOLD[142.34.229.4]  : EXPECTING..
[00186] -> SUCCESS!
[00187] -> GOLD[142.34.229.4]  : EXPECTING..
[00187] -> SUCCESS!
[00188] -> GOLD[142.34.229.4]  : EXPECTING..
[00188] -> SUCCESS!
[00188] -> GOLD[142.34.229.4]  : EXPECTING..
[00188] -> SUCCESS!
[00189] -> GOLD[142.34.229.4]  : EXPECTING..
[00189] -> SUCCESS!
[00189] -> GOLD[142.34.229.4]  : EXPECTING..
[00189] -> SUCCESS!
[00190] -> GOLD[142.34.229.4]  : EXPECTING..
[00190] -> SUCCESS!
[00190] -> GOLD[142.34.229.4]  : EXPECTING..
[00190] -> SUCCESS!
[00191] -> GOLD[142.34.229.4]  : EXPECTING..
[00191] -> SUCCESS!
[00191] -> GOLD[142.34.229.4]  : EXPECTING..
[00191] -> SUCCESS!
[00192] -> GOLD[142.34.229.4]  : EXPECTING..
[00192] -> SUCCESS!
[00192] -> GOLD[142.34.229.4]  : EXPECTING..
[00192] -> SUCCESS!
[00193] -> GOLD[142.34.229.4]  : EXPECTING..
[00193] -> SUCCESS!
[00194] -> GOLD[142.34.229.4]  : EXPECTING..
[00194] -> SUCCESS!
[00194] -> GOLD[142.34.229.4]  : EXPECTING..
[00194] -> SUCCESS!
[00195] REPEATS (0 of 30) COMMAND expect_routing_to
[00195] REPEATS > NICE! ALL ATTEMPTS WERE OK!
[00195] --
```
