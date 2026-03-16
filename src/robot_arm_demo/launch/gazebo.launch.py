# gazebo.launch.py
# 
# 启动Gazebo仿真环境及相关的控制器和状态发布节点。

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler, TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    gui = LaunchConfiguration('gui')

    pkg_share = get_package_share_directory('robot_arm_demo')
    
    # 处理URDF文件
    xacro_file = os.path.join(pkg_share, 'urdf', '6_axis_arm.urdf.xacro')
    doc = xacro.process_file(xacro_file)
    robot_description = {'robot_description': doc.toxml()}
    
    # 机器人状态发布节点 (必须使用仿真时间以匹配Gazebo时钟)
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': True}]
    )

    # 启动Gazebo物理服务端 (无头模式)
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    gazebo_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r -s -v4 empty.sdf'}.items(),
    )

    # 单独启动Gazebo GUI客户端
    gazebo_gui = ExecuteProcess(
        cmd=['gz', 'sim', '-g', '-v4'],
        output='screen'
    )

    # 通过 ros_gz_sim create 直接加载 URDF 字符串，避免等待 /robot_description 话题
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-world', 'empty', '-string', doc.toxml(), '-name', '6_axis_arm', '-z', '0.01'],
        output='screen'
    )

    # robot_state_publisher 仍然需要提供 TF 和关节状态，但不再承担生成实体的职责。
    delayed_robot_state_publisher = TimerAction(
        period=1.0,
        actions=[node_robot_state_publisher]
    )

    # 桥接Gazebo时钟到ROS
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # 加载并启动关节状态广播器
    load_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    # 加载并启动机械臂控制器
    load_arm_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller'],
        output='screen'
    )

    # 等待 spawn_entity 完成后再加载控制器
    delay_broadcaster_after_spawn = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[load_joint_state_broadcaster, load_arm_controller],
        )
    )

    # 延迟5秒启动GUI，确保物理引擎和控制器先就绪
    delayed_gui = TimerAction(
        period=5.0,
        actions=[gazebo_gui],
        condition=IfCondition(gui)
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'gui',
            default_value='true',
            description='Whether to start the Gazebo GUI client.'
        ),
        gazebo_server,
        spawn_entity,
        delayed_robot_state_publisher,
        clock_bridge,
        delay_broadcaster_after_spawn,
        delayed_gui,
    ])
