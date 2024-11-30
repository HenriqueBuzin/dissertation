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