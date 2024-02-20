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