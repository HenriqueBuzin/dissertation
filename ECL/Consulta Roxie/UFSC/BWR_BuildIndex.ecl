// EXPORT BWR_BuildIndex := 'todo';
IMPORT $;
//
OUTPUT($.STD_Consumption.File,,'~UFSC::XYZ::FOG::OUT_Consumption', OVERWRITE);
//
BUILD($.IDX_Consumption.IDX_Time_Id_Date,OVERWRITE);
COUNT($.IDX_Consumption.IDX_Time_Id_Date);     //  95
//