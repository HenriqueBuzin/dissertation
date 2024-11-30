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