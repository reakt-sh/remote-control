# Required packages: iot

################################ Configuration ################################
# Name of an existing MQTT broker that should be used for publishing
# broker1 can be either "addix" or "msgaarden"
:local broker1 "cau"
#:local broker2 "cau-backup"
:local lIdentity [/system/identity/get name];
:local lTime [/system clock get time];
:local lDate [/system clock get date];
:local lRouterboardModel [/system routerboard get value-name=model]
:local lCurrentFirmware [/system routerboard get value-name=current-firmware]
:local lUpgradeFirmware [/system routerboard get value-name=upgrade-firmware]

# MQTT topic where the message should be published
:local topic "rtsys/wan/$lIdentity"

:local lLatitude;
:local lLongitude;
:local lAltitude;
:local lSpeed;
:local lBearing; 
:local lSatellites
/system gps monitor once do={
  :set lLatitude $latitude;
  :set lLongitude $longitude;
  :set lAltitude $altitude;
  :set lSpeed $speed;
  :set lBearing $"true-bearing";
  :set lSatellites $satellites;
};

:local lModel
:local lRevision
:local lCurrentOperator
:local lCurrentCellid;
:local lEnbId;
:local lSectorId;
:local lPhyCellId;
:local lDataClass;
:local lPrimaryBand;
:local lcaBand;
:local lulcaBand;
:local lDlModulation;
:local lCqi;
:local lRi;
:local lMcs;
:local lRssi;
:local lRsrp;
:local lRsrq;
:local lSinr;
:local lNrDlModulation;
:local lNrRsrp;
:local lNrRsrq;
:local lNrSinr;

/interface lte monitor lte1 once do={
  :set lModel $model;
  :set lRevision $revision;
  :set lCurrentOperator $"current-operator";
  :set lCurrentCellid $"current-cellid";
  :set lEnbId $"enb-id";
  :set lSectorId $"sector-id";
  :set lPhyCellId $"phy-cellid";
  :set lDataClass $"data-class";
  :set lPrimaryBand $"primary-band";
  :set lcaBand $"ca-band";
  :set lulcaBand $"ul-ca-band";
  :set lDlModulation $"dl-modulation";
  :set lCqi $cqi;
  :set lRi $ri;
  :set lMcs $mcs;
  :set lRssi $rssi;
  :set lRsrp $rsrp;
  :set lRsrq $rsrq;
  :set lSinr $sinr;
  :set lNrDlModulation $"nr-dl-modulation";
  :set lNrRsrp $"nr-rsrp";
  :set lNrRsrq $"nr-rsrq";
  :set lNrSinr $"nr-sinr";
}

:local lrxpacketspersecond;
:local lrxbitspersecond;
:local lfprxpacketspersecond;
:local lfprxbitspersecond;
:local lrxdropspersecond;
:local lrxerrorspersecond;
:local ltxpacketspersecond;
:local ltxbitspersecond;
:local lfptxpacketspersecond;
:local lfptxbitspersecond;
:local ltxdropspersecond;
:local ltxqueuedropspersecond;
:local ltxerrorspersecond;

/interface/monitor-traffic lte1 once do={
  :set lrxpacketspersecond $"rx-packets-per-second";
  :set lrxbitspersecond $"rx-bits-per-second";
  :set lfprxpacketspersecond $"fp-rx-packets-per-second";
  :set lfprxbitspersecond $"fp-rx-bits-per-second";
  :set lrxdropspersecond $"rx-drops-per-second";
  :set lrxerrorspersecond $"rx-errors-per-second";
  :set ltxpacketspersecond $"tx-packets-per-second";
  :set ltxbitspersecond $"tx-bits-per-second";
  :set lfptxpacketspersecond $"fp-tx-packets-per-second";
  :set lfptxbitspersecond $"fp-tx-bits-per-second";
  :set ltxdropspersecond $"tx-drops-per-second";
  :set ltxqueuedropspersecond $"tx-queue-drops-per-second";
  :set ltxerrorspersecond $"tx-errors-per-second";
};

