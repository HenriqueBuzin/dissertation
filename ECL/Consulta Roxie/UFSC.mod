//Import:ecl:UFSC.BWR_BrowseData
// EXPORT BWR_BrowseData := 'todo';
IMPORT $;
//
$.modConsumption.File;
//
$.UID_Consumption;
$.STD_Consumption.File;
COUNT($.STD_Consumption.File);
//
//Import:ecl:UFSC.BWR_BuildIndex
// EXPORT BWR_BuildIndex := 'todo';
IMPORT $;
//
OUTPUT($.STD_Consumption.File,,'~UFSC::XYZ::FOG::OUT_Consumption', OVERWRITE);
//
BUILD($.IDX_Consumption.IDX_Time_Id_Date,OVERWRITE);
COUNT($.IDX_Consumption.IDX_Time_Id_Date);     //  95
//
//Import:ecl:UFSC.BWR_Event
// EXPORT BWR_Event := 'todo';
IMPORT $,Std;
//
// $.SoapCall01($.modTimes.PushTime) : WHEN($.ModEvents(1).Minutes,COUNT(95));   // 95 records 
$.SoapCall01($.modTimes.PushTime) : WHEN($.ModEvents(1).Minutes);
//
//Import:ecl:UFSC.BWR_Notify
// EXPORT BWR_Notify := 'todo';
IMPORT $,Std;
//
NOTIFY(EVENT('CRON','0-59/1 * * * *'));  // - Forced Action!!!
//
//Import:ecl:UFSC.BWR_Tests
// EXPORT BWR_Tests := 'todo';
IMPORT $,Std;
//
mydef := 'Hello World';
OUTPUT(MyDef);
mydef;
//
//  
// SysTime    := INTFORMAT((STD.Date.CurrentTime()/100) -300,4,1);
// NumSysTime := (INTEGER) SysTime;
// RecTime    := $.STD_Consumption.File[1].Time;
// NumRecTime := (INTEGER) RecTime;
// CalcTime   := NumRecTime - NumSysTime; CalcTime;
//
//Import:ecl:UFSC.Data1
// EXPORT Data1 := 'todo';
//
IMPORT Std;
//
ConsumptionDataLayout := RECORD
  UNSIGNED8 ID;
  STRING10  Date;
  STRING8   Time;
  REAL8     Consumption;
