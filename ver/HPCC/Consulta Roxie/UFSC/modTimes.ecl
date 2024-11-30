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