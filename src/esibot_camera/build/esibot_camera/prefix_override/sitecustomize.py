import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/user/esibot_ws/src/esibot_camera/install/esibot_camera'