:local lcaBand3;
:set lcaBand3 "";
:local j;
:foreach j in $lcaBand do={ 
  if ($lcaBand3 = "") do={
    :set lcaBand3 ($j)
  } else {
    :set lcaBand3 ($lcaBand3 . "\",\"" . $j); 
  }
};

:local lulcaBand3;
:set lulcaBand3 "";
:local k;
:foreach k in $lulcaBand do={ 
  if ($lulcaBand3 = "") do={
    :set lulcaBand3 ($k)
  } else {
    :set lulcaBand3 ($lulcaBand3 . "\",\"" . $k); 
  }
};

:local pubMessage \
  "{
    \"identity\": \"$lIdentity\",
    \"router_time\": \"$lTime\",
    \"router_date\": \"$lDate\",
    \"RouterboardModel\": \"$lRouterboardModel\",
    \"CurrentFirmware\": \"$lCurrentFirmware\",
    \"UpgradeFirmware\": \"$lUpgradeFirmware\",
  \
  \"gps\":{
      \"lat\":\"$lLatitude\",
      \"lon\":\"$lLongitude\",
      \"altitude\":\"$lAltitude\",
      \"speed\":\"$lSpeed\",
      \"heading\":\"$lBearing\",
      \"satellites\":\"$lSatellites\"},
  \
  \"lte\": {
      \"lModel\":\"$lModel\",
      \"lRevision\":\"$lRevision\",
      \"lCurrentOperator\":\"$lCurrentOperator\",
      \"lCurrentCellid\":\"$lCurrentCellid\",
      \"lEnbId\":\"$lEnbId\",
      \"lSectorId\":\"$lSectorId\",
      \"lPhyCellId\":\"$lPhyCellId\",
      \"lDataClass\":\"$lDataClass\",
      \"lPrimaryBand\":\"$lPrimaryBand\",
      \"lcaBand\":[\"$lcaBand3\"],
      \"lulcaBand\":[\"$lulcaBand3\"],
      \"lDlModulation\":\"$lDlModulation\",
      \"lCqi\":\"$lCqi\",
      \"lRi\":\"$lRi\",
      \"lMcs\":\"$lMcs\",
      \"lRssi\":\"$lRssi\",
      \"lRsrp\":\"$lRsrp\",
      \"lRsrq\":\"$lRsrq\",
      \"lSinr\":\"$lSinr\",
      \"lNrDlModulation\":\"$lNrDlModulation\",
      \"lNrRsrp\":\"$lNrRsrp\",
      \"lNrRsrq\":\"$lNrRsrq\",
      \"lNrSinr\":\"$lNrSinr\",
      \"lrxpacketspersecond\":\"$lrxpacketspersecond\",
      \"lrxbitspersecond\":\"$lrxbitspersecond\",
      \"lfprxpacketspersecond\":\"$lfprxpacketspersecond\",
      \"lfprxbitspersecond\":\"$lfprxbitspersecond\",
      \"lrxdropspersecond\":\"$lrxdropspersecond\",
      \"lrxerrorspersecond\":\"$lrxerrorspersecond\",
      \"ltxpacketspersecond\":\"$ltxpacketspersecond\",
      \"ltxbitspersecond\":\"$ltxbitspersecond\",
      \"lfptxpacketspersecond\":\"$lfptxpacketspersecond\",
      \"lfptxbitspersecond\":\"$lfptxbitspersecond\",
      \"ltxdropspersecond\":\"$ltxdropspersecond\",
      \"ltxqueuedropspersecond\":\"$ltxqueuedropspersecond\",
      \"ltxerrorspersecond\":\"$ltxerrorspersecond\"
      }}"

:put ("[*] Total message size: $[:len $pubMessage] bytes")
:put ("[*] Sending message to MQTT broker...")
/iot mqtt publish broker=$broker1 topic=$topic message=$pubMessage
#/iot mqtt publish broker=$broker2 topic=$topic message=$pubMessage
:put ("[*] Sending message to MQTT broker...")