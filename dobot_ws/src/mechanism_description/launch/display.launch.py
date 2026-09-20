from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

PKG_NAME = 'mechanism_description'


def generate_launch_description() -> LaunchDescription:
    pkg_share = FindPackageShare(PKG_NAME)

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

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'),
            ' ',
            xacro_file
        ]),
        value_type=str
    )

    ld = LaunchDescription()

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description
            }
        ]
    )
    ld.add_action(rsp_node)

    jsp_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen',
    )
    ld.add_action(jsp_gui_node)

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        additional_env={
            '__NV_PRIME_RENDER_OFFLOAD': '1',
            '__GLX_VENDOR_LIBRARY_NAME': 'nvidia'
        }
    )
    ld.add_action(rviz)

    return ld
