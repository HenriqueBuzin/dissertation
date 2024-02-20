// EXPORT SoapCall01 := 'todo';
IMPORT $,Std;
//
EXPORT SoapCall01(INTEGER RecvTime) := FUNCTION
//
  NumSysTime  := (INTEGER) $.modTimes.SysTime;
  SysTimeHHMM := (STRING) $.modTimes.SysTime[1..2] + ':' + $.modTimes.SysTime[3..4];
//
  CalcTime    := $.modTimes.NumRecTime - $.modTimes.NumSysTime;
  AddNum(INTEGER RecvTime=0) := RecvTime + 782;     // [0] for NumSysTime "OR" CalcTime value
  GetTime := AddNum(RecvTime);
//
  OutRec1 := RECORDOF($.STD_Consumption.File) AND NOT [RecId];   // short mode
  RoxieIP := 'http://127.0.0.1:8002/WsEcl/soap/query/roxie/fetch_consumption.1';
  svc     := 'fetch_consumption.1';
//
  InputRec1 := RECORD
    UNSIGNED8 Id_Value   := 0;
    STRING8   Time_Value := (STRING) GetTime;
    STRING10  Date_Value := '';
  END;
//
// 1 rec in, recordset out
  ManyRec1 := SOAPCALL(RoxieIP,svc,InputRec1,DATASET(OutRec1));
// OUTPUT(ManyRec1);
//
  RETURN SEQUENTIAL(OUTPUT(NumSysTime, NAMED('System_Time')),
                    OUTPUT(CalcTime, NAMED('Calculated_Time')),
                    OUTPUT(GetTime, NAMED('Get_Time')),
                    OUTPUT(SysTimeHHMM, NAMED('Formatted_Time')),
                    OUTPUT(ManyRec1,NAMED('SoapCall01'),EXTEND));
END;
//