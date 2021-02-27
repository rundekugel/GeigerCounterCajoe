# GeigerCounterCajoe

The GeigerCounter from Cajoe GMV2 runs with approximately 20000 Baud
The file geigertool.py interprets the data, which is sent via USB.

options:
-hex   view hexdump
-d=<format codes>  show values as u32,u16,s32,s16,float,double
-b=<baudrate>
-p=<portname>
-bs=<blocksize>
-xo=<0|1>          xon/xoff
-ts=<0|1|r>          timestamp on/off/relative
  
for Linux: use -p=/dev/ttyUSBx, where x is the number of the virtual serial port from the GMV-2
for Windows: use -p=COMx where x is the port, where the vortual GMV-2 serial port is installed.

todo:
 - measure the baudrate.
 - make it useable as lib
 - store measurements in a buffer
