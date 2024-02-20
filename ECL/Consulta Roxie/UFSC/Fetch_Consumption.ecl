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