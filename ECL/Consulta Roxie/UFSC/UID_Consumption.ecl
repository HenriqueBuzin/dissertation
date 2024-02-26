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