END;
//
ConsumptionData := DATASET([
	{1, '16/12/2006', '17:24:00', 0.07027},
	{1, '16/12/2006', '17:25:00', 0.08933},
	{1, '16/12/2006', '17:26:00', 0.08957},
	{1, '16/12/2006', '17:27:00', 0.08980},
	{1, '16/12/2006', '17:28:00', 0.06110},
	{2, '16/12/2006', '17:29:00', 0.05867},
	{2, '16/12/2006', '17:30:00', 0.06170},
	{2, '16/12/2006', '17:31:00', 0.06167},
	{2, '16/12/2006', '17:32:00', 0.06113},
	{2, '16/12/2006', '17:33:00', 0.06103},
	{3, '16/12/2006', '17:34:00', 0.07413},
	{3, '16/12/2006', '17:35:00', 0.09020},
	{3, '16/12/2006', '17:36:00', 0.08707},
	{3, '16/12/2006', '17:37:00', 0.08780},
	{3, '16/12/2006', '17:38:00', 0.06757},
	{4, '16/12/2006', '17:39:00', 0.05640},
	{4, '16/12/2006', '17:40:00', 0.05450},
	{4, '16/12/2006', '17:41:00', 0.05717},
	{4, '16/12/2006', '17:42:00', 0.05443},
	{4, '16/12/2006', '17:43:00', 0.06213},
	{5, '16/12/2006', '17:44:00', 0.09823},
	{5, '16/12/2006', '17:45:00', 0.12843},
	{5, '16/12/2006', '17:46:00', 0.11710},
	{5, '16/12/2006', '17:47:00', 0.08623},
	{5, '16/12/2006', '17:48:00', 0.07457},
	{6, '16/12/2006', '17:49:00', 0.05413},
	{6, '16/12/2006', '17:50:00', 0.05393},
	{6, '16/12/2006', '17:51:00', 0.05380},
	{6, '16/12/2006', '17:52:00', 0.05430},
	{6, '16/12/2006', '17:53:00', 0.05297},
	{7, '16/12/2006', '17:54:00', 0.04533},
	{7, '16/12/2006', '17:55:00', 0.06263},
	{7, '16/12/2006', '17:56:00', 0.07237},
	{7, '16/12/2006', '17:57:00', 0.07520},
	{7, '16/12/2006', '17:58:00', 0.06763},
	{8, '16/12/2006', '17:59:00', 0.04120},
	{8, '16/12/2006', '18:00:00', 0.04650},
	{8, '16/12/2006', '18:01:00', 0.04373},
	{8, '16/12/2006', '18:02:00', 0.04620},
	{8, '16/12/2006', '18:03:00', 0.06233},
	{9, '16/12/2006', '18:04:00', 0.08213},
	{9, '16/12/2006', '18:05:00', 0.10087},
	{9, '16/12/2006', '18:06:00', 0.11253},
	{9, '16/12/2006', '18:07:00', 0.10790},
	{9, '16/12/2006', '18:08:00', 0.10513},
	{10, '16/12/2006', '18:09:00', 0.07440},
	{10, '16/12/2006', '18:10:00', 0.05660},
	{10, '16/12/2006', '18:11:00', 0.05150},
	{10, '16/12/2006', '18:12:00', 0.06217},
	{10, '16/12/2006', '18:13:00', 0.03847},
	{11, '16/12/2006', '18:14:00', 0.03980},
	{11, '16/12/2006', '18:15:00', 0.07663},
	{11, '16/12/2006', '18:16:00', 0.07540},
	{11, '16/12/2006', '18:17:00', 0.07003},
	{11, '16/12/2006', '18:18:00', 0.07453},
	{12, '16/12/2006', '18:19:00', 0.04753},
	{12, '16/12/2006', '18:20:00', 0.04880},
	{12, '16/12/2006', '18:21:00', 0.04900},
	{12, '16/12/2006', '18:22:00', 0.04890},
	{12, '16/12/2006', '18:23:00', 0.04877},
	{13, '16/12/2006', '18:24:00', 0.05753},
	{13, '16/12/2006', '18:25:00', 0.08117},
	{13, '16/12/2006', '18:26:00', 0.08113},
	{13, '16/12/2006', '18:27:00', 0.08110},
	{13, '16/12/2006', '18:28:00', 0.05293},
	{14, '16/12/2006', '18:29:00', 0.04867},
	{14, '16/12/2006', '18:30:00', 0.04883},
	{14, '16/12/2006', '18:31:00', 0.04853},
	{14, '16/12/2006', '18:32:00', 0.04347},
	{14, '16/12/2006', '18:33:00', 0.04523},
	{15, '16/12/2006', '18:34:00', 0.05897},
	{15, '16/12/2006', '18:35:00', 0.10120},
	{15, '16/12/2006', '18:36:00', 0.07560},
	{15, '16/12/2006', '18:37:00', 0.07347},
	{15, '16/12/2006', '18:38:00', 0.04853},
	{16, '16/12/2006', '18:39:00', 0.03877},
	{16, '16/12/2006', '18:40:00', 0.03773},
	{16, '16/12/2006', '18:41:00', 0.03783},
	{16, '16/12/2006', '18:42:00', 0.03763},
	{16, '16/12/2006', '18:43:00', 0.03647},
	{17, '16/12/2006', '18:44:00', 0.04963},
	{17, '16/12/2006', '18:45:00', 0.07000},
	{17, '16/12/2006', '18:46:00', 0.07007},
	{17, '16/12/2006', '18:47:00', 0.07030},
	{17, '16/12/2006', '18:48:00', 0.04643},
	{18, '16/12/2006', '18:49:00', 0.04233},
	{18, '16/12/2006', '18:50:00', 0.04160},
	{18, '16/12/2006', '18:51:00', 0.03893},
	{18, '16/12/2006', '18:52:00', 0.03870},
	{18, '16/12/2006', '18:53:00', 0.04080},
	{19, '16/12/2006', '18:54:00', 0.07163},
	{19, '16/12/2006', '18:55:00', 0.07050},
	{19, '16/12/2006', '18:56:00', 0.07050},
	{19, '16/12/2006', '18:57:00', 0.06540},
	{19, '16/12/2006', '18:58:00', 0.07030},
	{20, '16/12/2006', '18:59:00', 0.07040},
	{20, '16/12/2006', '19:00:00', 0.06783},
	{20, '16/12/2006', '19:01:00', 0.06020},
	{20, '16/12/2006', '19:02:00', 0.05763},
	{20, '16/12/2006', '19:03:00', 0.05723}],ConsumptionDataLayout);
