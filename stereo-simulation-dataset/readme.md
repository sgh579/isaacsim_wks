Create a stereo camera in Isaac Sim and capture some images with specific parameter recorded.

## command to run

diy stereo camera

~/isaacsim/_build/linux-x86_64/release/python.sh /home/goodmansun/isaacsim_wks/stereo-simulation-dataset/run.py

stereo camera wrapper

~/isaacsim/_build/linux-x86_64/release/python.sh /home/goodmansun/isaacsim_wks/stereo-simulation-dataset/run_with_wrapper.py

~~stereo camera example~~

~/isaacsim/_build/linux-x86_64/release/python.sh /home/goodmansun/isaacsim/_build/linux-x86_64/release/standalone_examples/api/isaacsim.sensors.camera/camera_stereoscopic_depth.py

所有可用的数据 Key: dict_keys(['rendering_time', 'rendering_frame', 'DepthSensorDistance', 'distance_to_image_plane'])
Key: rendering_time                 | Shape/Type: N/A
Key: rendering_frame                | Shape/Type: N/A
Key: DepthSensorDistance            | Shape/Type: (1080, 1920)
Key: distance_to_image_plane        | Shape/Type: (1080, 1920)

this is not the wrapped stereo camera. It is dedicated for depth.