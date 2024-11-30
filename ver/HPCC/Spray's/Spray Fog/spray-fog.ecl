IMPORT Std;

ConsumptionDataLayout := RECORD
  UNSIGNED8 ID;
  STRING10  Date;
  STRING8   Time;
  REAL8     Consumption;
END;

ConsumptionData := DATASET('~ufsc::xyz::fog::consumption_per_minute::results.csv', ConsumptionDataLayout, CSV(SEPARATOR(','), HEADING(1)));

OUTPUT(ConsumptionData, NAMED('DataConsumption'));

AddressDataLayout := RECORD
  UNSIGNED8 Id;
  STRING20  Address;
END;

AddressData := DATASET([
	{1, '123 Fake Street'},
	{2, '456 Elm Street'},
	{3, '789 Maple Avenue'},
	{4, '444 Pine Street'},
	{5, '555 Oak Street'},
	{6, '666 Cedar Street'},
	{7, '777 Birch Street'},
	{8, '888 Cherry Street'},
	{9, '999 Walnut Street'},
	{0, '1110 Willow Street'},
	{11, '1221 Poplar Street'},
	{12, '1332 Hawthorn Street'},
	{13, '1443 Chestnut Street'},
	{14, '1554 Sycamore Street'},
	{15, '1665 Aspen Street'},
	{16, '1776 Spruce Street'},
	{17, '1887 Beech Street'},
	{18, '1998 Hemlock Street'},
	{19, '2109 Holly Street'},
	{20, '2220 Juniper Street'}],AddressDataLayout);

OUTPUT(AddressData, NAMED('DataAddress'));

OutputLayout := RECORD
  UNSIGNED8 Id;
  STRING20  Address;
  STRING10  Date;
  STRING8   Time;
  REAL8     Consumption;
END;

outputData := JOIN(ConsumptionData, AddressData, LEFT.id = RIGHT.Id, TRANSFORM(OutputLayout,
    SELF.Id          := LEFT.Id,
    SELF.Address     := RIGHT.Address,
    SELF.Date        := LEFT.Date,
    SELF.Time        := LEFT.Time,
    SELF.Consumption := LEFT.Consumption));

// OUTPUT(OutputData, NAMED('DataConsumptionAddressTime'));

OUTPUT(OutputData,, '~UFSC::XYZ::FOG::Consumption',CSV, OVERWRITE, NAMED('DataConsumptionAddressTime'));
