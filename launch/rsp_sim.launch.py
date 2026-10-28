import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


from launch_ros.actions import Node
import xacro


# Ported from Gazebo Classic (gazebo_ros) to the new Gazebo (ros_gz_sim), following video #10.
def generate_launch_description():

    # Specify the name of the package and path to xacro file within the package
    pkg_name = 'urdf_example'
    pkg_share = get_package_share_directory(pkg_name)
    file_subpath = 'description/example_robot.urdf.xacro'


    # Use xacro to process the file
    xacro_file = os.path.join(pkg_share, file_subpath)
    robot_description_raw = xacro.process_file(xacro_file).toxml()


    # The world is now passed in explicitly (it used to be passed down by gazebo_ros)
    world = LaunchConfiguration('world')
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_share, 'worlds', 'empty.sdf'),
        description='World file to load')


    # Configure the node
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw,
        'use_sim_time': True}] # add other parameters here if required
    )


    # gazebo_ros/gazebo.launch.py  ->  ros_gz_sim/gz_sim.launch.py
    # -r runs the simulation straight away, -v4 prints extra debug info
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch'), '/gz_sim.launch.py']),
        launch_arguments={'gz_args': ['-r -v4 ', world],
                          'on_exit_shutdown': 'true'}.items()
        )


    # gazebo_ros spawn_entity.py  ->  ros_gz_sim create  (-entity became -name)
    spawn_entity = Node(package='ros_gz_sim', executable='create',
                    arguments=['-topic', 'robot_description',
                                '-name', 'my_bot'],
                    output='screen')


    # Copy Gazebo topics <-> ROS topics (clock, joint states, trajectory commands, camera)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': os.path.join(pkg_share, 'config', 'gz_bridge.yaml'),
                     'use_sim_time': True}],
        output='screen'
    )

    # Images get their own bridge so they can use image_transport
    image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['camera/image', 'camera/depth_image'],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )




    # Run the node
    return LaunchDescription([
        world_arg,
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        bridge,
        image_bridge
    ])