//
OUTPUT(ConsumptionData, NAMED('DataConsumption'));
//
//
AddressDataLayout := RECORD
  UNSIGNED8 Id;
  STRING20  Address;
END;
//
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
//
OUTPUT(AddressData, NAMED('DataAddress'));
//
//
OutputLayout := RECORD
  UNSIGNED8 Id;
  STRING20  Address;
  STRING10  Date;
  STRING8   Time;
  REAL8     Consumption;
END;
//
outputData := JOIN(ConsumptionData, AddressData, LEFT.id = RIGHT.Id, TRANSFORM(OutputLayout,
    SELF.Id          := LEFT.Id,
    SELF.Address     := RIGHT.Address,
    SELF.Date        := LEFT.Date,
    SELF.Time        := LEFT.Time,
    SELF.Consumption := LEFT.Consumption));
//
// OUTPUT(OutputData, NAMED('DataConsumptionAddressTime'));
OUTPUT(OutputData,, '~UFSC::XYZ::FOG::Consumption',CSV, OVERWRITE, NAMED('DataConsumptionAddressTime'));
//
//Import:ecl:UFSC.Fetch_Consumption
// EXPORT Fetch_Consumption := 'todo';
IMPORT $,Std;
//
EXPORT Fetch_Consumption (UNSIGNED8 Id_Value, STRING8 Time_Value, STRING10 Date_Value) := FUNCTION
//
	basekey := $.IDX_Consumption.IDX_Time_Id_Date;
//
	FilteredKey := IF(Id_Value = 0, basekey(Time = Time_Value),
                    IF(Date_Value = '',
                       basekey(Time = Time_Value OR Id = Id_Value AND NOT Date = Date_Value),
                       basekey(Time = Time_Value OR Id = Id_Value AND Date = Date_Value))
                   );
//
	RETURN OUTPUT(FilteredKey);
END;
//
//Import:ecl:UFSC.IDX_Consumption
// EXPORT IDX_Consumption := 'todo';
IMPORT $;
//
STD_Consumption := $.STD_Consumption.File;
//
EXPORT IDX_Consumption := MODULE
	EXPORT Layout := RECORD
    RECORDOF(STD_Consumption) AND NOT [RecId];
  END;
//
  SHARED Filename         := '~UFSC::XYZ::FOG::OUT_Consumption';
  EXPORT File 	          := DATASET(Filename,Layout,FLAT);
	EXPORT IDX_Time_Id_Date := INDEX(File,{Time,Id,Date},{File},'~UFSC::XYZ::KEY::IDX_Time_Id_Date');
END;
//
//Import:ecl:UFSC.modConsumption
// EXPORT modConsumption := 'todo';
IMPORT $;
//
EXPORT modConsumption := MODULE
  EXPORT Layout := RECORD
    UNSIGNED8 Id;
    STRING20  Address;
    STRING10  Date;
    STRING8   Time;
    REAL8     Consumption;
  END;
