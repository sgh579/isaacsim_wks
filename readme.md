this is where to store python scripts developed for my project


~/isaacsim/_build/linux-x86_64/release/python.sh <python standalone script>

## standard start

~/isaacsim/_build/linux-x86_64/release/isaac-sim.sh

## stereo camera


~/isaacsim/_build/linux-x86_64/release/python.sh ~/isaacsim_wks/stereo_recording/run.py

### standalone python example

stereoscopic depth

~/isaacsim/_build/linux-x86_64/release/python.sh ~/isaacsim/_build/linux-x86_64/release/standalone_examples/api/isaacsim.sensors.camera/camera_stereoscopic_depth.py

## Spring-based Force sensor: 

### Verification of stiffness

change the mass and record data mannually from the terminal output

~/isaacsim/_build/linux-x86_64/release/python.sh ~/isaacsim_wks/SpringForceSensor/test_stiffness.py

plot it with
```
conda activate plot_env
cd ~/isaacsim_wks/SpringForceSensor
python plot_sensor_verification.py 
```

### start the press and data recording

~/isaacsim/_build/linux-x86_64/release/python.sh ~/isaacsim_wks/SpringForceSensor/run.py

### Plot the curve

conda activate plot_env
python ~/isaacsim_wks/SpringForceSensor/plot_force.py /home/goodmansun/Documents/ExperimentalDataRaw/press/<csv filename>


## use ffmpeg to make video from keyframes
ffmpeg -y -framerate 30 -i ./stereo_parallel_recording/%04d_L.png -c:v libx264 -pix_fmt yuv420p left_eye.mp4
ffmpeg -y -framerate 30 -i ./stereo_parallel_recording/%04d_R.png -c:v libx264 -pix_fmt yuv420p right_eye.mp4