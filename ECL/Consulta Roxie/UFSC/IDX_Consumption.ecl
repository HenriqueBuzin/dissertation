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