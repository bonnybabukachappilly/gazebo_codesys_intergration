from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

PKG_NAME = 'mechanism_description'
GAZEBO_PKG = 'ros_gz_sim'


def generate_launch_description() -> LaunchDescription:
    pkg_share = FindPackageShare(PKG_NAME)
    gazebo_pkg = FindPackageShare(GAZEBO_PKG)

    xacro_file = PathJoinSubstitution([
        pkg_share,
        'urdf',
        'vertical_lift.urdf.xacro'
    ])

    rviz_config = PathJoinSubstitution([
        pkg_share,
        'rviz',
        'display.rviz'
    ])

    gazebo_launch = PathJoinSubstitution([
        gazebo_pkg,
        'launch',
        'gz_sim.launch.py'
    ])

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'),
            ' ',
            xacro_file
        ]),
        value_type=str
    )

    controller_yaml = PathJoinSubstitution([
        pkg_share,
        'config',
        'vertical_lift_controllers.yaml'
    ])

    ld = LaunchDescription()

    resource_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=[PathJoinSubstitution([pkg_share, '..'])]
    )
    ld.add_action(resource_path)

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': True
            }
        ]
    )
    ld.add_action(rsp_node)

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch),
        launch_arguments=[('gz_args', '-r -v 3 empty.sdf')]
    )
    ld.add_action(gazebo)

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'vertical_lift'],
        output='screen'
    )
    ld.add_action(spawn)

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )
    ld.add_action(bridge)

    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    broadcast_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn,
            on_exit=[joint_state_broadcaster]
        )
    )

    ld.add_action(broadcast_spawner)

    joint_trajectory_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_trajectory_controller',
            '--param-file', controller_yaml
        ],
        output='screen'
    )

    trajectory_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[joint_trajectory_controller]
        )
    )
    ld.add_action(trajectory_spawner)

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        additional_env={
            '__NV_PRIME_RENDER_OFFLOAD': '1',
            '__GLX_VENDOR_LIBRARY_NAME': 'nvidia'
        }
    )
    ld.add_action(rviz)

    return ld
