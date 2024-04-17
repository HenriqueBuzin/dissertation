IMPORT Std;

LZ_IP := '192.168.56.101';
LZ_Dir := '/var/lib/HPCCSystems/mydropzone/';
LZ_Path := '//' + LZ_IP + LZ_Dir;
RawFile := 'consumption.csv';
LogicalFileName := '~UFSC::XYZ::FOG::Consumption';

STD.File.SprayDelimited(LZ_IP,
												LZ_Path + RawFile,
												,,,,'mythor',
												LogicalFileName,-1,,,TRUE,TRUE);
