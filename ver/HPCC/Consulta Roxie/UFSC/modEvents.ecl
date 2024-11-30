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