//
  EXPORT File := DATASET('~UFSC::XYZ::FOG::Consumption',Layout,CSV);
END;
//
//Import:ecl:UFSC.modEvents
// EXPORT modEvents := 'todo';
IMPORT $,Std;
//
EXPORT modEvents(UNSIGNED1 n) := MODULE
  EXPORT Days    := CRON('0 ' + n + ' * * *');
  EXPORT Hours   := CRON('0 0-23/' + n + ' * * *');
  EXPORT Minutes := CRON('0-59/' + n + ' * * * *');
  // EXPORT EveryOneMinute       := CRON('0-59/1 * * * *');
END;
//
//Import:ecl:UFSC.modTimes
// EXPORT modTimes := 'todo';
IMPORT $,Std;
//
EXPORT modTimes := MODULE
  EXPORT CntRec     := COUNT($.STD_Consumption.File);
//
  EXPORT SysTime    := INTFORMAT((STD.Date.CurrentTime()/100) -300,4,1);
  EXPORT NumSysTime := (INTEGER) SysTime;
//
  EXPORT RecTime    := $.STD_Consumption.File[1].Time;
  EXPORT NumRecTime := (INTEGER) RecTime;   // 1724
//
  EXPORT PushTime    := NumSysTime;
END;
//
//Import:ecl:UFSC.SoapCall01
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
//Import:ecl:UFSC.SoapCall02
// EXPORT SoapCall02 := 'todo';
IMPORT $;
//
OutRec1 := RECORDOF($.STD_Consumption.File) AND NOT [RecId];   // short mode
RoxieIP := 'http://127.0.0.1:8002/WsEcl/soap/query/roxie/fetch_consumption.1';
svc     := 'fetch_consumption.1';
//
// recordset in, recordset out
InputRec := RECORD
  STRING8   Time_Value {XPATH('Time_Value')};
  UNSIGNED8 Id_Value   {XPATH('Id_Value')};
  STRING10  Date_Value {XPATH('Date_Value')};
END;
//
InputDataset := DATASET([{'172400',1,'20061216'},
                         {'172900',2,'20061216'},
                         {'173400',3,'20061216'}],Inputrec);
//
ManyRec2 := SOAPCALL(InputDataset,RoxieIP,svc,Inputrec,TRANSFORM(LEFT),DATASET(OutRec1),ONFAIL(SKIP));
OUTPUT(ManyRec2);
//
//Import:ecl:UFSC.STD_Consumption
// EXPORT STD_Consumption := 'todo';
IMPORT $,Std;
//
EXPORT STD_Consumption := MODULE
	EXPORT Layout := RECORD
    $.UID_Consumption.RecId;
    $.UID_Consumption.Id;
    $.UID_Consumption.Address;
    STRING10 Date     := (STRING10) STD.Date.FromStringToDate($.UID_Consumption.Date,'%d/%m/%Y');
    STRING8  Time     := STD.Str.FindReplace($.UID_Consumption.Time[1..5],':','');
    $.UID_Consumption.consumption;
  END;
//
	EXPORT File := TABLE($.UID_Consumption,Layout)
                    :PERSIST('~UFSC::XYZ::FOG::STD_Consumption');
END;
//
//Import:ecl:UFSC.UID_Consumption
// EXPORT UID_Consumption := 'todo';
IMPORT $,Std;
//
Consumption := $.modConsumption.File;
//
Layout_Consumption_RecID := RECORD
  UNSIGNED4 RecId;
  $.modConsumption.Layout;
END;
//
Layout_Consumption_RecID IDrecs($.modConsumption.Layout L, INTEGER cnt) := TRANSFORM
  SELF.RecID    := cnt;
  SELF          := L;
END;
//
EXPORT UID_Consumption := PROJECT(Consumption,IDrecs(LEFT,COUNTER))
                              : PERSIST('~UFSC::XYZ::FOG::UID_Consumption');
//
