import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/idrisg/iot-project/IoT_Projct/esibot_ws/install/esibot_bringup'
