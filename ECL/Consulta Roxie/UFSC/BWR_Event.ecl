// EXPORT BWR_Event := 'todo';
IMPORT $,Std;
//
// $.SoapCall01($.modTimes.PushTime) : WHEN($.ModEvents(1).Minutes,COUNT(95));   // 95 records 
$.SoapCall01($.modTimes.PushTime) : WHEN($.ModEvents(1).Minutes);
//