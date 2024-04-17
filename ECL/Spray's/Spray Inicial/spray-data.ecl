IMPORT Std;

consumptionDataLayout := RECORD
  UNSIGNED id;
  STRING date;
  STRING time;
  STRING consumption;
END;

consumptionData := DATASET('~projeto::consumption_per_minute', consumptionDataLayout, CSV(HEADING(1), SEPARATOR([',','\t'])));

OUTPUT(consumptionData, NAMED('DataConsumption'));

addressDataLayout := RECORD
  UNSIGNED id;
  STRING address;
END;

addressData := DATASET([
  {1, '123 Fake Street'},
  {2, '456 Elm Street'},
  {3, '789 Maple Avenue'}
], addressDataLayout);

OUTPUT(addressData, NAMED('DataAddress'));

/*
outputLayout := RECORD
  UNSIGNED id;
  STRING address;
  STRING date;
  STRING time;
  REAL consumption;
END;

outputData := JOIN(consumptionData, addressData, LEFT.id = RIGHT.id,
  TRANSFORM(outputLayout,
    SELF.id := LEFT.id,
    SELF.address := RIGHT.address,
    SELF.date := LEFT.date,
    SELF.time := LEFT.time,
    SELF.consumption := LEFT.consumption));

OUTPUT(outputData, NAMED('DataConsumptionAddressTime'));
*/