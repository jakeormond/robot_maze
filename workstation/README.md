# run_task.py

This is the main script for running the behavioural task. The code can be run from the workstation folder at the command line using:

```
python run_task.py
```

We have also run it from within VSCode, using both "Run Python File" and "Debug Python File" options. 

Before running the task, a number of steps must first be completed:

- Using configuration.py stored in the honeycomb_task folder, create a configuration file containing the robots ip addresses and port numbers.  

- Using platform_map.py, also in the honeycomb_task folder, create the map files. Initially, the user will need to create the full map of the environment (platform_map) and the restricted_map, in which positions at the maze edges have been removed (these edge positions are not suitable as final robot positions because the robots can not reach them with e.g. driving into walls, off the maze, etc)

- Calculate all platform positions within the overhead camera's field of view using the code stored in the platform_coordinates directory (a README.md stored there details the process).  

The script will prompt the user to enter an animal identifier, as well as the initial platform positions. Robot1 should be the start platform, on which the animal will be placed. Robot2 and Robot3 should be placed one platform away. 

Once the initial positions have been set, the script can calculate the region of the field of view around which to crop. It will then save the crop parameters into the top-level directory, and then prompt the user to start the video acquisition. Once video acquisition has started, the user can start the task by pressing any key. 

When the animal reaches the goal position, the user will be prompted to stop the video acquisition. Once this has been done, press any button, and all tracking files as well as the behaviour file (listing the animal's choices with timestamps) will be moved into short-term and long-term storage locations. 

Note that a number of directory locations are hard-coded, and will need to be changed if your set-up differs from ours. These directories are:

- top_dir, temporary storage of tracking files
- data_dir, short-term storage of tracking and behaviour files on the local machine
- yaml_dir, the location of the previously generated configuration file
- map_dir, the location of the map files
- server_dir, the location for long-term storage