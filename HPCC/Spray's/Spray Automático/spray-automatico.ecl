IMPORT Std;

ConsumptionDataLayout := RECORD
  UNSIGNED8 Id;
	STRING20  Address;
  STRING20  Street;
  STRING10  Date;
  STRING8   Time;
  REAL8     Consumption;
END;

LZ_IP := '192.168.56.101';
LZ_Dir := '/var/lib/HPCCSystems/mydropzone/';
LZ_Path := '//' + LZ_IP + LZ_Dir;
RawFile := 'consumption.csv';
LogicalFileName := '~UFSC::XYZ::FOG::Consumption';

// STD.File.SprayDelimited(LZ_IP,
                        // LZ_Path + RawFile,
                        // ,,,, 'mythor',
                        // LogicalFileName, -1, , , 
												// TRUE, FALSE);

ConsumptionData := DATASET(LogicalFileName, ConsumptionDataLayout, CSV(SEPARATOR(','), HEADING(1)));

OUTPUT(ConsumptionData, NAMED('DataConsumption'));

// OUTPUT(ConsumptionData, NAMED('DataConsumption'), ALL);
