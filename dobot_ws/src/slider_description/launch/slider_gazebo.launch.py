from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

PKG_NAME = 'slider_description'
GAZEBO_PKG = 'ros_gz_sim'


def generate_launch_description() -> LaunchDescription:
    pkg_share = FindPackageShare(PKG_NAME)
    gazebo_pkg = FindPackageShare(GAZEBO_PKG)

    gazebo_launch = PathJoinSubstitution(
        [gazebo_pkg, 'launch', 'gz_sim.launch.py'])

    xacro_file = PathJoinSubstitution([
        pkg_share, 'urdf', 'slider.urdf.xacro'])

    controller_yaml = PathJoinSubstitution([
        pkg_share, 'config', 'carrier_controllers.yaml'])

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    entity_name = LaunchConfiguration('entity_name')

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ', xacro_file,
            ' controller_yaml:=', controller_yaml,
            ' name_space:=', namespace
        ]), value_type=str
    )

    ld = LaunchDescription()

    ld.add_action(DeclareLaunchArgument(
        'namespace', default_value='slider'))

    ld.add_action(DeclareLaunchArgument(
        'use_sim_time', default_value='true'))

    ld.add_action(DeclareLaunchArgument(
        'entity_name', default_value='sliding_plate'))

    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=namespace,
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time
        }]
    )
    ld.add_action(rsp_node)

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        namespace=namespace,
        arguments=[
            '-topic', ['/', namespace, '/robot_description'],
            '-name', entity_name,
            '-allow_renaming', 'true'
        ],
        output='screen'
    )
    ld.add_action(spawn)

    jsb_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '-c', ['/', namespace, '/controller_manager']
        ],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    ld.add_action(RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn,
            on_exit=[jsb_spawner])))

    controllers_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'p1_carrier_controller', 'right_lift_controller', 'left_lift_controller',
            '-c', ['/', namespace, '/controller_manager'],
            '--param-file', controller_yaml
        ],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    ld.add_action(RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=jsb_spawner,
            on_exit=[controllers_spawner])))

    ld.add_action(AppendEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=PathJoinSubstitution([pkg_share, '..'])
    ))

    ld.add_action(IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch),
        launch_arguments=[('gz_args', '-r -v 3 empty.sdf')]
    ))

    return ld
